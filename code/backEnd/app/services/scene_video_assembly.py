from typing import Any

from app.services.shot_assembly import (
    CAMERA_ANGLE_TEXT,
    CAMERA_MOVEMENT_TEXT,
    DEPTH_OF_FIELD_TEXT,
    MEDIA_MODE_TEXT,
    SHOT_SIZE_TEXT,
    STYLE_TEXT,
    _assemble_character_blocks,
    _assemble_scene_block,
    _build_media_references,
    _build_video_payload,
    _clean_text,
    _dedupe_text,
    _join_cn,
    _normalize_shot_media,
    _translate_visual_term,
)
from app.storage.episode_store import load_parsed_script, load_raw_script
from app.storage.scene_store import get_scene
from app.storage.storyboard_store import get_storyboard, save_storyboard


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
            else:
                character, text = "", raw_text
        if character or text:
            entries.append({"character": character, "text": text})
    return entries


def _find_scene_from_parsed_script(series_slug: str, episode_id: str, scene_id: str) -> dict[str, Any]:
    parsed = load_parsed_script(series_slug, episode_id)
    scenes = parsed.get("scenes") or []
    scene_manifest = get_scene(series_slug, scene_id) or {}
    scene_name = _clean_text(scene_manifest.get("name", "")).lower()

    matched_scene = None
    for item in scenes:
        location = _clean_text(item.get("location", "")).lower()
        summary = _clean_text(item.get("summary", "")).lower()
        if scene_name and (scene_name in location or location in scene_name or scene_name in summary):
            matched_scene = item
            break

    if matched_scene is None and len(scenes) == 1:
        matched_scene = scenes[0]

    return {
        "parsed": parsed,
        "raw_script": load_raw_script(series_slug, episode_id),
        "scene": matched_scene or {},
    }


def _camera_summary(camera: dict[str, Any]) -> str:
    parts = _dedupe_text(
        [
            _clean_text(camera.get("angle", "")) and f"机位角度：{_clean_text(camera.get('angle', ''))}",
            _clean_text(camera.get("movement", "")) and f"运镜方式：{_clean_text(camera.get('movement', ''))}",
            _clean_text(camera.get("shot_size", "")) and f"景别：{_clean_text(camera.get('shot_size', ''))}",
        ]
    )
    return "；".join(parts)


def _dialogue_excerpt(dialogues: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in dialogues:
        speaker = _clean_text(item.get("character", ""))
        text = _clean_text(item.get("text", ""))
        if speaker and text:
            parts.append(f"{speaker}: {text}")
        elif text:
            parts.append(text)
    return " / ".join(parts)


def _scene_raw_script_excerpt(raw_text: str, scene_location: str, scene_summary: str, max_lines: int = 8) -> str:
    lines = [_clean_text(line) for line in str(raw_text or "").splitlines() if _clean_text(line)]
    if not lines:
        return ""

    needles = [item for item in [scene_location, scene_summary] if _clean_text(item)]
    best_index = -1
    for index, line in enumerate(lines):
        if any(needle in line for needle in needles):
            best_index = index
            break

    if best_index < 0:
        return "\n".join(lines[:max_lines])

    start = max(0, best_index - 1)
    end = min(len(lines), best_index + max_lines)
    return "\n".join(lines[start:end])


def _resolve_scene_script_context(series_slug: str, episode_id: str, scene_id: str) -> dict[str, Any]:
    bundle = _find_scene_from_parsed_script(series_slug, episode_id, scene_id)
    parsed = bundle["parsed"]
    matched_scene = bundle["scene"] or {}
    raw_script = bundle["raw_script"]
    scene_shots = matched_scene.get("shots") or []

    shot_outlines: list[dict[str, Any]] = []
    dialogue_lines: list[str] = []
    scene_characters: list[str] = []
    beat_outline: list[str] = []

    for index, shot in enumerate(scene_shots, start=1):
      dialogues = _normalize_dialogue_entries(shot.get("dialogues") or [])
      for item in shot.get("characters") or []:
          character_name = _clean_text(item)
          if character_name and character_name not in scene_characters:
              scene_characters.append(character_name)
      dialogue_excerpt = _dialogue_excerpt(dialogues)
      if dialogue_excerpt:
          dialogue_lines.append(dialogue_excerpt)
      beat_line = _join_cn(
          _dedupe_text(
              [
                  _clean_text(shot.get("description", "")),
                  _clean_text(shot.get("emotion", "")) and f"情绪{_clean_text(shot.get('emotion', ''))}",
                  _clean_text(shot.get("beat", "")),
                  dialogue_excerpt and f"对白{dialogue_excerpt}",
              ]
          ),
          sep="，",
      )
      if beat_line:
          beat_outline.append(f"节拍{index}：{beat_line}")
      shot_outlines.append(
          {
              "index": index,
              "description": _clean_text(shot.get("description", "")),
              "emotion": _clean_text(shot.get("emotion", "")),
              "beat": _clean_text(shot.get("beat", "")),
              "dialogue_excerpt": dialogue_excerpt,
              "camera_summary": _camera_summary(shot.get("camera") or {}),
          }
      )

    scene_location = _clean_text(matched_scene.get("location", ""))
    scene_summary = _clean_text(matched_scene.get("summary", ""))
    return {
        "episode_title": _clean_text(parsed.get("title", episode_id)),
        "scene_summary": scene_summary,
        "scene_location": scene_location,
        "scene_time": _clean_text(matched_scene.get("time", "")),
        "dialogue_excerpt": " / ".join(dialogue_lines),
        "beat_outline": beat_outline,
        "shot_outlines": shot_outlines,
        "scene_characters": scene_characters,
        "raw_script_excerpt": _scene_raw_script_excerpt(raw_script, scene_location, scene_summary),
    }


def _reference_token(label: str) -> str:
    normalized = _clean_text(label)
    return f"@{normalized}" if normalized else ""


def _reference_tokens(labels: list[str]) -> str:
    return _join_cn([_reference_token(label) for label in labels if _clean_text(label)])


def _build_mode_intro(shot_media: dict[str, Any], media_references: list[dict[str, Any]]) -> list[str]:
    labels_by_role: dict[str, list[str]] = {}
    for item in media_references:
        labels_by_role.setdefault(item.get("role", ""), []).append(item.get("label", ""))

    mode = shot_media.get("mode", "reference_image")
    first_frame_labels = labels_by_role.get("first_frame", [])
    last_frame_labels = labels_by_role.get("last_frame", [])
    image_labels = labels_by_role.get("reference_image", [])
    sections: list[str] = []

    if mode == "text_only":
        sections.append("纯文字生成：仅依据场景文本与节拍描述生成整段视频。")
    elif mode == "reference_image" and image_labels:
        sections.append(f"参考生成：结合{_reference_tokens(image_labels)}中的角色与场景参考完成整段场景视频。")
    elif mode == "first_last_frame" and first_frame_labels:
        if last_frame_labels:
            sections.append(
                f"首尾帧生成：以{_reference_token(first_frame_labels[0])}作为首帧，以{_reference_token(last_frame_labels[0])}作为尾帧，生成完整场景过程。"
            )
        else:
            sections.append(f"首尾帧生成：以{_reference_token(first_frame_labels[0])}作为首帧，自然推演完整场景过程。")

    return sections


def _build_scene_direct_prompt(
    *,
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    media_references: list[dict[str, Any]],
    script_context: dict[str, Any],
    visual: dict[str, Any],
    shot_media: dict[str, Any],
    warnings: list[str],
) -> tuple[str, list[str]]:
    scene_profile = scene_block.get("visual_profile", {})
    media_labels_by_source: dict[tuple[str, str], list[str]] = {}
    for item in media_references:
        key = (item.get("source_kind", ""), item.get("source_id", ""))
        media_labels_by_source.setdefault(key, []).append(item.get("label", ""))

    prompt_sections: list[str] = []
    prompt_sections.extend(_build_mode_intro(shot_media, media_references))

    if shot_media.get("mode", "reference_image") == "reference_image":
        role_segments: list[str] = []
        for block in character_blocks:
            labels = media_labels_by_source.get(("character", block["id"]), [])
            if labels:
                role_segments.append(f"{_reference_tokens(labels)}中的角色定义为{block['name']}，保持外形、体态和身份稳定。")
        scene_labels = media_labels_by_source.get(("scene", scene_block["id"]), [])
        if scene_labels:
            role_segments.append(
                f"{_reference_tokens(scene_labels)}定义为场景{scene_block['name']}，保持空间关系、布光和环境气质一致。"
            )
        if role_segments:
            prompt_sections.append("参考绑定：" + "".join(role_segments))

    raw_script_excerpt = _clean_text(script_context.get("raw_script_excerpt", ""))
    if raw_script_excerpt:
        prompt_sections.append("剧本原文摘录：\n" + raw_script_excerpt)

    scene_summary = _clean_text(script_context.get("scene_summary") or scene_block.get("summary") or scene_block.get("description"))
    if scene_summary:
        prompt_sections.append(f"场景摘要：{scene_summary}。")

    beat_outline = script_context.get("beat_outline") or []
    if beat_outline:
        prompt_sections.append("场景节拍：\n" + "\n".join(beat_outline))

    shot_outlines = script_context.get("shot_outlines") or []
    camera_outline = [item.get("camera_summary", "") for item in shot_outlines if _clean_text(item.get("camera_summary", ""))]
    if camera_outline:
        prompt_sections.append("镜头节奏参考：" + "；".join(camera_outline) + "。")

    location_text = _clean_text(script_context.get("scene_location"))
    time_text = _clean_text(script_context.get("scene_time") or scene_profile.get("time", ""))
    weather_text = _clean_text(scene_profile.get("weather", ""))
    lighting_text = _clean_text(visual.get("lighting") or scene_profile.get("lighting", ""))
    palette_text = _clean_text(visual.get("palette") or scene_profile.get("palette", ""))
    atmosphere_text = _clean_text(scene_profile.get("atmosphere", ""))
    architecture_text = _clean_text(scene_profile.get("architecture", ""))
    key_props_text = _join_cn(scene_profile.get("key_props") or [])
    style_text = _translate_visual_term(visual.get("style", ""), STYLE_TEXT) or _clean_text(visual.get("style", ""))
    movement_text = _translate_visual_term(visual.get("camera_movement", ""), CAMERA_MOVEMENT_TEXT) or "镜头运动自然流畅"
    angle_text = _translate_visual_term(visual.get("camera_angle", ""), CAMERA_ANGLE_TEXT) or "平视"
    shot_size_text = _translate_visual_term(visual.get("shot_size", ""), SHOT_SIZE_TEXT) or "中景"
    depth_of_field_text = _translate_visual_term(visual.get("depth_of_field", ""), DEPTH_OF_FIELD_TEXT)
    lens_text = _clean_text(visual.get("lens", ""))

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
    if environment_parts:
        prompt_sections.append("场景视觉：" + "，".join(environment_parts) + "。")

    direction_parts = _dedupe_text(
        [
            f"整体镜头语言以{shot_size_text}为主",
            angle_text and f"视角以{angle_text}为主",
            movement_text,
            lens_text and f"{lens_text}镜头语言",
            depth_of_field_text,
            "请将以上节拍组织为一条完整连贯的场景视频，可自然完成镜头衔接，但角色与场景必须持续稳定",
        ]
    )
    prompt_sections.append("生成要求：" + "，".join(direction_parts) + "。")

    ratio_text = _clean_text(visual.get("aspect_ratio", ""))
    resolution_text = _clean_text(visual.get("resolution", ""))
    duration_seconds = int(visual.get("duration_seconds") or 5)
    generation_count = int(visual.get("generation_count") or 1)
    audio_text = "需要同步生成声音" if bool(shot_media.get("generate_audio")) else "无需生成声音"
    prompt_sections.append(
        "输出规格："
        + "，".join(
            _dedupe_text(
                [
                    ratio_text and f"画面比例为{ratio_text}",
                    resolution_text and f"分辨率为{resolution_text}",
                    f"时长为{duration_seconds}秒",
                    f"一次生成{generation_count}条结果",
                    audio_text,
                ]
            )
        )
        + "。"
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

    return "\n".join([section for section in prompt_sections if _clean_text(section)]), constraints


def assemble_scene_direct_package(
    series_slug: str,
    storyboard_id: str,
    scene_id: str,
    scene_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    payload = scene_payload or {}
    visual = payload.get("visual") or {}
    shot_media = _normalize_shot_media({"media": payload.get("media") or {}})
    scene_block, scene_negatives = _assemble_scene_block(series_slug, scene_id)
    character_ids = payload.get("characters") or []
    character_blocks, character_negatives = _assemble_character_blocks(series_slug, character_ids)
    episode_id = _clean_text(payload.get("episode_id") or storyboard.get("episode_id", ""))
    script_context = _resolve_scene_script_context(series_slug, episode_id, scene_id)
    media_references, warnings = _build_media_references(shot_media, character_blocks, scene_block)

    prompt_text, constraints = _build_scene_direct_prompt(
        scene_block=scene_block,
        character_blocks=character_blocks,
        media_references=media_references,
        script_context=script_context,
        visual=visual,
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
        "positive": prompt_text,
        "negative": negative_prompt,
        "reference_images": [item["path"] for item in media_references if item.get("type") == "image"],
        "media_references": media_references,
        "constraints": constraints,
        "warnings": warnings,
        "script_context": script_context,
        "scene_context": scene_block,
        "character_context": character_blocks,
        "shot_media": shot_media,
        "video_payload": _build_video_payload(
            prompt_text=prompt_text,
            negative_prompt=negative_prompt,
            media_references=media_references,
            visual=visual,
            shot_media=shot_media,
        ),
        "assembled_from": {
            "episode_id": episode_id,
            "scene_id": scene_id,
            "character_ids": character_ids,
            "mode": shot_media.get("mode", "reference_image"),
            "mode_label": MEDIA_MODE_TEXT.get(shot_media.get("mode", "reference_image"), shot_media.get("mode", "reference_image")),
            "production_mode": "scene_direct",
        },
    }

    config = {
        "episode_id": episode_id,
        "scene_id": scene_id,
        "characters": character_ids,
        "media": shot_media,
        "visual": visual,
    }
    return save_storyboard(
        series_slug,
        storyboard_id,
        {
            "scene_direct_config": config,
            "scene_direct_package": assembled,
        },
    )
