import base64
import json
import os
from typing import Any

import requests

from app.storage.character_store import get_character, get_character_bible, save_character_assets
from app.storage.common import ensure_directory, read_json, write_bytes_atomic, write_json_atomic
from app.storage.episode_store import get_episode_dir, list_episodes
from app.storage.series_store import get_series_path


CHARACTER_SYSTEM_PROMPT = """
You are a film and animation character design director.
Return only valid JSON.
Build a stable character package that can be reused across many shots with minimal drift.
Be concrete about face proportions, hair, costume, and performance aura.
All prompt text should optimize for production reference-sheet generation and identity consistency.
"""


CHARACTER_USER_PROMPT = """
Generate a strict JSON object for this character.

Target schema:
{{
  "summary": "one-line role positioning",
  "anchors": {{
    "face": "face shape, proportion, signature facial traits",
    "hair": "hair style, color, length, texture",
    "costume": "default costume, materials, layers, accessories",
    "aura": "temperament, posture, emotional projection"
  }},
  "bible": {{
    "core_identity": "who this person is in production terms",
    "appearance": ["rule 1", "rule 2"],
    "wardrobe_rules": ["rule 1", "rule 2"],
    "expression_rules": ["rule 1", "rule 2"],
    "performance_notes": ["note 1", "note 2"],
    "continuity_rules": ["rule 1", "rule 2"]
  }},
  "visual_prompts": {{
    "front": "front full-body reference prompt",
    "side": "side full-body reference prompt",
    "back": "back full-body reference prompt",
    "features": "3x3 feature decomposition board prompt",
    "sheet": "final single-sheet character bible prompt"
  }},
  "negative_prompt": "what must be avoided"
}}

Character name: {name}
Character brief: {brief}

Story context:
{context}
"""

CHARACTER_GENERATION_MODE_REFERENCE_PLUS_TEXT = "reference_plus_text"
CHARACTER_GENERATION_MODE_REFERENCE_SUBJECT_ONLY = "reference_subject_only"


class ImageProviderError(Exception):
    """Raised when the external image provider cannot be reached or returns bad data."""


def _get_deepseek_settings() -> tuple[str, str, str]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("缺少 DEEPSEEK_API_KEY 配置")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://www.packyapi.com/v1").rstrip("/")
    model = os.getenv("DEEPSEEK_CHARACTER_MODEL", os.getenv("DEEPSEEK_SCRIPT_MODEL", "deepseek-v4-pro")).strip()
    return api_key, base_url, model


def _get_gpt_image_settings() -> tuple[str, str, str]:
    api_key = os.getenv("GPT_IMAGE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("缺少 GPT_IMAGE_API_KEY 配置")
    base_url = os.getenv("GPT_IMAGE_BASE_URL", "https://www.packyapi.com/v1").rstrip("/")
    model = os.getenv("GPT_IMAGE_MODEL", "gpt-image-2").strip()
    return api_key, base_url, model


def _get_gpt_image_response_format() -> str:
    response_format = os.getenv("GPT_IMAGE_RESPONSE_FORMAT", "url").strip().lower()
    if response_format not in {"url", "b64_json"}:
        return "url"
    return response_format


def _get_character_sheet_size() -> str:
    size = os.getenv("GPT_IMAGE_CHARACTER_SHEET_SIZE", "1024x1536").strip().lower()
    return size or "1024x1536"


def _get_character_sheet_quality() -> str:
    quality = os.getenv("GPT_IMAGE_CHARACTER_QUALITY", os.getenv("GPT_IMAGE_QUALITY", "medium")).strip().lower()
    if quality not in {"low", "medium", "high", "auto"}:
        return "medium"
    return quality


def _get_gpt_image_output_format() -> str:
    output_format = os.getenv("GPT_IMAGE_OUTPUT_FORMAT", "jpeg").strip().lower()
    if output_format not in {"png", "jpeg", "jpg"}:
        return "jpeg"
    return "jpeg" if output_format == "jpg" else output_format


def _get_gpt_image_output_extension() -> str:
    return ".png" if _get_gpt_image_output_format() == "png" else ".jpg"


def _get_gpt_image_output_compression() -> int | None:
    if _get_gpt_image_output_format() != "jpeg":
        return None

    raw_value = os.getenv("GPT_IMAGE_OUTPUT_COMPRESSION", "82").strip()
    try:
        value = int(raw_value)
    except ValueError:
        return 82
    return min(100, max(0, value))


def _build_gpt_image_payload(prompt: str, size: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": _get_gpt_image_settings()[2],
        "prompt": prompt,
        "size": size,
        "quality": _get_character_sheet_quality(),
        "output_format": _get_gpt_image_output_format(),
        "response_format": _get_gpt_image_response_format(),
        "n": 1,
    }
    compression = _get_gpt_image_output_compression()
    if compression is not None:
        payload["output_compression"] = compression
    return payload


def _create_gpt_image_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = os.getenv("GPT_IMAGE_TRUST_ENV", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return session


def _raise_provider_http_error(response: requests.Response, action: str) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text.strip()
        if detail:
            detail = detail[:600]
            raise ImageProviderError(
                f"PackyAPI {action} 请求失败，HTTP {response.status_code}：{detail}"
            ) from exc
        raise ImageProviderError(
            f"PackyAPI {action} 请求失败，HTTP {response.status_code}"
        ) from exc


def _parse_provider_payload(response: requests.Response, action: str) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError as exc:
        raise ImageProviderError(f"PackyAPI {action} 返回了无效 JSON") from exc


def _strip_code_fences(content: str) -> str:
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def _extract_json_payload(content: str) -> dict[str, Any]:
    cleaned = _strip_code_fences(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _collect_episode_context(series_slug: str, character_name: str, episode_ids: list[str]) -> str:
    snippets: list[str] = []
    episode_id_set = {item for item in episode_ids if item}

    for episode in list_episodes(series_slug):
        episode_id = episode.get("id", "")
        if episode_id_set and episode_id not in episode_id_set:
            continue

        parsed_path = get_episode_dir(series_slug, episode_id) / "script.parsed.json"
        parsed = read_json(parsed_path, default={})
        scenes = parsed.get("scenes") or []
        matched_lines: list[str] = []

        for scene in scenes:
            location = scene.get("location", "")
            summary = scene.get("summary", "")
            for shot in scene.get("shots") or []:
                characters = shot.get("characters") or []
                if character_name in characters:
                    description = shot.get("description", "")
                    emotion = shot.get("emotion", "")
                    matched_lines.append(
                        f"Scene: {location}; Summary: {summary}; Shot: {description}; Emotion: {emotion}"
                    )
                for dialogue in shot.get("dialogues") or []:
                    if dialogue.get("character") == character_name:
                        matched_lines.append(f"Dialogue: {dialogue.get('text', '')}")

        if matched_lines:
            snippets.append(f"{episode.get('name', episode_id)}:\n" + "\n".join(matched_lines[:10]))

    if snippets:
        return "\n\n".join(snippets[:3])
    return "No strong script context was found. Use the brief and name to build a stable production-ready design."


def _normalize_character_package(payload: dict[str, Any], character_name: str, brief: str) -> dict[str, Any]:
    anchors = payload.get("anchors") or {}
    bible = payload.get("bible") or {}
    visual_prompts = payload.get("visual_prompts") or {}

    def _lines(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    summary = str(payload.get("summary", "")).strip() or f"{character_name} design package"
    negative_prompt = str(payload.get("negative_prompt", "")).strip()

    normalized = {
        "summary": summary,
        "anchors": {
            "face": str(anchors.get("face", "")).strip(),
            "hair": str(anchors.get("hair", "")).strip(),
            "costume": str(anchors.get("costume", "")).strip(),
            "aura": str(anchors.get("aura", "")).strip(),
        },
        "bible": {
            "core_identity": str(bible.get("core_identity", "")).strip(),
            "appearance": _lines(bible.get("appearance")),
            "wardrobe_rules": _lines(bible.get("wardrobe_rules")),
            "expression_rules": _lines(bible.get("expression_rules")),
            "performance_notes": _lines(bible.get("performance_notes")),
            "continuity_rules": _lines(bible.get("continuity_rules")),
        },
        "visual_prompts": {
            "front": str(visual_prompts.get("front", "")).strip(),
            "side": str(visual_prompts.get("side", "")).strip(),
            "back": str(visual_prompts.get("back", "")).strip(),
            "features": str(visual_prompts.get("features", "")).strip(),
            "sheet": str(visual_prompts.get("sheet", "")).strip(),
        },
        "negative_prompt": negative_prompt,
        "brief": brief,
    }

    fallback_labels = {
        "front": "front full body production reference",
        "side": "side full body production reference",
        "back": "back full body production reference",
        "features": "3x3 character feature decomposition board",
        "sheet": "single final character bible sheet",
    }
    for view_name, label in fallback_labels.items():
        if not normalized["visual_prompts"][view_name]:
            normalized["visual_prompts"][view_name] = (
                f"{character_name}, {summary}, "
                f"{normalized['anchors']['face']}, {normalized['anchors']['hair']}, "
                f"{normalized['anchors']['costume']}, {normalized['anchors']['aura']}, "
                f"{label}, clean background, production design"
            )

    return normalized


def _build_full_sheet_prompt(character_name: str, package: dict[str, Any]) -> str:
    continuity_lines = package["bible"]["continuity_rules"]
    continuity_text = "; ".join(continuity_lines[:4])
    return (
        f"{package['visual_prompts']['sheet']}. "
        f"Character name: {character_name}. "
        "Create one complete character bible sheet in a single image. "
        "Top area must contain three consistent full-body turnaround views: front view, side view, back view. "
        "Bottom area must contain a 3x3 feature decomposition board with labeled-style panel separation showing: "
        "face close-up, hair detail, upper costume, lower costume, accessory detail, shoes detail, "
        "tattoo or body mark if any otherwise signature prop detail, hand or gesture detail, and signature pose. "
        f"Keep strict identity consistency: {package['anchors']['face']}; {package['anchors']['hair']}; "
        f"{package['anchors']['costume']}; {package['anchors']['aura']}. "
        f"Continuity requirements: {continuity_text or 'same person, same costume, same performance aura'}. "
        "Visible panel borders, clean background, production reference-sheet aesthetic, highly readable layout, "
        "all subpanels belong to the same exact character."
    )


def _build_reference_subject_only_sheet_prompt() -> str:
    return (
        "Use the uploaded reference image as the only identity source. "
        "Do not reinterpret the character from text description, script, name, biography, or extra invention. "
        "Preserve the exact same subject identity, face, body proportions, costume, accessories, colors, markings, and silhouette from the reference image. "
        "Create one complete character bible sheet in a single image. "
        "Top area must contain three consistent full-body turnaround views: front view, side view, back view. "
        "Bottom area must contain a 3x3 feature decomposition board with visible panel borders. "
        "The nine panels should focus on: face close-up, hairstyle or head detail, upper clothing detail, lower clothing detail, accessory detail, shoes detail, tattoo or body mark if any otherwise signature prop detail, hand or gesture detail, and signature pose. "
        "Clean neutral background, production reference-sheet layout, highly readable arrangement, same exact subject across all panels."
    )


def _build_reference_subject_only_package(character: dict[str, Any], current_bible: dict[str, Any]) -> dict[str, Any]:
    anchors = current_bible.get("anchors") or character.get("anchors") or {}
    bible = current_bible.get("bible") or {}
    return {
        "summary": str(current_bible.get("summary", "")).strip(),
        "anchors": {
            "face": str(anchors.get("face", "")).strip(),
            "hair": str(anchors.get("hair", "")).strip(),
            "costume": str(anchors.get("costume", "")).strip(),
            "aura": str(anchors.get("aura", "")).strip(),
        },
        "bible": {
            "core_identity": str(bible.get("core_identity", "")).strip() or "Use uploaded reference image as the identity source.",
            "appearance": [str(item).strip() for item in (bible.get("appearance") or []) if str(item).strip()],
            "wardrobe_rules": [str(item).strip() for item in (bible.get("wardrobe_rules") or []) if str(item).strip()],
            "expression_rules": [str(item).strip() for item in (bible.get("expression_rules") or []) if str(item).strip()],
            "performance_notes": [str(item).strip() for item in (bible.get("performance_notes") or []) if str(item).strip()],
            "continuity_rules": [str(item).strip() for item in (bible.get("continuity_rules") or []) if str(item).strip()],
        },
        "visual_prompts": {
            "front": "",
            "side": "",
            "back": "",
            "features": "",
            "sheet": "Reference-only single-sheet character bible with three-view turnaround and 3x3 feature board.",
        },
        "negative_prompt": "Do not redesign from text, do not change identity, do not add invented props, do not change costume or species.",
        "brief": character.get("brief", ""),
    }


def _resolve_generation_mode(requested_mode: str | None, has_source_image: bool) -> str:
    mode = (requested_mode or CHARACTER_GENERATION_MODE_REFERENCE_PLUS_TEXT).strip().lower()
    allowed = {
        CHARACTER_GENERATION_MODE_REFERENCE_PLUS_TEXT,
        CHARACTER_GENERATION_MODE_REFERENCE_SUBJECT_ONLY,
    }
    if mode not in allowed:
        raise ValueError(f"不支持的角色生成模式：{requested_mode}")
    if mode == CHARACTER_GENERATION_MODE_REFERENCE_SUBJECT_ONLY and not has_source_image:
        raise ValueError("仅按参考图生成模式至少需要上传一张参考图")
    return mode


def _generate_character_package(name: str, brief: str, context: str) -> dict[str, Any]:
    api_key, base_url, model = _get_deepseek_settings()
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0.3,
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": CHARACTER_SYSTEM_PROMPT.strip()},
                {
                    "role": "user",
                    "content": CHARACTER_USER_PROMPT.format(
                        name=name,
                        brief=brief or "No brief provided.",
                        context=context,
                    ).strip(),
                },
            ],
        },
        timeout=180,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"DeepSeek 角色生成失败：{response.text}") from exc

    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content.strip():
        raise ValueError("DeepSeek 返回的角色设定为空")

    try:
        payload = _extract_json_payload(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"角色 JSON 解析失败：{content}") from exc

    return _normalize_character_package(payload, name, brief)


def _decode_image_payload(item: dict[str, Any], session: requests.Session) -> bytes:
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])

    if item.get("url"):
        try:
            response = session.get(item["url"], timeout=180)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ImageProviderError(f"PackyAPI 图片下载失败：{exc}") from exc
        return response.content

    raise ImageProviderError("PackyAPI returned neither b64_json nor url")


def _generate_reference_image(prompt: str, size: str) -> bytes:
    api_key, base_url, model = _get_gpt_image_settings()
    payload = _build_gpt_image_payload(prompt, size)
    payload["model"] = model
    with _create_gpt_image_session() as session:
        try:
            response = session.post(
                f"{base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=300,
            )
        except requests.RequestException as exc:
            raise ImageProviderError(f"PackyAPI 文生图连接失败：{exc}") from exc
        _raise_provider_http_error(response, "image generation")
        payload = _parse_provider_payload(response, "image generation")
        data = payload.get("data") or []
        if not data:
            raise ImageProviderError("PackyAPI image generation returned no image data")
        return _decode_image_payload(data[0], session)


def _generate_reference_image_from_source(prompt: str, size: str, source_bytes: bytes) -> bytes:
    api_key, base_url, model = _get_gpt_image_settings()
    payload = _build_gpt_image_payload(prompt, size)
    payload["model"] = model
    payload["input_fidelity"] = os.getenv("GPT_IMAGE_INPUT_FIDELITY", "high")
    payload.pop("n", None)
    with _create_gpt_image_session() as session:
        try:
            response = session.post(
                f"{base_url}/images/edits",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                },
                data=payload,
                files={
                    "image": ("reference.png", source_bytes, "image/png"),
                },
                timeout=300,
            )
        except requests.RequestException as exc:
            raise ImageProviderError(f"PackyAPI 图生图连接失败：{exc}") from exc
        _raise_provider_http_error(response, "image edit")
        payload = _parse_provider_payload(response, "image edit")
        data = payload.get("data") or []
        if not data:
            raise ImageProviderError("PackyAPI image edit returned no image data")
        return _decode_image_payload(data[0], session)


def _load_primary_source_image(series_slug: str, character: dict[str, Any]) -> bytes | None:
    source_images = character.get("source_images") or []
    if not source_images:
        return None

    latest = source_images[-1]
    relative_path = str(latest.get("path", "")).strip()
    if not relative_path:
        return None

    absolute_path = get_series_path(series_slug) / relative_path
    if not absolute_path.exists():
        return None
    return absolute_path.read_bytes()


def _remove_stale_sheet_files(refs_dir, active_extension: str) -> None:
    for extension in (".png", ".jpg"):
        if extension == active_extension:
            continue
        stale_path = refs_dir / f"character_bible_sheet{extension}"
        if stale_path.exists():
            stale_path.unlink()


def generate_character_assets(
    series_slug: str,
    character_id: str,
    *,
    episode_ids: list[str] | None = None,
    generation_mode: str | None = None,
) -> dict[str, Any]:
    character = get_character(series_slug, character_id)
    if character is None:
        raise FileNotFoundError(character_id)

    episode_ids = episode_ids or []
    source_image_bytes = _load_primary_source_image(series_slug, character)
    current_bible = get_character_bible(series_slug, character_id)
    resolved_mode = _resolve_generation_mode(generation_mode, source_image_bytes is not None)
    context = _collect_episode_context(series_slug, character.get("name", ""), episode_ids)
    if resolved_mode == CHARACTER_GENERATION_MODE_REFERENCE_SUBJECT_ONLY:
        package = _build_reference_subject_only_package(character, current_bible)
        final_prompt = _build_reference_subject_only_sheet_prompt()
    else:
        package = _generate_character_package(
            name=character.get("name", ""),
            brief=character.get("brief", ""),
            context=context,
        )
        final_prompt = _build_full_sheet_prompt(character.get("name", ""), package)

    version = int(character.get("latest_version", current_bible.get("version", 1))) + 1

    series_root = get_series_path(series_slug)
    character_dir = series_root / "characters" / character_id
    refs_dir = character_dir / "refs"
    version_dir = character_dir / "generated" / f"v{version:03d}"
    ensure_directory(refs_dir)
    ensure_directory(version_dir)

    final_size = _get_character_sheet_size()
    output_format = _get_gpt_image_output_format()
    output_extension = _get_gpt_image_output_extension()
    final_sheet_bytes = (
        _generate_reference_image_from_source(final_prompt, final_size, source_image_bytes)
        if source_image_bytes is not None
        else _generate_reference_image(final_prompt, final_size)
    )
    ref_path = refs_dir / f"character_bible_sheet{output_extension}"
    versioned_sheet_path = version_dir / f"character_bible_sheet{output_extension}"
    write_bytes_atomic(ref_path, final_sheet_bytes)
    write_bytes_atomic(versioned_sheet_path, final_sheet_bytes)
    _remove_stale_sheet_files(refs_dir, output_extension)

    prompt_manifest = {
        "character_id": character_id,
        "version": version,
        "summary": package["summary"],
        "anchors": package["anchors"],
        "visual_prompts": package["visual_prompts"],
        "negative_prompt": package["negative_prompt"],
        "image_size": final_size,
        "output_format": output_format,
        "output_extension": output_extension,
        "quality": _get_character_sheet_quality(),
        "output_compression": _get_gpt_image_output_compression(),
        "episode_ids": episode_ids,
        "source_image_mode": "image_edit" if source_image_bytes is not None else "text_only",
        "generation_mode": resolved_mode,
        "layout_mode": "single_sheet",
    }
    write_json_atomic(version_dir / "prompt_package.json", prompt_manifest)

    bible_payload = {
        "character_id": character_id,
        "version": version,
        "brief": character.get("brief", ""),
        "summary": package["summary"],
        "anchors": package["anchors"],
        "bible": package["bible"],
        "visual_prompts": package["visual_prompts"],
        "negative_prompt": package["negative_prompt"],
        "notes": [],
        "generated_from": {
            "episode_ids": episode_ids,
            "context_summary": context,
            "source_images": character.get("source_images", []),
        },
        "generation": {
            "image_provider": "packyapi",
            "image_model": os.getenv("GPT_IMAGE_MODEL", "gpt-image-2").strip(),
            "image_size": final_size,
            "output_format": output_format,
            "quality": _get_character_sheet_quality(),
            "output_compression": _get_gpt_image_output_compression(),
            "deepseek_model": (
                os.getenv(
                    "DEEPSEEK_CHARACTER_MODEL",
                    os.getenv("DEEPSEEK_SCRIPT_MODEL", "deepseek-v4-pro"),
                ).strip()
                if resolved_mode == CHARACTER_GENERATION_MODE_REFERENCE_PLUS_TEXT
                else ""
            ),
            "version_dir": str(version_dir.relative_to(series_root)).replace("\\", "/"),
            "mode": "image_edit" if source_image_bytes is not None else "text_generation",
            "generation_mode": resolved_mode,
            "layout_mode": "single_sheet",
        },
        "reference_images": {
            "sheet": str(ref_path.relative_to(series_root)).replace("\\", "/"),
        },
        "component_images": {},
        "source_images": character.get("source_images", []),
    }

    manifest = save_character_assets(
        series_slug,
        character_id,
        version=version,
        anchors=package["anchors"],
        bible_data=bible_payload,
        reference_images={"sheet": str(ref_path)},
        component_images={},
    )

    return {
        "item": manifest,
        "bible": bible_payload,
        "reference_images": manifest["reference_images"],
    }
