import base64
import json
import os
from typing import Any

import requests

from app.storage.common import ensure_directory, read_json, write_bytes_atomic, write_json_atomic
from app.storage.episode_store import get_episode_dir, list_episodes
from app.storage.scene_store import get_scene, get_scene_prompt_package, save_scene_assets
from app.storage.series_store import get_series_path


SCENE_SYSTEM_PROMPT = """
You are a production designer and environment concept director.
Return only valid JSON.
Build a stable scene package for multi-view reference generation.
Focus on spatial continuity, lighting, palette, atmosphere, architectural cues, and prop stability.
"""


SCENE_USER_PROMPT = """
Generate a strict JSON object for this scene.

Target schema:
{{
  "summary": "one-line scene summary",
  "visual_profile": {{
    "time": "time of day or era cue",
    "weather": "weather or environmental condition",
    "lighting": "lighting setup",
    "palette": "color system",
    "style": "visual style",
    "architecture": "space design or structure",
    "atmosphere": "mood and environmental feeling",
    "key_props": ["prop 1", "prop 2"]
  }},
  "view_prompts": {{
    "establishing": "wide establishing environment prompt",
    "closeup": "closer environmental framing prompt",
    "bird_eye": "high angle or bird-eye environment prompt",
    "detail": "detail shot prompt for a representative area or prop cluster"
  }},
  "negative_prompt": "what must be avoided"
}}

Scene name: {name}
Scene description: {description}

Story context:
{context}
"""


def _get_deepseek_settings() -> tuple[str, str, str]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    model = os.getenv("DEEPSEEK_SCENE_MODEL", os.getenv("DEEPSEEK_SCRIPT_MODEL", "deepseek-chat")).strip()
    return api_key, base_url, model


def _get_scene_image_settings() -> tuple[str, str, str]:
    api_key = os.getenv("SCENE_IMAGE_API_KEY", os.getenv("GPT_IMAGE_API_KEY", "")).strip()
    if not api_key:
        raise ValueError("Missing SCENE_IMAGE_API_KEY or GPT_IMAGE_API_KEY")
    base_url = os.getenv("SCENE_IMAGE_BASE_URL", os.getenv("GPT_IMAGE_BASE_URL", "https://www.packyapi.com/v1")).rstrip("/")
    model = os.getenv("SCENE_IMAGE_MODEL", os.getenv("GPT_IMAGE_MODEL", "gpt-image-2")).strip()
    return api_key, base_url, model


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


def _collect_scene_context(series_slug: str, scene_name: str, episode_ids: list[str]) -> str:
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
            if scene_name.lower() in location.lower() or location.lower() in scene_name.lower():
                matched_lines.append(f"Scene location: {location}; Summary: {summary}")
                for shot in scene.get("shots") or []:
                    matched_lines.append(
                        f"Shot: {shot.get('description', '')}; Emotion: {shot.get('emotion', '')}; Beat: {shot.get('beat', '')}"
                    )

        if matched_lines:
            snippets.append(f"{episode.get('name', episode_id)}:\n" + "\n".join(matched_lines[:12]))

    if snippets:
        return "\n\n".join(snippets[:3])
    return "No strong script context was found. Use the scene name and description to build a stable environment package."


def _normalize_scene_package(payload: dict[str, Any], scene_name: str, description: str) -> dict[str, Any]:
    visual_profile = payload.get("visual_profile") or {}
    view_prompts = payload.get("view_prompts") or {}

    key_props = visual_profile.get("key_props") or []
    if isinstance(key_props, str):
        key_props = [key_props]

    normalized = {
        "summary": str(payload.get("summary", "")).strip() or f"{scene_name} environment package",
        "visual_profile": {
            "time": str(visual_profile.get("time", "")).strip(),
            "weather": str(visual_profile.get("weather", "")).strip(),
            "lighting": str(visual_profile.get("lighting", "")).strip(),
            "palette": str(visual_profile.get("palette", "")).strip(),
            "style": str(visual_profile.get("style", "")).strip(),
            "architecture": str(visual_profile.get("architecture", "")).strip(),
            "atmosphere": str(visual_profile.get("atmosphere", "")).strip(),
            "key_props": [str(item).strip() for item in key_props if str(item).strip()],
        },
        "view_prompts": {
            "establishing": str(view_prompts.get("establishing", "")).strip(),
            "closeup": str(view_prompts.get("closeup", "")).strip(),
            "bird_eye": str(view_prompts.get("bird_eye", "")).strip(),
            "detail": str(view_prompts.get("detail", "")).strip(),
        },
        "negative_prompt": str(payload.get("negative_prompt", "")).strip(),
        "description": description,
    }

    fallback_labels = {
        "establishing": "wide establishing view",
        "closeup": "closer environmental view",
        "bird_eye": "bird-eye overview",
        "detail": "detail view",
    }
    for view_name, label in fallback_labels.items():
        if not normalized["view_prompts"][view_name]:
            normalized["view_prompts"][view_name] = (
                f"{scene_name}, {normalized['summary']}, {normalized['visual_profile']['architecture']}, "
                f"{normalized['visual_profile']['lighting']}, {normalized['visual_profile']['palette']}, "
                f"{normalized['visual_profile']['style']}, {normalized['visual_profile']['atmosphere']}, "
                f"{label}, environment concept art, no characters, production design reference"
            )

    return normalized


def _build_image_prompt(scene_name: str, package: dict[str, Any], view_name: str) -> str:
    profile = package["visual_profile"]
    props = ", ".join(profile.get("key_props") or [])
    return (
        f"{package['view_prompts'][view_name]}. "
        f"Scene name: {scene_name}. "
        f"Keep environment continuity: time {profile['time']}; weather {profile['weather']}; "
        f"lighting {profile['lighting']}; palette {profile['palette']}; style {profile['style']}; "
        f"architecture {profile['architecture']}; atmosphere {profile['atmosphere']}; key props {props}. "
        "Environment only unless the prompt explicitly requires otherwise. Clean high-quality reference image."
    )


def _build_scene_sheet_prompt(scene_name: str, package: dict[str, Any]) -> str:
    profile = package["visual_profile"]
    props = ", ".join(profile.get("key_props") or [])
    return (
        f"Create one complete scene reference sheet for {scene_name}. "
        "Generate a single collage image with four clearly separated panels in one board. "
        "Panel 1: wide establishing view. "
        "Panel 2: closer atmosphere view. "
        "Panel 3: bird-eye or high-angle spatial overview. "
        "Panel 4: representative detail area or prop cluster close-up. "
        f"Keep strict environment continuity across all panels: time {profile['time']}; weather {profile['weather']}; "
        f"lighting {profile['lighting']}; palette {profile['palette']}; style {profile['style']}; "
        f"architecture {profile['architecture']}; atmosphere {profile['atmosphere']}; key props {props}. "
        f"Use these panel intentions: establishing {package['view_prompts']['establishing']}; "
        f"closeup {package['view_prompts']['closeup']}; bird-eye {package['view_prompts']['bird_eye']}; "
        f"detail {package['view_prompts']['detail']}. "
        "Environment only, no characters unless the scene design absolutely requires tiny background scale figures. "
        "Visible panel borders, clean production design board aesthetic, highly readable layout, same exact location in all panels."
    )


def _get_scene_sheet_size() -> str:
    size = os.getenv("SCENE_IMAGE_SHEET_SIZE", "1536x1024").strip().lower()
    return size or "1536x1024"


def _get_scene_image_quality() -> str:
    quality = os.getenv("SCENE_IMAGE_QUALITY", os.getenv("GPT_IMAGE_QUALITY", "medium")).strip().lower()
    if quality not in {"low", "medium", "high", "auto"}:
        return "medium"
    return quality


def _get_scene_image_output_format() -> str:
    output_format = os.getenv("SCENE_IMAGE_OUTPUT_FORMAT", os.getenv("GPT_IMAGE_OUTPUT_FORMAT", "jpeg")).strip().lower()
    if output_format not in {"png", "jpeg", "jpg"}:
        return "jpeg"
    return "jpeg" if output_format == "jpg" else output_format


def _get_scene_image_output_extension() -> str:
    return ".png" if _get_scene_image_output_format() == "png" else ".jpg"


def _get_scene_image_output_compression() -> int | None:
    if _get_scene_image_output_format() != "jpeg":
        return None

    raw_value = os.getenv("SCENE_IMAGE_OUTPUT_COMPRESSION", os.getenv("GPT_IMAGE_OUTPUT_COMPRESSION", "82")).strip()
    try:
        value = int(raw_value)
    except ValueError:
        return 82
    return min(100, max(0, value))


def _get_scene_image_response_format() -> str:
    response_format = os.getenv("SCENE_IMAGE_RESPONSE_FORMAT", os.getenv("GPT_IMAGE_RESPONSE_FORMAT", "url")).strip().lower()
    if response_format not in {"url", "b64_json"}:
        return "url"
    return response_format


def _build_scene_image_payload(prompt: str, size: str, model: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": _get_scene_image_quality(),
        "output_format": _get_scene_image_output_format(),
        "response_format": _get_scene_image_response_format(),
        "n": 1,
    }
    compression = _get_scene_image_output_compression()
    if compression is not None:
        payload["output_compression"] = compression
    return payload


def _create_scene_image_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = os.getenv("SCENE_IMAGE_TRUST_ENV", os.getenv("GPT_IMAGE_TRUST_ENV", "false")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return session


def _remove_stale_scene_sheet_files(refs_dir, active_extension: str) -> None:
    for extension in (".png", ".jpg"):
        if extension == active_extension:
            continue
        stale_path = refs_dir / f"scene_reference_sheet{extension}"
        if stale_path.exists():
            stale_path.unlink()

    for legacy_name in ("establishing", "closeup", "bird_eye", "detail"):
        for extension in (".png", ".jpg", ".jpeg"):
            legacy_path = refs_dir / f"{legacy_name}{extension}"
            if legacy_path.exists():
                legacy_path.unlink()


def _generate_scene_package(name: str, description: str, context: str) -> dict[str, Any]:
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
                {"role": "system", "content": SCENE_SYSTEM_PROMPT.strip()},
                {
                    "role": "user",
                    "content": SCENE_USER_PROMPT.format(
                        name=name,
                        description=description or "No scene description provided.",
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
        raise ValueError(f"DeepSeek scene generation failed: {response.text}") from exc

    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content.strip():
        raise ValueError("DeepSeek returned empty scene package")

    try:
        payload = _extract_json_payload(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse scene JSON: {content}") from exc

    return _normalize_scene_package(payload, name, description)


def _decode_image_payload(item: dict[str, Any], session: requests.Session) -> bytes:
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])

    if item.get("url"):
        response = session.get(item["url"], timeout=180)
        response.raise_for_status()
        return response.content

    raise ValueError("Image provider returned neither b64_json nor url")


def _generate_reference_image(prompt: str, size: str) -> bytes:
    api_key, base_url, model = _get_scene_image_settings()
    payload = _build_scene_image_payload(prompt, size, model)
    with _create_scene_image_session() as session:
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
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise ValueError(f"Scene image request failed: {response.text}") from exc

        response_payload = response.json()
        data = response_payload.get("data") or []
        if not data:
            raise ValueError("Scene image provider returned no image data")
        return _decode_image_payload(data[0], session)


def generate_scene_assets(
    series_slug: str,
    scene_id: str,
    *,
    episode_ids: list[str] | None = None,
) -> dict[str, Any]:
    scene = get_scene(series_slug, scene_id)
    if scene is None:
        raise FileNotFoundError(scene_id)

    episode_ids = episode_ids or ([scene.get("episode_id")] if scene.get("episode_id") else [])
    context = _collect_scene_context(series_slug, scene.get("name", ""), episode_ids)
    package = _generate_scene_package(
        name=scene.get("name", ""),
        description=scene.get("description", ""),
        context=context,
    )

    current_package = get_scene_prompt_package(series_slug, scene_id)
    version = int(scene.get("latest_version", current_package.get("version", 1))) + 1

    series_root = get_series_path(series_slug)
    scene_dir = series_root / "scenes" / scene_id
    refs_dir = scene_dir / "refs"
    version_dir = scene_dir / "generated" / f"v{version:03d}"
    ensure_directory(refs_dir)
    ensure_directory(version_dir)

    image_size = _get_scene_sheet_size()
    output_format = _get_scene_image_output_format()
    output_extension = _get_scene_image_output_extension()
    prompt = _build_scene_sheet_prompt(scene.get("name", ""), package)
    image_bytes = _generate_reference_image(prompt, image_size)

    ref_path = refs_dir / f"scene_reference_sheet{output_extension}"
    versioned_path = version_dir / f"scene_reference_sheet{output_extension}"
    write_bytes_atomic(ref_path, image_bytes)
    write_bytes_atomic(versioned_path, image_bytes)
    _remove_stale_scene_sheet_files(refs_dir, output_extension)

    prompt_manifest = {
        "scene_id": scene_id,
        "version": version,
        "summary": package["summary"],
        "visual_profile": package["visual_profile"],
        "view_prompts": package["view_prompts"],
        "negative_prompt": package["negative_prompt"],
        "image_size": image_size,
        "output_format": output_format,
        "output_extension": output_extension,
        "quality": _get_scene_image_quality(),
        "output_compression": _get_scene_image_output_compression(),
        "episode_ids": episode_ids,
        "layout_mode": "single_sheet",
        "generated_from": {
            "context_summary": context,
        },
        "generation": {
            "image_provider": os.getenv("SCENE_IMAGE_PROVIDER", "packyapi"),
            "image_model": os.getenv("SCENE_IMAGE_MODEL", os.getenv("GPT_IMAGE_MODEL", "gpt-image-2")).strip(),
            "image_size": image_size,
            "output_format": output_format,
            "quality": _get_scene_image_quality(),
            "output_compression": _get_scene_image_output_compression(),
            "deepseek_model": os.getenv(
                "DEEPSEEK_SCENE_MODEL",
                os.getenv("DEEPSEEK_SCRIPT_MODEL", "deepseek-chat"),
            ).strip(),
            "version_dir": str(version_dir.relative_to(series_root)).replace("\\", "/"),
            "layout_mode": "single_sheet",
        },
    }
    write_json_atomic(version_dir / "prompt_package.json", prompt_manifest)

    prompt_payload = dict(prompt_manifest)
    prompt_payload["reference_images"] = {
        "sheet": str(ref_path.relative_to(series_root)).replace("\\", "/"),
    }

    manifest = save_scene_assets(
        series_slug,
        scene_id,
        version=version,
        visual_profile=package["visual_profile"],
        prompt_package=prompt_payload,
        reference_images={"sheet": str(ref_path)},
    )

    scene_prompt_package = get_scene_prompt_package(series_slug, scene_id)
    return {
        "item": manifest,
        "prompt_package": scene_prompt_package,
        "reference_images": manifest["reference_images"],
    }
