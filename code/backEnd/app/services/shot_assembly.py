from typing import Any

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
        "generate_audio": bool(raw_media.get("generate_audio", False)),
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


def _compose_subject_features(block: dict[str, Any]) -> str:
    anchors = block.get("anchors", {})
    features = _dedupe_text(
        [
            anchors.get("face", ""),
            anchors.get("hair", ""),
            anchors.get("costume", ""),
            anchors.get("biology", ""),
            block.get("summary", ""),
        ],
        limit=3,
    )
    return _join_cn(features)


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
        for block in character_blocks:
            labels = media_labels_by_source.get(("character", block["id"]), [])
            if not labels:
                continue
            feature_text = _compose_subject_features(block)
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

    seedance_prompt, seedance_constraints = _build_seedance_prompt(
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
        "positive": seedance_prompt,
        "negative": negative_prompt,
        "reference_images": [item["path"] for item in media_references if item.get("type") == "image"],
        "media_references": media_references,
        "constraints": seedance_constraints,
        "warnings": warnings,
        "script_context": script_context,
        "scene_context": scene_block,
        "character_context": character_blocks,
        "shot_media": shot_media,
        "video_payload": _build_video_payload(
            prompt_text=seedance_prompt,
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
            "prompt_package": assembled,
            "dialogue": _normalize_dialogue_entries(script_context.get("dialogues") or []),
            "status": "package_ready",
        },
    )
    return updated
