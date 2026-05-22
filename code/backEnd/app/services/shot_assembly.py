import os
import re
from typing import Any

import requests

from app.storage.character_store import get_character, get_character_bible
from app.storage.episode_store import load_parsed_script, load_raw_script
from app.storage.scene_store import get_scene, get_scene_prompt_package
from app.storage.storyboard_store import get_shot, get_storyboard, save_shot


SHOT_SIZE_TEXT = {
    "wide": "远景",
    "medium": "中景",
    "closeup": "近景",
    "extreme_closeup": "特写",
}

CAMERA_ANGLE_TEXT = {
    "eye_level": "平视",
    "high_angle": "俯视",
    "low_angle": "仰视",
    "top_down": "顶视角",
}

CAMERA_MOVEMENT_TEXT = {
    "static": "固定镜头",
    "push_in": "缓慢推进",
    "pull_out": "缓慢拉远",
    "pan": "平稳横摇",
    "tracking": "平稳跟拍",
}

DEPTH_OF_FIELD_TEXT = {
    "deep": "大景深",
    "medium": "中等景深",
    "shallow": "浅景深",
}

STYLE_TEXT = {
    "cinematic realism": "电影感写实风格",
}

MEDIA_MODE_TEXT = {
    "text_only": "纯文本",
    "reference_image": "参考生成",
    "first_frame": "首尾帧生成",
    "first_last_frame": "首尾帧生成",
}

SUPPORTED_ANCHOR_MODES = {
    "auto",
    "face_priority",
    "costume_priority",
    "aura_priority",
    "first_appearance",
    "minimal",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _list_text(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _dedupe_text(values: list[str], limit: int | None = None) -> list[str]:
    items: list[str] = []
    for value in values:
        text = _clean_text(value)
        if not text or text in items:
            continue
        items.append(text)
        if limit is not None and len(items) >= limit:
            break
    return items


def _join_cn(values: list[str], sep: str = "、") -> str:
    return sep.join([item for item in values if _clean_text(item)])


def _normalize_shot_media(shot: dict[str, Any]) -> dict[str, Any]:
    raw_media = shot.get("media") or {}
    mode = _clean_text(raw_media.get("mode", "reference_image")) or "reference_image"
    if mode == "first_frame":
        mode = "first_last_frame"
    if mode not in {"text_only", "reference_image", "first_frame", "first_last_frame"}:
        mode = "reference_image"
    return {
        "mode": mode,
        "generate_audio": bool(raw_media.get("generate_audio", True)),
        "first_frame_path": _clean_text(raw_media.get("first_frame_path", "")),
        "last_frame_path": _clean_text(raw_media.get("last_frame_path", "")),
        "reference_image_paths": _dedupe_text(_list_text(raw_media.get("reference_image_paths", []))),
    }


def _normalize_dialogue_entries(value: Any) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for item in value or []:
        if isinstance(item, dict):
            character = _clean_text(item.get("character", ""))
            text = _clean_text(item.get("text", ""))
        else:
            raw_text = _clean_text(item)
            if not raw_text:
                continue
            if ":" in raw_text:
                character, text = [part.strip() for part in raw_text.split(":", 1)]
            elif "：" in raw_text:
                character, text = [part.strip() for part in raw_text.split("：", 1)]
            else:
                character, text = "", raw_text
        if not character and not text:
            continue
        entries.append({"character": character, "text": text})
    return entries


def _dialogue_excerpt(dialogues: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in dialogues:
        speaker = _clean_text(item.get("character", ""))
        text = _clean_text(item.get("text", ""))
        if speaker and text:
            lines.append(f"{speaker}：{text}")
        elif text:
            lines.append(text)
    return " / ".join(lines)


def _numeric_suffix(value: str) -> int:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return int(digits) if digits else 0


def _normalize_script_lines(raw_text: str) -> list[str]:
    return [_clean_text(line) for line in str(raw_text or "").splitlines() if _clean_text(line)]


def _extract_raw_script_excerpt(
    *,
    raw_text: str,
    scene_location: str,
    scene_summary: str,
    shot_description: str,
    shot_beat: str,
    dialogues: list[dict[str, Any]],
    max_lines: int = 4,
) -> str:
    lines = _normalize_script_lines(raw_text)
    if not lines:
        return ""

    dialogue_needles = [_clean_text(item.get("text", "")) for item in dialogues if _clean_text(item.get("text", ""))]
    scene_needles = _dedupe_text([scene_location, scene_summary])
    shot_needles = _dedupe_text([shot_description, shot_beat])

    best_index = -1
    best_score = 0
    for index, line in enumerate(lines):
        score = 0
        for needle in dialogue_needles:
            if needle and needle in line:
                score += 6
        for needle in shot_needles:
            if needle and needle in line:
                score += 4
        for needle in scene_needles:
            if needle and needle in line:
                score += 2
        if score > best_score:
            best_score = score
            best_index = index

    if best_index < 0:
        return ""

    start = max(0, best_index - 1)
    end = min(len(lines), best_index + max_lines)
    return "\n".join(lines[start:end])


def _normalize_character_summary(value: Any) -> str:
    summary = _clean_text(value)
    if summary.lower() in {
        "based on uploaded reference image only.",
        "use uploaded reference image as the identity source.",
    }:
        return ""
    return summary


def _dialogue_excerpt(dialogues: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in dialogues:
        speaker = _clean_text(item.get("character", ""))
        text = _clean_text(item.get("text", ""))
        if speaker and text:
            lines.append(f"{speaker}: {text}")
        elif text:
            lines.append(text)
    return " / ".join(lines)


def _normalize_shot_story(shot: dict[str, Any]) -> dict[str, str]:
    raw_story = shot.get("story") or {}
    if not isinstance(raw_story, dict):
        raw_story = {}
    return {
        "description": _clean_text(raw_story.get("description", "")),
        "emotion": _clean_text(raw_story.get("emotion", "")),
        "beat": _clean_text(raw_story.get("beat", "")),
        "raw_script_excerpt": _clean_text(raw_story.get("raw_script_excerpt", "")),
    }


def _normalize_anchor_mode(value: Any) -> str:
    normalized = _clean_text(value)
    return normalized if normalized in SUPPORTED_ANCHOR_MODES else "auto"


def _normalize_shot_anchor_strategy(shot: dict[str, Any]) -> dict[str, Any]:
    raw_strategy = shot.get("anchor_strategy") or {}
    if not isinstance(raw_strategy, dict):
        raw_strategy = {}

    raw_per_character = raw_strategy.get("per_character") or {}
    if not isinstance(raw_per_character, dict):
        raw_per_character = {}

    per_character: dict[str, str] = {}
    for character_id, value in raw_per_character.items():
        normalized_character_id = _clean_text(character_id)
        if not normalized_character_id:
            continue
        normalized_mode = _normalize_anchor_mode(value.get("mode") if isinstance(value, dict) else value)
        if normalized_mode == "auto":
            continue
        per_character[normalized_character_id] = normalized_mode

    return {
        "mode": _normalize_anchor_mode(raw_strategy.get("mode")),
        "per_character": per_character,
    }


def _anchor_size_bucket(value: Any) -> str:
    normalized = _clean_text(value)
    if normalized in {"extreme_closeup", "closeup"}:
        return "closeup"
    if normalized == "medium":
        return "medium"
    return "wide"


def _is_performance_heavy(script_context: dict[str, Any]) -> bool:
    if script_context.get("dialogues") or []:
        return True
    if _clean_text(script_context.get("shot_emotion")):
        return True
    if _clean_text(script_context.get("shot_beat")):
        return True
    return False


def _anchor_type_sequence(mode: str, size_bucket: str, performance_heavy: bool) -> list[str]:
    if mode == "auto":
        if size_bucket == "closeup":
            return ["face", "aura"] if performance_heavy else ["face", "hair"]
        if size_bucket == "medium":
            return ["face", "aura"] if performance_heavy else ["face", "costume"]
        return ["costume", "aura"]
    if mode == "face_priority":
        if size_bucket == "closeup":
            return ["face", "hair"]
        return ["face", "costume"]
    if mode == "costume_priority":
        if size_bucket == "closeup":
            return ["face", "costume"]
        if size_bucket == "medium":
            return ["costume", "face"]
        return ["costume", "aura"]
    if mode == "aura_priority":
        if size_bucket == "wide":
            return ["costume", "aura"]
        return ["face", "aura"]
    if mode == "first_appearance":
        if size_bucket == "closeup":
            return ["face", "hair", "aura"]
        if size_bucket == "medium":
            return ["face", "hair", "costume"]
        return ["costume", "aura", "face"]
    if mode == "minimal":
        return ["face"] if size_bucket != "wide" else ["costume"]
    return ["face", "costume"]


def _anchor_fallback_sequence(size_bucket: str) -> list[str]:
    if size_bucket == "closeup":
        return ["face", "hair", "costume", "aura"]
    if size_bucket == "medium":
        return ["face", "costume", "hair", "aura"]
    return ["costume", "aura", "face", "hair"]


def _anchor_text_limit(mode: str, character_index: int, character_count: int) -> int:
    if character_count <= 1:
        if mode == "first_appearance":
            return 3
        if mode == "minimal":
            return 1
        return 2
    if character_count == 2:
        if character_index == 0:
            if mode == "first_appearance":
                return 3
            if mode == "minimal":
                return 1
            return 2
        if mode == "first_appearance":
            return 2
        return 1
    if character_index == 0:
        return 1 if mode == "minimal" else 2
    return 0 if mode == "minimal" else 1


def _resolve_script_context(series_slug: str, episode_id: str, scene_id: str, shot: dict[str, Any]) -> dict[str, Any]:
    parsed = load_parsed_script(series_slug, episode_id)
    raw_script = load_raw_script(series_slug, episode_id)
    scenes = parsed.get("scenes") or []
    script_source = shot.get("script_source") or {}
    scene_index = int(script_source.get("scene_index") or 0)
    shot_index = int(script_source.get("shot_index") or 0)
    inferred_shot_index = shot_index or _numeric_suffix(shot.get("id", ""))
    shot_story = _normalize_shot_story(shot)
    shot_dialogue = _normalize_dialogue_entries(shot.get("dialogue") or [])

    matched_scene = None
    matched_shot = None

    if scene_index > 0 and scene_index <= len(scenes):
        matched_scene = scenes[scene_index - 1]
        shots = matched_scene.get("shots") or []
        if shot_index > 0 and shot_index <= len(shots):
            matched_shot = shots[shot_index - 1]

    if matched_scene is None:
        scene_manifest = get_scene(series_slug, scene_id)
        scene_name = _clean_text((scene_manifest or {}).get("name", "")).lower()
        for item in scenes:
            location = _clean_text(item.get("location", "")).lower()
            if scene_name and (scene_name in location or location in scene_name):
                matched_scene = item
                break

    if matched_scene is None and len(scenes) == 1:
        matched_scene = scenes[0]

    if matched_scene and matched_shot is None:
        candidate_shots = matched_scene.get("shots") or []
        if inferred_shot_index > 0 and inferred_shot_index <= len(candidate_shots):
            matched_shot = candidate_shots[inferred_shot_index - 1]

    if matched_scene and matched_shot is None:
        candidate_shots = matched_scene.get("shots") or []
        dialogue_names = {line.get("character", "") for line in shot_dialogue}
        selected_characters = set(shot.get("characters") or [])
        for item in candidate_shots:
            item_characters = set(item.get("characters") or [])
            if item_characters & (selected_characters | dialogue_names):
                matched_shot = item
                break
        if matched_shot is None and candidate_shots:
            matched_shot = candidate_shots[0]

    if matched_scene is None:
        dialogue_names = {line.get("character", "") for line in shot_dialogue}
        selected_characters = set(shot.get("characters") or [])
        best_scene = None
        best_shot = None
        best_score = 0
        for scene in scenes:
            for candidate in scene.get("shots") or []:
                candidate_characters = set(candidate.get("characters") or [])
                score = len(candidate_characters & selected_characters) * 3 + len(candidate_characters & dialogue_names) * 2
                if score > best_score:
                    best_score = score
                    best_scene = scene
                    best_shot = candidate
        if best_scene is not None:
            matched_scene = best_scene
            matched_shot = best_shot

    matched_dialogues = _normalize_dialogue_entries((matched_shot or {}).get("dialogues") or [])
    dialogues = shot_dialogue or matched_dialogues

    scene_summary = _clean_text((matched_scene or {}).get("summary", ""))
    scene_location = _clean_text((matched_scene or {}).get("location", ""))
    shot_description = shot_story["description"] or _clean_text((matched_shot or {}).get("description", ""))
    shot_emotion = shot_story["emotion"] or _clean_text((matched_shot or {}).get("emotion", ""))
    shot_beat = shot_story["beat"] or _clean_text((matched_shot or {}).get("beat", ""))
    dialogue_excerpt = _dialogue_excerpt(dialogues)
    raw_script_excerpt = shot_story["raw_script_excerpt"] or _extract_raw_script_excerpt(
        raw_text=raw_script,
        scene_location=scene_location,
        scene_summary=scene_summary,
        shot_description=shot_description,
        shot_beat=shot_beat,
        dialogues=dialogues,
    )

    return {
        "episode_title": _clean_text(parsed.get("title", episode_id)),
        "scene_summary": scene_summary,
        "scene_location": scene_location,
        "scene_time": _clean_text((matched_scene or {}).get("time", "")),
        "shot_description": shot_description,
        "shot_emotion": shot_emotion,
        "shot_beat": shot_beat,
        "dialogues": dialogues,
        "dialogue_excerpt": dialogue_excerpt,
        "raw_script_excerpt": raw_script_excerpt,
    }


def _preferred_character_reference_paths(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    refs = manifest.get("reference_images") or {}
    sheet_paths = _dedupe_text([refs.get("sheet", "")], limit=1)
    return sheet_paths, sheet_paths


def _assemble_character_blocks(series_slug: str, character_ids: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    blocks: list[dict[str, Any]] = []
    negatives: list[str] = []

    for character_id in character_ids:
        manifest = get_character(series_slug, character_id)
        if manifest is None:
            continue
        bible = get_character_bible(series_slug, character_id)
        primary_ref_paths, all_ref_paths = _preferred_character_reference_paths(manifest)

        blocks.append(
            {
                "id": character_id,
                "name": manifest.get("name", character_id),
                "summary": _normalize_character_summary(bible.get("summary", "")),
                "anchors": manifest.get("anchors", {}),
                "continuity_rules": ((bible.get("bible") or {}).get("continuity_rules") or []),
                "reference_images": all_ref_paths,
                "preferred_reference_images": primary_ref_paths,
            }
        )
        if bible.get("negative_prompt"):
            negatives.append(str(bible["negative_prompt"]).strip())

    return blocks, negatives


def _assemble_scene_block(series_slug: str, scene_id: str) -> tuple[dict[str, Any], list[str]]:
    manifest = get_scene(series_slug, scene_id)
    if manifest is None:
        raise FileNotFoundError(scene_id)

    prompt_package = get_scene_prompt_package(series_slug, scene_id)
    refs = manifest.get("reference_images") or {}
    preferred_ref_paths = _dedupe_text([refs.get("sheet", "")], limit=1)
    all_ref_paths = _dedupe_text([refs.get("sheet", "")])
    negatives = []
    if prompt_package.get("negative_prompt"):
        negatives.append(str(prompt_package["negative_prompt"]).strip())

    block = {
        "id": scene_id,
        "name": manifest.get("name", scene_id),
        "description": manifest.get("description", ""),
        "summary": prompt_package.get("summary", ""),
        "visual_profile": prompt_package.get("visual_profile", manifest.get("visual_profile", {})),
        "view_prompts": prompt_package.get("view_prompts", {}),
        "reference_images": all_ref_paths,
        "preferred_reference_images": preferred_ref_paths,
    }
    return block, negatives


def _append_reference(references: list[dict[str, Any]], **kwargs: Any) -> None:
    path = _clean_text(kwargs.get("path", ""))
    if not path:
        return
    references.append(
        {
            "type": kwargs.get("type", "image"),
            "path": path,
            "role": kwargs.get("role", "reference_image"),
            "source_kind": kwargs.get("source_kind", "shot"),
            "source_id": kwargs.get("source_id", ""),
            "source_name": kwargs.get("source_name", ""),
            "source_detail": kwargs.get("source_detail", ""),
        }
    )


def _has_any_media_inputs(shot_media: dict[str, Any]) -> bool:
    return bool(
        shot_media.get("first_frame_path")
        or shot_media.get("last_frame_path")
        or shot_media.get("reference_image_paths")
    )


def _reference_token(label: str) -> str:
    normalized = _clean_text(label)
    return f"@{normalized}" if normalized else ""


def _reference_tokens(labels: list[str]) -> str:
    return _join_cn([_reference_token(label) for label in labels if _clean_text(label)])


def _format_mode_warning(text: str) -> str:
    return f"当前模式下已忽略{text}"


def _build_media_references(
    shot_media: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    scene_block: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    references: list[dict[str, Any]] = []
    warnings: list[str] = []
    mode = shot_media.get("mode", "reference_image")

    if mode == "text_only":
        if _has_any_media_inputs(shot_media):
            warnings.append(_format_mode_warning("首帧、尾帧和参考图片。"))
        return references, warnings

    if mode == "reference_image":
        if _has_any_media_inputs(shot_media):
            warnings.append(_format_mode_warning("首帧、尾帧和手动上传参考图片，参考生成模式只使用角色圣经拼图与场景参考拼图。"))

        for block in character_blocks:
            for path in block.get("preferred_reference_images", []):
                _append_reference(
                    references,
                    type="image",
                    path=path,
                    role="reference_image",
                    source_kind="character",
                    source_id=block["id"],
                    source_name=block["name"],
                    source_detail="角色圣经拼图",
                )
        for path in scene_block.get("preferred_reference_images", []):
            _append_reference(
                references,
                type="image",
                path=path,
                role="reference_image",
                source_kind="scene",
                source_id=scene_block["id"],
                source_name=scene_block["name"],
                source_detail="场景参考拼图",
            )
        if not references:
            warnings.append("参考生成模式未找到角色圣经拼图或场景参考拼图，将退化为纯文字描述。")

    elif mode in {"first_frame", "first_last_frame"}:
        first_frame_path = _clean_text(shot_media.get("first_frame_path", ""))
        last_frame_path = _clean_text(shot_media.get("last_frame_path", ""))
        if not first_frame_path:
            raise ValueError("首尾帧生成模式必须提供首帧图。")

        _append_reference(
            references,
            type="image",
            path=first_frame_path,
            role="first_frame",
            source_kind="shot",
            source_name="首帧",
            source_detail="首帧",
        )
        if last_frame_path:
            _append_reference(
                references,
                type="image",
                path=last_frame_path,
                role="last_frame",
                source_kind="shot",
                source_name="尾帧",
                source_detail="尾帧",
            )
        if shot_media.get("reference_image_paths"):
            warnings.append(_format_mode_warning("补充参考图片，首尾帧生成模式只使用首帧和尾帧。"))
    else:
        raise ValueError(f"不支持的镜头输入模式：{mode}")

    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for item in references:
        dedupe_key = (item["type"], item["role"], item["path"])
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped.append(item)

    type_limits = {"image": 9}
    type_counts = {"image": 0}
    limited: list[dict[str, Any]] = []
    for item in deduped:
        item_type = item["type"]
        type_counts[item_type] += 1
        if type_counts[item_type] > type_limits[item_type]:
            continue
        limited.append(item)

    if type_counts["image"] > type_limits["image"]:
        warnings.append("参考图片超过 Seedance 2.0 上限，已截断为前 9 张。")

    label_counts = {"image": 0}
    label_prefix = {"image": "图像"}
    for item in limited:
        item_type = item["type"]
        label_counts[item_type] += 1
        item["index"] = label_counts[item_type]
        item["label"] = f"{label_prefix[item_type]}{label_counts[item_type]}"

    return limited, warnings


def _compose_subject_features(
    block: dict[str, Any],
    *,
    mode: str,
    size_bucket: str,
    performance_heavy: bool,
    character_index: int,
    character_count: int,
) -> str:
    limit = _anchor_text_limit(mode, character_index, character_count)
    if limit <= 0:
        return ""

    anchors = block.get("anchors", {}) or {}
    requested_types = _anchor_type_sequence(mode, size_bucket, performance_heavy)
    fallback_types = _anchor_fallback_sequence(size_bucket)

    features: list[str] = []
    used_types: set[str] = set()

    for anchor_type in [*requested_types, *fallback_types]:
        normalized_type = _clean_text(anchor_type)
        if not normalized_type or normalized_type in used_types:
            continue
        used_types.add(normalized_type)
        feature_text = _compact_prompt_fragment(anchors.get(normalized_type, ""), max_parts=3, max_chars=40)
        if not feature_text or feature_text in features:
            continue
        features.append(feature_text)
        if len(features) >= limit:
            break

    if len(features) < limit:
        summary = _compact_prompt_fragment(_normalize_character_summary(block.get("summary", "")), max_parts=2, max_chars=32)
        if summary and summary not in features:
            features.append(summary)

    return _join_cn(features[:limit])


def _describe_dialogue(dialogues: list[dict[str, Any]]) -> str:
    sentences: list[str] = []
    for item in dialogues:
        speaker = _clean_text(item.get("character", ""))
        text = _clean_text(item.get("text", ""))
        if speaker and text:
            sentences.append(f"{speaker}说：“{text}”")
        elif text:
            sentences.append(f"画外音说：“{text}”")
    return "，".join(sentences)


def _translate_visual_term(value: str, mapping: dict[str, str]) -> str:
    normalized = _clean_text(value)
    if not normalized:
        return ""
    return mapping.get(normalized, normalized)


def _build_mode_prompt_intro(shot_media: dict[str, Any], media_references: list[dict[str, Any]]) -> list[str]:
    labels_by_role: dict[str, list[str]] = {}
    labels_by_source: dict[tuple[str, str], list[str]] = {}
    for item in media_references:
        labels_by_role.setdefault(item.get("role", ""), []).append(item.get("label", ""))
        labels_by_source.setdefault((item.get("source_kind", ""), item.get("source_id", "")), []).append(item.get("label", ""))

    intro_sections: list[str] = []
    mode = shot_media.get("mode", "reference_image")
    first_frame_labels = labels_by_role.get("first_frame", [])
    last_frame_labels = labels_by_role.get("last_frame", [])
    image_labels = labels_by_role.get("reference_image", [])

    if mode == "first_frame" and first_frame_labels:
        intro_sections.append(f"首尾帧生成：以{_reference_token(first_frame_labels[0])}作为首帧，保持开场主体与构图稳定。")
    elif mode == "first_last_frame" and first_frame_labels:
        if last_frame_labels:
            intro_sections.append(
                f"首尾帧生成：以{_reference_token(first_frame_labels[0])}作为首帧，以{_reference_token(last_frame_labels[0])}作为尾帧，生成两者之间自然连贯的过渡。"
            )
        else:
            intro_sections.append(f"首尾帧生成：以{_reference_token(first_frame_labels[0])}作为首帧，尾帧未提供，请根据剧情自然完成后续镜头。")
    elif mode == "reference_image" and image_labels:
        role_segments: list[str] = []
        for item in media_references:
            if item.get("source_kind") == "character":
                role_segments.append(f"{_reference_token(item.get('label', ''))}对应角色{item.get('source_name', '')}")
            elif item.get("source_kind") == "scene":
                role_segments.append(f"{_reference_token(item.get('label', ''))}对应场景{item.get('source_name', '')}")
        intro_sections.append("参考生成：" + "，".join(_dedupe_text(role_segments)) + "。")
    elif mode == "text_only":
        intro_sections.append("纯文字生成：仅依据文字描述生成，不使用任何图像参考。")

    return intro_sections


def _build_seedance_prompt(
    *,
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    media_references: list[dict[str, Any]],
    script_context: dict[str, Any],
    shot: dict[str, Any],
    shot_media: dict[str, Any],
    warnings: list[str],
) -> tuple[str, list[str]]:
    visual = shot.get("visual") or {}
    scene_profile = scene_block.get("visual_profile", {})
    mode = shot_media.get("mode", "reference_image")
    anchor_strategy = _normalize_shot_anchor_strategy(shot)
    size_bucket = _anchor_size_bucket(visual.get("shot_size", ""))
    performance_heavy = _is_performance_heavy(script_context)
    media_labels_by_source: dict[tuple[str, str], list[str]] = {}
    for item in media_references:
        key = (item.get("source_kind", ""), item.get("source_id", ""))
        media_labels_by_source.setdefault(key, []).append(item.get("label", ""))

    prompt_sections: list[str] = []
    mode_intro = _build_mode_prompt_intro(shot_media, media_references)
    if mode_intro:
        prompt_sections.extend(mode_intro)

    if mode == "reference_image":
        subject_lines: list[str] = []
        reference_character_blocks = [
            block for block in character_blocks if media_labels_by_source.get(("character", block["id"]), [])
        ]
        character_count = len(reference_character_blocks)
        for character_index, block in enumerate(reference_character_blocks):
            labels = media_labels_by_source.get(("character", block["id"]), [])
            effective_mode = anchor_strategy["per_character"].get(block["id"], anchor_strategy["mode"])
            feature_text = _compose_subject_features(
                block,
                mode=effective_mode,
                size_bucket=size_bucket,
                performance_heavy=performance_heavy,
                character_index=character_index,
                character_count=character_count,
            )
            subject_lines.append(
                f"{_reference_tokens(labels)}中的角色定义为{block['name']}，保持{feature_text or '角色外观、体态与身份特征'}稳定。"
            )
        if subject_lines:
            prompt_sections.append("角色匹配：" + "；".join(subject_lines) + "。")

        scene_labels = media_labels_by_source.get(("scene", scene_block["id"]), [])
        scene_summary = _clean_text(script_context.get("scene_summary") or scene_block.get("summary") or scene_block.get("description"))
        if scene_labels:
            prompt_sections.append(
                "场景匹配："
                f"{_reference_tokens(scene_labels)}对应场景{scene_block['name']}，保持"
                f"{scene_summary or scene_block['name']}的空间关系、环境气质与布光基调。"
            )

    shot_description = _clean_text(script_context.get("shot_description"))
    shot_emotion = _clean_text(script_context.get("shot_emotion"))
    shot_beat = _clean_text(script_context.get("shot_beat"))
    dialogue_text = _describe_dialogue(script_context.get("dialogues") or [])
    dialogue_excerpt_text = _clean_text(script_context.get("dialogue_excerpt"))
    raw_script_excerpt_text = _clean_text(script_context.get("raw_script_excerpt"))

    movement_text = _translate_visual_term(visual.get("camera_movement", ""), CAMERA_MOVEMENT_TEXT) or "固定镜头"
    angle_text = _translate_visual_term(visual.get("camera_angle", ""), CAMERA_ANGLE_TEXT) or "平视"
    shot_size_text = _translate_visual_term(visual.get("shot_size", ""), SHOT_SIZE_TEXT) or "中景"
    style_text = _translate_visual_term(visual.get("style", ""), STYLE_TEXT) or _clean_text(visual.get("style", ""))
    depth_of_field_text = _translate_visual_term(visual.get("depth_of_field", ""), DEPTH_OF_FIELD_TEXT)
    lens_text = _clean_text(visual.get("lens", ""))

    location_text = _clean_text(script_context.get("scene_location"))
    time_text = _clean_text(script_context.get("scene_time") or scene_profile.get("time", ""))
    weather_text = _clean_text(scene_profile.get("weather", ""))
    lighting_text = _clean_text(visual.get("lighting") or scene_profile.get("lighting", ""))
    palette_text = _clean_text(visual.get("palette") or scene_profile.get("palette", ""))
    atmosphere_text = _clean_text(scene_profile.get("atmosphere", ""))
    architecture_text = _clean_text(scene_profile.get("architecture", ""))
    key_props_text = _join_cn(_list_text(scene_profile.get("key_props")))
    ratio_text = _clean_text(visual.get("aspect_ratio", ""))
    resolution_text = _clean_text(visual.get("resolution", ""))
    duration_seconds = int(visual.get("duration_seconds") or 5)
    generation_count = int(visual.get("generation_count") or 1)
    audio_text = "需要同步生成声音" if bool(shot_media.get("generate_audio")) else "无需生成声音"

    action_parts = _dedupe_text(
        [
            shot_description,
            shot_beat,
            shot_emotion and f"情绪基调是{shot_emotion}",
            dialogue_text,
        ]
    )
    if not action_parts:
        action_parts = ["围绕当前剧情节点推进动作与情绪变化，动作自然连贯。"]

    environment_parts = _dedupe_text(
        [
            location_text and f"场景位于{location_text}",
            time_text and f"时间为{time_text}",
            weather_text and f"天气为{weather_text}",
            lighting_text and f"光线为{lighting_text}",
            palette_text and f"画面色调为{palette_text}",
            style_text and f"整体风格为{style_text}",
            atmosphere_text and f"氛围为{atmosphere_text}",
            architecture_text and f"环境结构呈现{architecture_text}",
            key_props_text and f"关键元素包含{key_props_text}",
        ]
    )

    camera_parts = _dedupe_text(
        [
            f"镜头采用{shot_size_text}",
            angle_text and f"{angle_text}视角",
            movement_text,
            lens_text and f"{lens_text}镜头语言",
            depth_of_field_text,
        ]
    )

    output_parts = _dedupe_text(
        [
            ratio_text and f"画面比例为{ratio_text}",
            resolution_text and f"分辨率为{resolution_text}",
            f"时长为{duration_seconds}秒",
            f"一次生成{generation_count}条结果",
            audio_text,
        ]
    )

    if raw_script_excerpt_text:
        prompt_sections.append("剧本原文摘录：\n" + raw_script_excerpt_text)
    elif dialogue_excerpt_text:
        prompt_sections.append("当前镜头台词片段：" + dialogue_excerpt_text + "。")

    if raw_script_excerpt_text and dialogue_excerpt_text:
        prompt_sections.append("当前镜头台词片段：" + dialogue_excerpt_text + "。")

    prompt_sections.append(
        "文字描述："
        + "，".join(action_parts)
        + "。"
        + ("，".join(environment_parts) + "。" if environment_parts else "")
        + ("镜头设计使用" + "，".join(camera_parts) + "。" if camera_parts else "")
    )
    if output_parts:
        prompt_sections.append("输出规格：" + "，".join(output_parts) + "。")

    constraints = _dedupe_text(
        [
            "画面高清，细节丰富，人物面部稳定不变形",
            "动作自然流畅，不僵硬，不抽搐，不闪烁",
            "保持无字幕",
            "不要生成Logo",
            "不要生成水印",
            "同一画面不出现重复人物，不出现双胞胎效果",
            "不出现肢体畸形、穿模、额外手脚",
        ]
    )
    prompt_sections.append("画质与约束：" + "，".join(constraints) + "。")

    if warnings:
        prompt_sections.append("备注：" + "；".join(warnings) + "。")

    prompt_text = "\n".join([section for section in prompt_sections if _clean_text(section)])
    return prompt_text, constraints


def _compose_subject_features(
    block: dict[str, Any],
    *,
    mode: str,
    size_bucket: str,
    performance_heavy: bool,
    character_index: int,
    character_count: int,
) -> str:
    limit = _anchor_text_limit(mode, character_index, character_count)
    if limit <= 0:
        return ""

    anchors = block.get("anchors", {}) or {}
    requested_types = _anchor_type_sequence(mode, size_bucket, performance_heavy)
    fallback_types = _anchor_fallback_sequence(size_bucket)

    features: list[str] = []
    used_types: set[str] = set()

    for anchor_type in [*requested_types, *fallback_types]:
        normalized_type = _clean_text(anchor_type)
        if not normalized_type or normalized_type in used_types:
            continue
        used_types.add(normalized_type)
        feature_text = _compact_prompt_fragment(anchors.get(normalized_type, ""), max_parts=3, max_chars=40)
        if not feature_text or feature_text in features:
            continue
        features.append(feature_text)
        if len(features) >= limit:
            break

    if len(features) < limit:
        summary = _compact_prompt_fragment(_normalize_character_summary(block.get("summary", "")), max_parts=2, max_chars=32)
        if summary and summary not in features:
            features.append(summary)

    return _join_cn(features[:limit])


def _build_mode_prompt_intro(shot_media: dict[str, Any], media_references: list[dict[str, Any]]) -> list[str]:
    labels_by_role: dict[str, list[str]] = {}
    for item in media_references:
        labels_by_role.setdefault(item.get("role", ""), []).append(item.get("label", ""))

    intro_sections: list[str] = []
    mode = shot_media.get("mode", "reference_image")
    first_frame_labels = labels_by_role.get("first_frame", [])
    last_frame_labels = labels_by_role.get("last_frame", [])
    image_labels = labels_by_role.get("reference_image", [])

    if mode == "first_frame" and first_frame_labels:
        intro_sections.append(f"首尾帧绑定：{_reference_token(first_frame_labels[0])} 为首帧，保持开场主体、动作起点和构图关系稳定。")
    elif mode == "first_last_frame" and first_frame_labels:
        if last_frame_labels:
            intro_sections.append(
                f"首尾帧绑定：{_reference_token(first_frame_labels[0])} 为首帧，{_reference_token(last_frame_labels[0])} 为尾帧，生成两者之间自然连贯的动作与镜头过渡。"
            )
        else:
            intro_sections.append(f"首尾帧绑定：{_reference_token(first_frame_labels[0])} 为首帧，尾帧未提供，请根据剧情自然完成后续动作。")
    elif mode == "reference_image" and image_labels:
        role_segments: list[str] = []
        for item in media_references:
            if item.get("source_kind") == "character":
                role_segments.append(f"{_reference_token(item.get('label', ''))}对应角色{item.get('source_name', '')}")
            elif item.get("source_kind") == "scene":
                role_segments.append(f"{_reference_token(item.get('label', ''))}对应场景{item.get('source_name', '')}")
        intro_sections.append("参考图绑定：" + "，".join(_dedupe_text(role_segments)) + "。")
    elif mode == "text_only":
        intro_sections.append("纯文字生成：仅依据文字描述生成，不使用任何图像参考。")

    return intro_sections


def _build_character_consistency_line(
    *,
    block: dict[str, Any],
    labels: list[str],
    feature_text: str,
) -> str:
    label_text = _reference_tokens(labels)
    fallback = "整体外形、表情气质和身份特征稳定"
    return f"保持{block['name']}与{label_text}一致，{feature_text or fallback}。"


def _build_scene_consistency_line(
    *,
    scene_block: dict[str, Any],
    scene_labels: list[str],
    script_context: dict[str, Any],
    scene_profile: dict[str, Any],
) -> str:
    scene_name = _clean_text(scene_block.get("name", ""))
    label_text = _reference_tokens(scene_labels)
    scene_parts = _dedupe_text(
        [
            _compact_prompt_fragment(script_context.get("scene_location"), max_parts=1, max_chars=16),
            _compact_prompt_fragment(scene_profile.get("lighting", ""), max_parts=2, max_chars=24),
            _compact_prompt_fragment(scene_profile.get("atmosphere", ""), max_parts=2, max_chars=20),
            _join_cn(_dedupe_text(_list_text(scene_profile.get("key_props")), limit=2), sep="、"),
        ],
        limit=3,
    )
    if scene_parts:
        return f"保持{scene_name}与{label_text}一致，延续" + "、".join(scene_parts) + "。"
    return f"保持{scene_name}与{label_text}一致，延续空间关系、环境气质和布光基调。"


def _build_story_basis_line(script_context: dict[str, Any]) -> str:
    raw_script_excerpt = _clean_text(script_context.get("raw_script_excerpt"))
    dialogue_excerpt = _clean_text(script_context.get("dialogue_excerpt"))
    if raw_script_excerpt:
        return "剧情依据：\n" + raw_script_excerpt
    if dialogue_excerpt:
        return "剧情依据：" + dialogue_excerpt + "。"
    return ""


def _build_action_line(
    *,
    shot_description: str,
    shot_beat: str,
    shot_emotion: str,
    dialogue_text: str,
) -> str:
    action_parts = _dedupe_text(
        [
            _clean_text(shot_description).rstrip("，。；; "),
            shot_beat and _clean_text(f"重点表现{shot_beat}").rstrip("，。；; "),
            shot_emotion and _clean_text(f"情绪为{shot_emotion}").rstrip("，。；; "),
            _clean_text(dialogue_text).rstrip("，。；; "),
        ]
    )
    if not action_parts:
        return "镜头内容：围绕当前剧情节点推进角色动作与情绪变化，动作自然连贯。"
    return "镜头内容：" + "，".join(action_parts) + "。"


def _build_scene_and_camera_line(
    *,
    script_context: dict[str, Any],
    scene_profile: dict[str, Any],
    shot_size_text: str,
    angle_text: str,
    movement_text: str,
    lens_text: str,
    depth_of_field_text: str,
    style_text: str,
) -> str:
    scene_parts = _dedupe_text(
        [
            _compact_prompt_fragment(script_context.get("scene_location"), max_parts=1, max_chars=16),
            _compact_prompt_fragment(scene_profile.get("time", ""), max_parts=2, max_chars=20),
            _compact_prompt_fragment(scene_profile.get("lighting", ""), max_parts=2, max_chars=24),
            _compact_prompt_fragment(scene_profile.get("atmosphere", ""), max_parts=2, max_chars=20),
            _join_cn(_dedupe_text(_list_text(scene_profile.get("key_props")), limit=2), sep="、"),
            _compact_prompt_fragment(style_text, max_parts=2, max_chars=20),
        ],
        limit=4,
    )
    camera_parts = _dedupe_text(
        [
            shot_size_text,
            angle_text,
            movement_text,
            lens_text,
            depth_of_field_text,
        ]
    )

    scene_clause = ""
    if scene_parts:
        scene_clause = "保持场景中的" + "、".join(scene_parts) + "。"
    camera_clause = ""
    if camera_parts:
        camera_clause = "镜头语言使用" + "，".join(camera_parts) + "。"
    return "场景与镜头语言：" + scene_clause + camera_clause


def _build_seedance_prompt(
    *,
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    media_references: list[dict[str, Any]],
    script_context: dict[str, Any],
    shot: dict[str, Any],
    shot_media: dict[str, Any],
    warnings: list[str],
) -> tuple[str, list[str]]:
    visual = shot.get("visual") or {}
    scene_profile = scene_block.get("visual_profile", {})
    mode = shot_media.get("mode", "reference_image")
    anchor_strategy = _normalize_shot_anchor_strategy(shot)
    size_bucket = _anchor_size_bucket(visual.get("shot_size", ""))
    performance_heavy = _is_performance_heavy(script_context)
    media_labels_by_source: dict[tuple[str, str], list[str]] = {}
    for item in media_references:
        key = (item.get("source_kind", ""), item.get("source_id", ""))
        media_labels_by_source.setdefault(key, []).append(item.get("label", ""))

    prompt_sections: list[str] = []
    prompt_sections.extend(_build_mode_prompt_intro(shot_media, media_references))

    if mode == "reference_image":
        consistency_lines: list[str] = []
        reference_character_blocks = [
            block for block in character_blocks if media_labels_by_source.get(("character", block["id"]), [])
        ]
        character_count = len(reference_character_blocks)
        for character_index, block in enumerate(reference_character_blocks):
            labels = media_labels_by_source.get(("character", block["id"]), [])
            effective_mode = anchor_strategy["per_character"].get(block["id"], anchor_strategy["mode"])
            feature_text = _compose_subject_features(
                block,
                mode=effective_mode,
                size_bucket=size_bucket,
                performance_heavy=performance_heavy,
                character_index=character_index,
                character_count=character_count,
            )
            consistency_lines.append(
                _build_character_consistency_line(
                    block=block,
                    labels=labels,
                    feature_text=feature_text,
                )
            )

        scene_labels = media_labels_by_source.get(("scene", scene_block["id"]), [])
        if scene_labels:
            consistency_lines.append(
                _build_scene_consistency_line(
                    scene_block=scene_block,
                    scene_labels=scene_labels,
                    script_context=script_context,
                    scene_profile=scene_profile,
                )
            )

        if consistency_lines:
            prompt_sections.append("一致性要求：" + "".join(consistency_lines))

    story_basis = _build_story_basis_line(script_context)
    if story_basis:
        prompt_sections.append(story_basis)

    shot_description = _clean_text(script_context.get("shot_description"))
    shot_emotion = _clean_text(script_context.get("shot_emotion"))
    shot_beat = _clean_text(script_context.get("shot_beat"))
    dialogue_text = _describe_dialogue(script_context.get("dialogues") or [])

    movement_text = _translate_visual_term(visual.get("camera_movement", ""), CAMERA_MOVEMENT_TEXT) or "固定镜头"
    angle_text = _translate_visual_term(visual.get("camera_angle", ""), CAMERA_ANGLE_TEXT) or "平视"
    shot_size_text = _translate_visual_term(visual.get("shot_size", ""), SHOT_SIZE_TEXT) or "中景"
    style_text = _translate_visual_term(visual.get("style", ""), STYLE_TEXT) or _clean_text(visual.get("style", ""))
    depth_of_field_text = _translate_visual_term(visual.get("depth_of_field", ""), DEPTH_OF_FIELD_TEXT)
    lens_text = _clean_text(visual.get("lens", ""))

    prompt_sections.append(
        _build_action_line(
            shot_description=shot_description,
            shot_beat=shot_beat,
            shot_emotion=shot_emotion,
            dialogue_text=dialogue_text,
        )
    )
    prompt_sections.append(
        _build_scene_and_camera_line(
            script_context=script_context,
            scene_profile=scene_profile,
            shot_size_text=shot_size_text,
            angle_text=angle_text,
            movement_text=movement_text,
            lens_text=lens_text,
            depth_of_field_text=depth_of_field_text,
            style_text=style_text,
        )
    )

    constraints = _dedupe_text(
        [
            "人物外形稳定，不要改设定，不要变形",
            "动作自然流畅，不僵硬，不抽搐，不闪烁",
            "同一画面不要出现重复人物或双胞胎效果",
            "不要出现肢体畸形、穿模、额外手脚",
            "不要出现字幕、Logo、水印",
        ]
    )
    prompt_sections.append("约束：" + "，".join(constraints) + "。")

    if warnings:
        prompt_sections.append("备注：" + "；".join(warnings) + "。")

    prompt_text = "\n".join([section for section in prompt_sections if _clean_text(section)])
    return prompt_text, constraints


def _compact_prompt_fragment(value: Any, *, max_parts: int = 2, max_chars: int = 36) -> str:
    text = _clean_text(value)
    if not text:
        return ""

    parts: list[str] = []
    for chunk in re.split(r"[，。；;、/]+", text):
        normalized = _clean_text(chunk)
        if not normalized or normalized in parts:
            continue
        parts.append(normalized)
        if len(parts) >= max_parts:
            break

    compact = "，".join(parts) if parts else text
    compact = compact.replace("，，", "，").strip("，。；; ")
    if len(compact) > max_chars:
        compact = compact[:max_chars].rstrip("，。；; ")
    return compact


def _build_video_payload(
    *,
    prompt_text: str,
    negative_prompt: str,
    media_references: list[dict[str, Any]],
    visual: dict[str, Any],
    shot_media: dict[str, Any],
) -> dict[str, Any]:
    reference_images = [item["path"] for item in media_references if item.get("type") == "image"]

    return {
        "provider": "doubao-seedance-2-0",
        "prompt": prompt_text,
        "negative_prompt": negative_prompt,
        "reference_images": reference_images,
        "media_references": media_references,
        "ratio": visual.get("aspect_ratio", ""),
        "aspect_ratio": visual.get("aspect_ratio", ""),
        "resolution": visual.get("resolution", ""),
        "duration": visual.get("duration_seconds", 5),
        "duration_seconds": visual.get("duration_seconds", 5),
        "count": visual.get("generation_count", 1),
        "generate_audio": bool(shot_media.get("generate_audio")),
        "watermark": False,
        "mode": shot_media.get("mode", "reference_image"),
    }


SHOT_PROMPT_SYSTEM_PROMPT = """
你是视频生成提示词润色助手。你的任务是把结构化的单镜头信息改写成一段可直接提交给 Seedance 2.0 的中文提示词。
要求：
1. 只输出最终提示词，不要解释，不要 Markdown，不要代码块。
2. 只能润色表达，不能改动角色名、场景名、参考图编号、镜头类型、运镜、景别、镜头参数、台词内容。
3. 必须保留所有 @图像N 的引用，不要改编号，不要遗漏。
4. 不要新增剧情，不要扩写成多镜头，不要发散出原输入没有的设定。
5. 重点让语言更自然、更像视频模型的拍摄指令，而不是数据库字段拼接。
6. 输出应围绕：参考绑定、一致性要求、剧情依据、镜头内容、场景与镜头语言、约束。
""".strip()


def _build_shot_prompt_skeleton(
    *,
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    media_references: list[dict[str, Any]],
    script_context: dict[str, Any],
    shot: dict[str, Any],
    shot_media: dict[str, Any],
    warnings: list[str],
) -> tuple[dict[str, Any], list[str]]:
    visual = shot.get("visual") or {}
    scene_profile = scene_block.get("visual_profile", {})
    mode = shot_media.get("mode", "reference_image")
    anchor_strategy = _normalize_shot_anchor_strategy(shot)
    size_bucket = _anchor_size_bucket(visual.get("shot_size", ""))
    performance_heavy = _is_performance_heavy(script_context)
    media_labels_by_source: dict[tuple[str, str], list[str]] = {}
    for item in media_references:
        key = (item.get("source_kind", ""), item.get("source_id", ""))
        media_labels_by_source.setdefault(key, []).append(item.get("label", ""))

    consistency_lines: list[str] = []
    if mode == "reference_image":
        reference_character_blocks = [
            block for block in character_blocks if media_labels_by_source.get(("character", block["id"]), [])
        ]
        character_count = len(reference_character_blocks)
        for character_index, block in enumerate(reference_character_blocks):
            labels = media_labels_by_source.get(("character", block["id"]), [])
            effective_mode = anchor_strategy["per_character"].get(block["id"], anchor_strategy["mode"])
            feature_text = _compose_subject_features(
                block,
                mode=effective_mode,
                size_bucket=size_bucket,
                performance_heavy=performance_heavy,
                character_index=character_index,
                character_count=character_count,
            )
            consistency_lines.append(
                _build_character_consistency_line(
                    block=block,
                    labels=labels,
                    feature_text=feature_text,
                )
            )

        scene_labels = media_labels_by_source.get(("scene", scene_block["id"]), [])
        if scene_labels:
            consistency_lines.append(
                _build_scene_consistency_line(
                    scene_block=scene_block,
                    scene_labels=scene_labels,
                    script_context=script_context,
                    scene_profile=scene_profile,
                )
            )

    shot_description = _clean_text(script_context.get("shot_description"))
    shot_emotion = _clean_text(script_context.get("shot_emotion"))
    shot_beat = _clean_text(script_context.get("shot_beat"))
    dialogue_text = _describe_dialogue(script_context.get("dialogues") or [])

    movement_text = _translate_visual_term(visual.get("camera_movement", ""), CAMERA_MOVEMENT_TEXT) or "固定镜头"
    angle_text = _translate_visual_term(visual.get("camera_angle", ""), CAMERA_ANGLE_TEXT) or "平视"
    shot_size_text = _translate_visual_term(visual.get("shot_size", ""), SHOT_SIZE_TEXT) or "中景"
    style_text = _translate_visual_term(visual.get("style", ""), STYLE_TEXT) or _clean_text(visual.get("style", ""))
    depth_of_field_text = _translate_visual_term(visual.get("depth_of_field", ""), DEPTH_OF_FIELD_TEXT)
    lens_text = _clean_text(visual.get("lens", ""))

    constraints = _dedupe_text(
        [
            "人物外形稳定，不要改设定，不要变形",
            "动作自然流畅，不僵硬，不抽搐，不闪烁",
            "同一画面不要出现重复人物或双胞胎效果",
            "不要出现肢体畸形、穿模、额外手脚",
            "不要出现字幕、Logo、水印",
        ]
    )

    skeleton = {
        "mode_intro": _build_mode_prompt_intro(shot_media, media_references),
        "consistency_lines": consistency_lines,
        "story_basis": _build_story_basis_line(script_context),
        "action_line": _build_action_line(
            shot_description=shot_description,
            shot_beat=shot_beat,
            shot_emotion=shot_emotion,
            dialogue_text=dialogue_text,
        ),
        "scene_camera_line": _build_scene_and_camera_line(
            script_context=script_context,
            scene_profile=scene_profile,
            shot_size_text=shot_size_text,
            angle_text=angle_text,
            movement_text=movement_text,
            lens_text=lens_text,
            depth_of_field_text=depth_of_field_text,
            style_text=style_text,
        ),
        "constraints": constraints,
        "warnings": [_clean_text(item) for item in warnings if _clean_text(item)],
    }
    return skeleton, constraints


def _build_shot_prompt_fallback(skeleton: dict[str, Any]) -> str:
    sections: list[str] = []
    sections.extend(skeleton.get("mode_intro") or [])
    if skeleton.get("consistency_lines"):
        sections.append("一致性要求：" + "".join(skeleton["consistency_lines"]))
    if _clean_text(skeleton.get("story_basis", "")):
        sections.append(_clean_text(skeleton["story_basis"]))
    if _clean_text(skeleton.get("action_line", "")):
        sections.append(_clean_text(skeleton["action_line"]))
    if _clean_text(skeleton.get("scene_camera_line", "")):
        sections.append(_clean_text(skeleton["scene_camera_line"]))
    if skeleton.get("constraints"):
        sections.append("约束：" + "，".join(skeleton["constraints"]) + "。")
    if skeleton.get("warnings"):
        sections.append("备注：" + "；".join(skeleton["warnings"]) + "。")
    return "\n".join([section for section in sections if _clean_text(section)])


def _call_deepseek_shot_prompt(skeleton: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing DEEPSEEK_API_KEY")

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://www.packyapi.com/v1").rstrip("/")
    model = os.getenv("DEEPSEEK_SHOT_PROMPT_MODEL", "deepseek-v4-pro").strip() or "deepseek-v4-pro"

    user_content = (
        "请根据以下单镜头结构化输入，输出最终可提交的中文提示词。\n\n"
        f"参考绑定：{chr(10).join(skeleton.get('mode_intro') or [])}\n"
        f"一致性要求：{''.join(skeleton.get('consistency_lines') or [])}\n"
        f"{skeleton.get('story_basis', '')}\n"
        f"{skeleton.get('action_line', '')}\n"
        f"{skeleton.get('scene_camera_line', '')}\n"
        f"约束：{'，'.join(skeleton.get('constraints') or [])}\n"
        f"备注：{'；'.join(skeleton.get('warnings') or [])}\n"
    ).strip()

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0.2,
                "max_tokens": 1200,
                "messages": [
                    {"role": "system", "content": SHOT_PROMPT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            },
            timeout=180,
        )
    except requests.RequestException as exc:
        raise ValueError(f"DeepSeek 单镜头提示词润色请求失败：{exc}") from exc
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"DeepSeek shot prompt refine failed: {response.text}") from exc

    payload = response.json()
    content = _clean_text(((payload.get("choices") or [{}])[0].get("message") or {}).get("content", ""))
    if not content:
        raise ValueError("DeepSeek returned empty shot prompt")
    return content, {"model": model, "base_url": base_url}


def _build_shot_prompt(
    *,
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    media_references: list[dict[str, Any]],
    script_context: dict[str, Any],
    shot: dict[str, Any],
    shot_media: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    skeleton, constraints = _build_shot_prompt_skeleton(
        scene_block=scene_block,
        character_blocks=character_blocks,
        media_references=media_references,
        script_context=script_context,
        shot=shot,
        shot_media=shot_media,
        warnings=warnings,
    )
    fallback_prompt = _build_shot_prompt_fallback(skeleton)
    ai_refined_prompt = ""
    selected_prompt = fallback_prompt
    selected_prompt_variant = "fallback_template"
    try:
        ai_refined_prompt, meta = _call_deepseek_shot_prompt(skeleton)
        selected_prompt = ai_refined_prompt
        selected_prompt_variant = "ai_refined"
        prompt_generation = {
            "mode": "ai_refined",
            "provider": "deepseek",
            "model": meta["model"],
            "fallback_used": False,
            "error": "",
        }
    except ValueError as exc:
        prompt_generation = {
            "mode": "fallback_template",
            "provider": "deepseek",
            "model": os.getenv("DEEPSEEK_SHOT_PROMPT_MODEL", "deepseek-v4-pro").strip() or "deepseek-v4-pro",
            "fallback_used": True,
            "error": str(exc),
        }
        if str(exc) not in skeleton["warnings"]:
            skeleton["warnings"].append(str(exc))

    return {
        "positive": selected_prompt,
        "prompt_variants": {
            "ai_refined": ai_refined_prompt,
            "fallback_template": fallback_prompt,
        },
        "selected_prompt_variant": selected_prompt_variant,
        "constraints": constraints,
        "prompt_input": skeleton,
        "prompt_generation": prompt_generation,
    }


def assemble_shot_prompt_package(series_slug: str, storyboard_id: str, shot_id: str) -> dict[str, Any]:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    shot = get_shot(series_slug, storyboard_id, shot_id)
    if shot is None:
        raise FileNotFoundError(shot_id)

    episode_id = _clean_text((shot.get("script_source") or {}).get("episode_id", storyboard.get("episode_id", "")))
    scene_id = _clean_text(shot.get("scene_id", ""))
    visual = shot.get("visual") or {}
    shot_media = _normalize_shot_media(shot)
    scene_block, scene_negatives = _assemble_scene_block(series_slug, scene_id)
    character_blocks, character_negatives = _assemble_character_blocks(series_slug, shot.get("characters") or [])
    script_context = _resolve_script_context(series_slug, episode_id, scene_id, shot)
    media_references, warnings = _build_media_references(shot_media, character_blocks, scene_block)
    anchor_strategy = _normalize_shot_anchor_strategy(shot)

    prompt_bundle = _build_shot_prompt(
        scene_block=scene_block,
        character_blocks=character_blocks,
        media_references=media_references,
        script_context=script_context,
        shot=shot,
        shot_media=shot_media,
        warnings=warnings,
    )

    negative_parts = []
    for item in [*character_negatives, *scene_negatives]:
        text = _clean_text(item)
        if text and text not in negative_parts:
            negative_parts.append(text)
    negative_prompt = "; ".join(negative_parts)

    assembled = {
        "positive": prompt_bundle["positive"],
        "negative": negative_prompt,
        "reference_images": [item["path"] for item in media_references if item.get("type") == "image"],
        "media_references": media_references,
        "constraints": prompt_bundle["constraints"],
        "warnings": prompt_bundle["prompt_input"].get("warnings") or warnings,
        "script_context": script_context,
        "scene_context": scene_block,
        "character_context": character_blocks,
        "shot_media": shot_media,
        "anchor_strategy": anchor_strategy,
        "prompt_input": prompt_bundle["prompt_input"],
        "prompt_generation": prompt_bundle["prompt_generation"],
        "prompt_variants": prompt_bundle["prompt_variants"],
        "selected_prompt_variant": prompt_bundle["selected_prompt_variant"],
        "video_payload": _build_video_payload(
            prompt_text=prompt_bundle["positive"],
            negative_prompt=negative_prompt,
            media_references=media_references,
            visual=visual,
            shot_media=shot_media,
        ),
        "assembled_from": {
            "episode_id": episode_id,
            "scene_id": scene_id,
            "character_ids": shot.get("characters") or [],
            "mode": shot_media.get("mode", "reference_image"),
            "mode_label": MEDIA_MODE_TEXT.get(shot_media.get("mode", "reference_image"), shot_media.get("mode", "reference_image")),
        },
    }

    updated = save_shot(
        series_slug,
        storyboard_id,
        shot_id,
        {
            "media": shot_media,
            "anchor_strategy": anchor_strategy,
            "prompt_package": assembled,
            "dialogue": _normalize_dialogue_entries(script_context.get("dialogues") or []),
            "status": "package_ready",
        },
    )
    return updated
