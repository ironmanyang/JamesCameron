from typing import Any

from app.storage.character_store import get_character, get_character_bible
from app.storage.episode_store import load_parsed_script
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
    "reference_image": "图片参考",
    "first_frame": "首帧图生视频",
    "first_last_frame": "首尾帧图生视频",
    "reference_video": "视频参考",
    "reference_audio": "音频参考",
    "multimodal_reference": "多模态参考",
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
    return {
        "mode": _clean_text(raw_media.get("mode", "reference_image")) or "reference_image",
        "generate_audio": bool(raw_media.get("generate_audio", False)),
        "first_frame_path": _clean_text(raw_media.get("first_frame_path", "")),
        "last_frame_path": _clean_text(raw_media.get("last_frame_path", "")),
        "reference_image_paths": _dedupe_text(_list_text(raw_media.get("reference_image_paths", []))),
        "reference_video_paths": _dedupe_text(_list_text(raw_media.get("reference_video_paths", []))),
        "reference_audio_paths": _dedupe_text(_list_text(raw_media.get("reference_audio_paths", []))),
    }


def _resolve_script_context(series_slug: str, episode_id: str, scene_id: str, shot: dict[str, Any]) -> dict[str, Any]:
    parsed = load_parsed_script(series_slug, episode_id)
    scenes = parsed.get("scenes") or []
    script_source = shot.get("script_source") or {}
    scene_index = int(script_source.get("scene_index") or 0)
    shot_index = int(script_source.get("shot_index") or 0)

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

    if matched_scene and matched_shot is None:
        candidate_shots = matched_scene.get("shots") or []
        dialogue_names = {line.get("character", "") for line in shot.get("dialogue") or []}
        selected_characters = set(shot.get("characters") or [])
        for item in candidate_shots:
            item_characters = set(item.get("characters") or [])
            if item_characters & (selected_characters | dialogue_names):
                matched_shot = item
                break
        if matched_shot is None and candidate_shots:
            matched_shot = candidate_shots[0]

    dialogues = []
    if matched_shot:
        dialogues = matched_shot.get("dialogues") or []

    return {
        "episode_title": _clean_text(parsed.get("title", episode_id)),
        "scene_summary": _clean_text((matched_scene or {}).get("summary", "")),
        "scene_location": _clean_text((matched_scene or {}).get("location", "")),
        "scene_time": _clean_text((matched_scene or {}).get("time", "")),
        "shot_description": _clean_text((matched_shot or {}).get("description", "")),
        "shot_emotion": _clean_text((matched_shot or {}).get("emotion", "")),
        "shot_beat": _clean_text((matched_shot or {}).get("beat", "")),
        "dialogues": dialogues,
    }


def _preferred_character_reference_paths(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    refs = manifest.get("reference_images") or {}
    component_images = manifest.get("component_images") or {}
    source_images = manifest.get("source_images") or []

    primary_candidates = _dedupe_text(
        [
            refs.get("sheet", ""),
            *(item.get("path", "") for item in source_images[:2]),
            component_images.get("front", ""),
        ]
    )
    all_candidates = _dedupe_text(
        [
            refs.get("sheet", ""),
            *(item.get("path", "") for item in source_images),
            component_images.get("front", ""),
            component_images.get("features", ""),
            component_images.get("side", ""),
            component_images.get("back", ""),
        ]
    )
    return primary_candidates[:2], all_candidates


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
                "summary": bible.get("summary", ""),
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


def _build_media_references(
    shot_media: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    scene_block: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    references: list[dict[str, Any]] = []
    warnings: list[str] = []

    _append_reference(
        references,
        type="image",
        path=shot_media.get("first_frame_path", ""),
        role="first_frame",
        source_kind="shot",
        source_name="首帧",
        source_detail="首帧",
    )
    _append_reference(
        references,
        type="image",
        path=shot_media.get("last_frame_path", ""),
        role="last_frame",
        source_kind="shot",
        source_name="尾帧",
        source_detail="尾帧",
    )

    for path in shot_media.get("reference_image_paths", []):
        _append_reference(
            references,
            type="image",
            path=path,
            role="reference_image",
            source_kind="shot",
            source_name="补充图片参考",
            source_detail="补充图片参考",
        )

    for path in shot_media.get("reference_video_paths", []):
        _append_reference(
            references,
            type="video",
            path=path,
            role="reference_video",
            source_kind="shot",
            source_name="视频参考",
            source_detail="视频参考",
        )

    for path in shot_media.get("reference_audio_paths", []):
        _append_reference(
            references,
            type="audio",
            path=path,
            role="reference_audio",
            source_kind="shot",
            source_name="音频参考",
            source_detail="音频参考",
        )

    image_count_before_fallback = len([item for item in references if item["type"] == "image"])
    if image_count_before_fallback < 9 and shot_media.get("mode") in {
        "reference_image",
        "reference_video",
        "reference_audio",
        "multimodal_reference",
    }:
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
                    source_detail="角色参考",
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
                source_detail="场景参考",
            )

    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for item in references:
        dedupe_key = (item["type"], item["role"], item["path"])
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped.append(item)

    type_limits = {"image": 9, "video": 3, "audio": 3}
    type_counts = {"image": 0, "video": 0, "audio": 0}
    limited: list[dict[str, Any]] = []
    for item in deduped:
        item_type = item["type"]
        type_counts[item_type] += 1
        if type_counts[item_type] > type_limits[item_type]:
            continue
        limited.append(item)

    if type_counts["image"] > type_limits["image"]:
        warnings.append("参考图片超过 Seedance 2.0 上限，已截断为前 9 张。")
    if type_counts["video"] > type_limits["video"]:
        warnings.append("参考视频超过 Seedance 2.0 上限，已截断为前 3 段。")
    if type_counts["audio"] > type_limits["audio"]:
        warnings.append("参考音频超过 Seedance 2.0 上限，已截断为前 3 段。")

    label_counts = {"image": 0, "video": 0, "audio": 0}
    label_prefix = {"image": "图片", "video": "视频", "audio": "音频"}
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
    for item in media_references:
        labels_by_role.setdefault(item.get("role", ""), []).append(item.get("label", ""))

    intro_sections: list[str] = []
    mode = shot_media.get("mode", "reference_image")
    first_frame_labels = labels_by_role.get("first_frame", [])
    last_frame_labels = labels_by_role.get("last_frame", [])
    image_labels = labels_by_role.get("reference_image", [])
    video_labels = labels_by_role.get("reference_video", [])
    audio_labels = labels_by_role.get("reference_audio", [])

    if mode == "first_frame" and first_frame_labels:
        intro_sections.append(f"输入设定：以{first_frame_labels[0]}为首帧，保持首帧主体与构图稳定。")
    elif mode == "first_last_frame" and first_frame_labels and last_frame_labels:
        intro_sections.append(
            f"输入设定：以{first_frame_labels[0]}为首帧，以{last_frame_labels[0]}为尾帧，生成二者之间自然连贯的过渡。"
        )
    elif mode == "reference_video" and video_labels:
        intro_sections.append(f"视频参考：参考{_join_cn(video_labels)}中的动作、运镜或节奏。")
    elif mode == "reference_audio" and audio_labels:
        intro_sections.append(f"音频参考：参考{_join_cn(audio_labels)}中的音色、节奏或环境声。")
    elif mode == "multimodal_reference":
        parts: list[str] = []
        if image_labels:
            parts.append(f"图片参考{_join_cn(image_labels)}")
        if video_labels:
            parts.append(f"视频参考{_join_cn(video_labels)}")
        if audio_labels:
            parts.append(f"音频参考{_join_cn(audio_labels)}")
        if parts:
            intro_sections.append("多模态参考：" + "，".join(parts) + "。")
    elif mode == "reference_image" and image_labels:
        intro_sections.append(f"图片参考：参考{_join_cn(image_labels)}中的主体、场景或构图细节。")

    if video_labels and mode != "reference_video":
        intro_sections.append(f"补充视频参考：参考{_join_cn(video_labels)}中的动作、运镜或节奏。")
    if audio_labels and mode != "reference_audio":
        intro_sections.append(f"补充音频参考：参考{_join_cn(audio_labels)}中的音色、节奏或环境声。")

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
    media_labels_by_source: dict[tuple[str, str], list[str]] = {}
    for item in media_references:
        key = (item.get("source_kind", ""), item.get("source_id", ""))
        media_labels_by_source.setdefault(key, []).append(item.get("label", ""))

    prompt_sections: list[str] = []
    mode_intro = _build_mode_prompt_intro(shot_media, media_references)
    if mode_intro:
        prompt_sections.extend(mode_intro)

    subject_lines: list[str] = []
    for block in character_blocks:
        labels = media_labels_by_source.get(("character", block["id"]), [])
        if not labels:
            continue
        feature_text = _compose_subject_features(block) or block["name"]
        label_text = _join_cn(labels)
        if len(labels) == 1:
            subject_lines.append(f"将{label_text}中的{feature_text}定义为{block['name']}。")
        else:
            subject_lines.append(f"将{label_text}中的同一角色定义为{block['name']}，保持面部、发型、服装特征一致。")
    if subject_lines:
        prompt_sections.append("主体定义：" + "".join(subject_lines))

    scene_labels = media_labels_by_source.get(("scene", scene_block["id"]), [])
    scene_summary = _clean_text(script_context.get("scene_summary") or scene_block.get("summary") or scene_block.get("description"))
    if scene_labels:
        prompt_sections.append(
            "场景参考："
            f"场景环境与氛围参考{_join_cn(scene_labels)}，保持"
            f"{scene_summary or scene_block['name']}的空间关系、环境气质与布光基调。"
        )

    shot_description = _clean_text(script_context.get("shot_description"))
    shot_emotion = _clean_text(script_context.get("shot_emotion"))
    shot_beat = _clean_text(script_context.get("shot_beat"))
    dialogue_text = _describe_dialogue(script_context.get("dialogues") or [])
    audio_reference_labels = [item["label"] for item in media_references if item.get("type") == "audio"]

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

    action_parts = _dedupe_text(
        [
            shot_description,
            shot_beat,
            shot_emotion and f"情绪基调是{shot_emotion}",
            dialogue_text,
            audio_reference_labels and dialogue_text and f"角色说话时音色参考{_join_cn(audio_reference_labels)}",
        ]
    )
    if not action_parts:
        action_parts = ["角色在当前场景中完成本镜头动作，动作自然连贯。"]

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

    prompt_sections.append(
        "镜头1："
        + "，".join(action_parts)
        + "。"
        + ("，".join(environment_parts) + "。" if environment_parts else "")
        + ("运镜使用" + "，".join(camera_parts) + "。" if camera_parts else "")
    )

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
    has_dialogue: bool,
) -> dict[str, Any]:
    reference_images = [item["path"] for item in media_references if item.get("type") == "image"]
    reference_videos = [item["path"] for item in media_references if item.get("type") == "video"]
    reference_audios = [item["path"] for item in media_references if item.get("type") == "audio"]
    has_audio_ref = bool(reference_audios)

    return {
        "provider": "doubao-seedance-2-0",
        "prompt": prompt_text,
        "negative_prompt": negative_prompt,
        "reference_images": reference_images,
        "reference_videos": reference_videos,
        "reference_audios": reference_audios,
        "media_references": media_references,
        "ratio": visual.get("aspect_ratio", ""),
        "aspect_ratio": visual.get("aspect_ratio", ""),
        "resolution": visual.get("resolution", ""),
        "duration": visual.get("duration_seconds", 5),
        "duration_seconds": visual.get("duration_seconds", 5),
        "generate_audio": bool(shot_media.get("generate_audio")) or has_dialogue or has_audio_ref,
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
        "reference_videos": [item["path"] for item in media_references if item.get("type") == "video"],
        "reference_audios": [item["path"] for item in media_references if item.get("type") == "audio"],
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
            has_dialogue=bool(script_context.get("dialogues")),
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
            "dialogue": [
                f"{_clean_text(item.get('character', ''))}: {_clean_text(item.get('text', ''))}"
                for item in script_context.get("dialogues", [])
                if _clean_text(item.get("character")) or _clean_text(item.get("text"))
            ],
            "status": "package_ready",
        },
    )
    return updated
