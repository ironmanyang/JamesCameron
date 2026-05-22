import os
from typing import Any

import requests

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
            elif "：" in raw_text:
                character, text = [part.strip() for part in raw_text.split("：", 1)]
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

        camera = shot.get("camera") or {}
        shot_outlines.append(
            {
                "index": index,
                "description": _clean_text(shot.get("description", "")),
                "emotion": _clean_text(shot.get("emotion", "")),
                "beat": _clean_text(shot.get("beat", "")),
                "dialogue_excerpt": dialogue_excerpt,
                "camera_angle": _clean_text(camera.get("angle", "")),
                "camera_movement": _clean_text(camera.get("movement", "")),
                "camera_shot_size": _clean_text(camera.get("shot_size", "")),
                "camera_summary": _camera_summary(camera),
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
    labels_by_source_kind: dict[str, list[str]] = {}
    for item in media_references:
        labels_by_role.setdefault(item.get("role", ""), []).append(item.get("label", ""))
        labels_by_source_kind.setdefault(item.get("source_kind", ""), []).append(item.get("label", ""))

    mode = shot_media.get("mode", "reference_image")
    first_frame_labels = labels_by_role.get("first_frame", [])
    last_frame_labels = labels_by_role.get("last_frame", [])
    character_labels = labels_by_source_kind.get("character", [])
    scene_labels = labels_by_source_kind.get("scene", [])
    sections: list[str] = []

    if mode == "text_only":
        sections.append("纯文字生成：仅依据场景剧情与镜头节拍生成整段视频。")
    elif mode == "reference_image":
        if character_labels and scene_labels:
            sections.append("参考生成：结合角色参考与场景参考完成整段场景视频，保持人物身份与环境关系稳定一致。")
        elif character_labels:
            sections.append("参考生成：结合角色参考完成整段场景视频，场景环境按文字描述构建。")
        elif scene_labels:
            sections.append("参考生成：结合场景参考完成整段场景视频，人物表演按文字描述生成。")
    elif mode == "first_last_frame" and first_frame_labels:
        if last_frame_labels:
            sections.append(
                f"首尾帧生成：以{_reference_token(first_frame_labels[0])}作为首帧，以{_reference_token(last_frame_labels[0])}作为尾帧，生成完整场景过程。"
            )
        else:
            sections.append(f"首尾帧生成：以{_reference_token(first_frame_labels[0])}作为首帧，自然推演完整场景过程。")

    return sections


def _scene_character_text(script_context: dict[str, Any], character_blocks: list[dict[str, Any]]) -> str:
    names = _dedupe_text(
        [block.get("name", "") for block in character_blocks] + list(script_context.get("scene_characters") or [])
    )
    return _join_cn(names)


def _scene_dialogue_highlights(shot_outlines: list[dict[str, Any]], limit: int = 2) -> str:
    lines = _dedupe_text([item.get("dialogue_excerpt", "") for item in shot_outlines], limit=limit)
    return "；".join(lines)


def _target_scene_beat_count(duration_seconds: int, total_shots: int) -> int:
    if total_shots <= 0:
        return 0
    if duration_seconds <= 5:
        return min(total_shots, 3)
    if duration_seconds <= 8:
        return min(total_shots, 4)
    return min(total_shots, 5)


def _chunk_scene_outlines(shot_outlines: list[dict[str, Any]], chunk_count: int) -> list[list[dict[str, Any]]]:
    if not shot_outlines or chunk_count <= 0:
        return []

    total = len(shot_outlines)
    chunks: list[list[dict[str, Any]]] = []
    start = 0
    for chunk_index in range(chunk_count):
        end = round((chunk_index + 1) * total / chunk_count)
        chunk = shot_outlines[start:end]
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks


def _summarize_scene_beat_chunk(chunk: list[dict[str, Any]], index: int) -> str:
    descriptions = _dedupe_text([item.get("description", "") for item in chunk], limit=2)
    beats = _dedupe_text([item.get("beat", "") for item in chunk], limit=2)
    emotions = _dedupe_text([item.get("emotion", "") for item in chunk], limit=2)
    dialogues = _dedupe_text([item.get("dialogue_excerpt", "") for item in chunk], limit=2)

    action_text = "，随后".join(descriptions) if len(descriptions) > 1 else (descriptions[0] if descriptions else "")
    parts = _dedupe_text(
        [
            action_text,
            beats and f"推进{_join_cn(beats, sep='、')}",
            emotions and f"情绪保持{_join_cn(emotions, sep='、')}",
            dialogues and f"对白可包含{'；'.join(dialogues)}",
        ]
    )
    return f"阶段{index}：" + "，".join(parts)


def _condense_scene_beats(shot_outlines: list[dict[str, Any]], duration_seconds: int) -> tuple[list[str], str]:
    if not shot_outlines:
        return [], ""

    chunk_count = _target_scene_beat_count(duration_seconds, len(shot_outlines))
    if len(shot_outlines) <= chunk_count:
        return (
            [
                _summarize_scene_beat_chunk([item], index)
                for index, item in enumerate(shot_outlines, start=1)
                if _clean_text(item.get("description", ""))
                or _clean_text(item.get("beat", ""))
                or _clean_text(item.get("dialogue_excerpt", ""))
            ],
            "",
        )

    chunks = _chunk_scene_outlines(shot_outlines, chunk_count)
    return (
        [_summarize_scene_beat_chunk(chunk, index) for index, chunk in enumerate(chunks, start=1) if chunk],
        f"当前场景原始包含{len(shot_outlines)}个分镜节拍，已按{duration_seconds}秒时长压缩为{len(chunks)}段生成指令。",
    )


def _build_scene_goal(
    script_context: dict[str, Any],
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    shot_outlines: list[dict[str, Any]],
) -> str:
    scene_summary = _clean_text(script_context.get("scene_summary") or scene_block.get("summary") or scene_block.get("description"))
    character_text = _scene_character_text(script_context, character_blocks)
    dialogue_highlights = _scene_dialogue_highlights(shot_outlines)
    goal_parts = _dedupe_text(
        [
            scene_summary and f"围绕{scene_summary}展开",
            character_text and f"主要角色为{character_text}",
            dialogue_highlights and f"关键对白为{dialogue_highlights}",
        ]
    )
    return "。".join(goal_parts) + ("。" if goal_parts else "")


def _build_reference_binding_text(
    media_references: list[dict[str, Any]],
    media_labels_by_source: dict[tuple[str, str], list[str]],
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
) -> str:
    role_segments: list[str] = []
    for block in character_blocks:
        labels = media_labels_by_source.get(("character", block["id"]), [])
        if labels:
            role_segments.append(
                f"{_reference_tokens(labels)}中的角色定义为{block['name']}，保持角色身份、外形和体态稳定。"
            )

    scene_labels = media_labels_by_source.get(("scene", scene_block["id"]), [])
    if scene_labels:
        role_segments.append(
            f"{_reference_tokens(scene_labels)}定义为场景{scene_block['name']}，保持空间关系、布光和环境气质一致。"
        )

    if not role_segments:
        image_labels = [_clean_text(item.get("label", "")) for item in media_references if item.get("type") == "image"]
        if image_labels:
            role_segments.append(f"参考图{_reference_tokens(image_labels)}用于统一角色与场景连续性。")

    return "".join(role_segments)


def _build_scene_visual_text(script_context: dict[str, Any], scene_profile: dict[str, Any], visual: dict[str, Any]) -> str:
    location_text = _clean_text(script_context.get("scene_location"))
    time_text = _clean_text(script_context.get("scene_time") or scene_profile.get("time", ""))
    weather_text = _clean_text(scene_profile.get("weather", ""))
    lighting_text = _clean_text(visual.get("lighting") or scene_profile.get("lighting", ""))
    palette_text = _clean_text(visual.get("palette") or scene_profile.get("palette", ""))
    atmosphere_text = _clean_text(scene_profile.get("atmosphere", ""))
    architecture_text = _clean_text(scene_profile.get("architecture", ""))
    key_props_text = _join_cn(scene_profile.get("key_props") or [])
    style_text = _translate_visual_term(visual.get("style", ""), STYLE_TEXT) or _clean_text(visual.get("style", ""))

    parts = _dedupe_text(
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
    return "，".join(parts) + ("。" if parts else "")


def _build_scene_camera_direction(*, visual: dict[str, Any], shot_outlines: list[dict[str, Any]]) -> str:
    movement_text = _translate_visual_term(visual.get("camera_movement", ""), CAMERA_MOVEMENT_TEXT) or "镜头运动自然流畅"
    angle_text = _translate_visual_term(visual.get("camera_angle", ""), CAMERA_ANGLE_TEXT) or "平视"
    shot_size_text = _translate_visual_term(visual.get("shot_size", ""), SHOT_SIZE_TEXT) or "中景"
    depth_of_field_text = _translate_visual_term(visual.get("depth_of_field", ""), DEPTH_OF_FIELD_TEXT)
    lens_text = _clean_text(visual.get("lens", ""))

    opening = shot_outlines[0] if shot_outlines else {}
    ending = shot_outlines[-1] if shot_outlines else {}

    opening_hint = _dedupe_text(
        [
            opening.get("camera_shot_size", "") and f"开场可从{opening.get('camera_shot_size', '')}切入",
            opening.get("camera_angle", "") and f"以{opening.get('camera_angle', '')}视角建立人物与空间关系",
        ],
        limit=2,
    )
    ending_hint = _dedupe_text(
        [
            ending.get("camera_movement", "") and f"结尾可自然过渡到{ending.get('camera_movement', '')}",
            ending.get("camera_shot_size", "") and f"并收束到{ending.get('camera_shot_size', '')}",
        ],
        limit=2,
    )

    parts = _dedupe_text(
        [
            f"整体镜头语言以{shot_size_text}为主",
            f"整体视角以{angle_text}为主",
            movement_text,
            lens_text and f"{lens_text}镜头语言",
            depth_of_field_text,
            opening_hint and "，".join(opening_hint),
            ending_hint and "，".join(ending_hint),
            "镜头衔接允许自然切换，但角色身份、场景关系和情绪推进必须保持连贯稳定",
        ]
    )
    return "，".join(parts) + ("。" if parts else "")


def _build_scene_output_spec(visual: dict[str, Any], shot_media: dict[str, Any]) -> str:
    ratio_text = _clean_text(visual.get("aspect_ratio", ""))
    resolution_text = _clean_text(visual.get("resolution", ""))
    duration_seconds = int(visual.get("duration_seconds") or 5)
    generation_count = int(visual.get("generation_count") or 1)
    audio_text = "需要同步生成声音" if bool(shot_media.get("generate_audio")) else "无需生成声音"
    parts = _dedupe_text(
        [
            ratio_text and f"画面比例为{ratio_text}",
            resolution_text and f"分辨率为{resolution_text}",
            f"时长为{duration_seconds}秒",
            f"一次生成{generation_count}条结果",
            audio_text,
        ]
    )
    return "，".join(parts) + ("。" if parts else "")


def _build_scene_constraints() -> list[str]:
    return _dedupe_text(
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


def _build_scene_prompt_skeleton(
    *,
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    media_references: list[dict[str, Any]],
    script_context: dict[str, Any],
    visual: dict[str, Any],
    shot_media: dict[str, Any],
    warnings: list[str],
) -> tuple[dict[str, Any], list[str]]:
    scene_profile = scene_block.get("visual_profile", {})
    media_labels_by_source: dict[tuple[str, str], list[str]] = {}
    for item in media_references:
        key = (item.get("source_kind", ""), item.get("source_id", ""))
        media_labels_by_source.setdefault(key, []).append(item.get("label", ""))

    duration_seconds = int(visual.get("duration_seconds") or 5)
    shot_outlines = script_context.get("shot_outlines") or []
    condensed_beats, condensation_note = _condense_scene_beats(shot_outlines, duration_seconds)

    skeleton = {
        "mode_intro": _build_mode_intro(shot_media, media_references),
        "reference_binding": _build_reference_binding_text(
            media_references=media_references,
            media_labels_by_source=media_labels_by_source,
            scene_block=scene_block,
            character_blocks=character_blocks,
        ),
        "scene_goal": _build_scene_goal(
            script_context=script_context,
            scene_block=scene_block,
            character_blocks=character_blocks,
            shot_outlines=shot_outlines,
        ),
        "condensed_beats": condensed_beats,
        "scene_visual": _build_scene_visual_text(script_context, scene_profile, visual),
        "camera_direction": _build_scene_camera_direction(visual=visual, shot_outlines=shot_outlines),
        "output_spec": _build_scene_output_spec(visual, shot_media),
        "constraints": _build_scene_constraints(),
        "warnings": list(warnings),
        "raw_script_excerpt": _clean_text(script_context.get("raw_script_excerpt", "")),
        "shot_outlines": shot_outlines,
        "condensation_note": condensation_note,
        "duration_seconds": duration_seconds,
        "mode": shot_media.get("mode", "reference_image"),
        "character_names": [block.get("name", "") for block in character_blocks if _clean_text(block.get("name", ""))],
        "scene_name": scene_block.get("name", ""),
    }
    if condensation_note:
        skeleton["warnings"].append(condensation_note)
    return skeleton, skeleton["constraints"]


def _build_scene_direct_prompt_fallback(skeleton: dict[str, Any]) -> str:
    sections: list[str] = []
    sections.extend(skeleton.get("mode_intro") or [])

    if _clean_text(skeleton.get("reference_binding", "")):
        sections.append("参考绑定：" + _clean_text(skeleton["reference_binding"]))
    if _clean_text(skeleton.get("scene_goal", "")):
        sections.append("场景目标：" + _clean_text(skeleton["scene_goal"]))
    if skeleton.get("condensed_beats"):
        sections.append("剧情阶段：\n" + "\n".join(skeleton["condensed_beats"]))
    if _clean_text(skeleton.get("scene_visual", "")):
        sections.append("场景视觉：" + _clean_text(skeleton["scene_visual"]))
    if _clean_text(skeleton.get("camera_direction", "")):
        sections.append("镜头原则：" + _clean_text(skeleton["camera_direction"]))
    if _clean_text(skeleton.get("output_spec", "")):
        sections.append("输出规格：" + _clean_text(skeleton["output_spec"]))
    if skeleton.get("constraints"):
        sections.append("画质与约束：" + "，".join(skeleton["constraints"]) + "。")
    if skeleton.get("warnings"):
        sections.append("备注：" + "；".join([_clean_text(item) for item in skeleton["warnings"] if _clean_text(item)]) + "。")
    return "\n".join([section for section in sections if _clean_text(section)])


SCENE_DIRECT_SYSTEM_PROMPT = """
你是视频生成提示词导演。你的任务是把结构化的场景信息改写成一段可以直接提交给 Seedance 2.0 的中文提示词。

要求：
1. 只输出最终提示词，不要解释，不要 Markdown，不要代码块。
2. 必须严格使用输入里已有的信息，不要编造新的角色、场景、动作、对白、运镜、时长、规格。
3. 必须保留所有 @图像N 形式的参考绑定，不要改编号，不要漏掉。
4. 这是“整段场景视频”提示词，不是单镜头提示词。请把多个节拍压成连贯的阶段推进。
5. 如果时长较短，应主动压缩节拍，避免把过多分镜逐条平铺。
6. 不要把“原始剧本格式”直接照抄进最终提示词，不要输出括号舞台说明。
7. 语言要自然、专业、可执行，像导演给视频模型的生产指令。
8. 输出应包含：参考绑定、场景目标、剧情推进、视觉统一、镜头原则、输出规格、画质约束。
""".strip()


def _call_deepseek_scene_prompt(skeleton: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("缺少 DEEPSEEK_API_KEY 配置")

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://www.packyapi.com/v1").rstrip("/")
    model = os.getenv("DEEPSEEK_SCENE_DIRECT_MODEL", "deepseek-v4-pro").strip() or "deepseek-v4-pro"

    user_content = (
        "请根据以下结构化输入，生成最终的场景直出提示词。\n\n"
        f"模式说明：{chr(10).join(skeleton.get('mode_intro') or [])}\n"
        f"参考绑定：{skeleton.get('reference_binding', '')}\n"
        f"场景目标：{skeleton.get('scene_goal', '')}\n"
        "剧情阶段：\n"
        + ("\n".join(skeleton.get("condensed_beats") or []) or "无")
        + "\n"
        f"场景视觉：{skeleton.get('scene_visual', '')}\n"
        f"镜头原则：{skeleton.get('camera_direction', '')}\n"
        f"输出规格：{skeleton.get('output_spec', '')}\n"
        f"画质与约束：{'，'.join(skeleton.get('constraints') or [])}\n"
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
                "temperature": 0.3,
                "max_tokens": 1800,
                "messages": [
                    {"role": "system", "content": SCENE_DIRECT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            },
            timeout=180,
        )
    except requests.RequestException as exc:
        raise ValueError(f"DeepSeek 场景直出提示词润色请求失败：{exc}") from exc
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"DeepSeek 场景直出提示词生成失败：{response.text}") from exc

    payload = response.json()
    content = _clean_text(((payload.get("choices") or [{}])[0].get("message") or {}).get("content", ""))
    if not content:
        raise ValueError("DeepSeek 返回的场景直出提示词为空")
    return content, {"model": model, "base_url": base_url}


def _build_scene_direct_prompt(
    *,
    scene_block: dict[str, Any],
    character_blocks: list[dict[str, Any]],
    media_references: list[dict[str, Any]],
    script_context: dict[str, Any],
    visual: dict[str, Any],
    shot_media: dict[str, Any],
    warnings: list[str],
) -> tuple[str, list[str], dict[str, Any], dict[str, Any]]:
    skeleton, constraints = _build_scene_prompt_skeleton(
        scene_block=scene_block,
        character_blocks=character_blocks,
        media_references=media_references,
        script_context=script_context,
        visual=visual,
        shot_media=shot_media,
        warnings=warnings,
    )

    try:
        prompt_text, meta = _call_deepseek_scene_prompt(skeleton)
        generation_meta = {
            "mode": "ai_refined",
            "provider": "deepseek",
            "model": meta["model"],
            "fallback_used": False,
            "error": "",
        }
    except ValueError as exc:
        prompt_text = _build_scene_direct_prompt_fallback(skeleton)
        generation_meta = {
            "mode": "fallback_template",
            "provider": "deepseek",
            "model": os.getenv("DEEPSEEK_SCENE_DIRECT_MODEL", "deepseek-v4-pro").strip() or "deepseek-v4-pro",
            "fallback_used": True,
            "error": str(exc),
        }
        if str(exc) not in skeleton["warnings"]:
            skeleton["warnings"].append(str(exc))

    return prompt_text, constraints, skeleton, generation_meta


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

    prompt_text, constraints, prompt_input, prompt_generation = _build_scene_direct_prompt(
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
        "warnings": prompt_input.get("warnings") or warnings,
        "script_context": script_context,
        "scene_context": scene_block,
        "character_context": character_blocks,
        "shot_media": shot_media,
        "prompt_input": prompt_input,
        "prompt_generation": prompt_generation,
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
