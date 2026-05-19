from typing import Any

from app.storage.character_store import get_character, get_character_bible
from app.storage.episode_store import load_parsed_script
from app.storage.scene_store import get_scene, get_scene_prompt_package
from app.storage.storyboard_store import get_shot, get_storyboard, save_shot


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _list_text(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


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


def _assemble_character_blocks(series_slug: str, character_ids: list[str]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    blocks: list[dict[str, Any]] = []
    negatives: list[str] = []
    reference_images: list[str] = []

    for character_id in character_ids:
        manifest = get_character(series_slug, character_id)
        if manifest is None:
            continue
        bible = get_character_bible(series_slug, character_id)
        refs = manifest.get("reference_images") or {}
        ref_paths = [path for path in refs.values() if path]
        source_paths = [item.get("path", "") for item in manifest.get("source_images") or [] if item.get("path")]
        for path in source_paths:
            if path not in ref_paths:
                ref_paths.append(path)
        reference_images.extend(ref_paths)

        blocks.append(
            {
                "id": character_id,
                "name": manifest.get("name", character_id),
                "summary": bible.get("summary", ""),
                "anchors": manifest.get("anchors", {}),
                "continuity_rules": ((bible.get("bible") or {}).get("continuity_rules") or []),
                "reference_images": ref_paths,
            }
        )
        if bible.get("negative_prompt"):
            negatives.append(str(bible["negative_prompt"]).strip())

    return blocks, negatives, reference_images


def _assemble_scene_block(series_slug: str, scene_id: str) -> tuple[dict[str, Any], list[str], list[str]]:
    manifest = get_scene(series_slug, scene_id)
    if manifest is None:
        raise FileNotFoundError(scene_id)

    prompt_package = get_scene_prompt_package(series_slug, scene_id)
    refs = manifest.get("reference_images") or {}
    ref_paths = [path for path in refs.values() if path]
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
        "reference_images": ref_paths,
    }
    return block, negatives, ref_paths


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
    scene_block, scene_negatives, scene_refs = _assemble_scene_block(series_slug, scene_id)
    character_blocks, character_negatives, character_refs = _assemble_character_blocks(series_slug, shot.get("characters") or [])
    script_context = _resolve_script_context(series_slug, episode_id, scene_id, shot)

    reference_images = []
    for path in [*character_refs, *scene_refs]:
        if path and path not in reference_images:
            reference_images.append(path)

    dialogue_lines = [
        f"{_clean_text(item.get('character', ''))}: {_clean_text(item.get('text', ''))}"
        for item in script_context.get("dialogues", [])
        if _clean_text(item.get("character")) or _clean_text(item.get("text"))
    ]

    character_prompt_lines = []
    for block in character_blocks:
        anchors = block.get("anchors", {})
        continuity = ", ".join(_list_text(block.get("continuity_rules")))
        character_prompt_lines.append(
            (
                f"{block['name']}: {block.get('summary', '')}; "
                f"biology {anchors.get('biology', '')}; face {anchors.get('face', '')}; "
                f"hair {anchors.get('hair', '')}; costume {anchors.get('costume', '')}; "
                f"palette {anchors.get('palette', '')}; aura {anchors.get('aura', '')}; "
                f"continuity {continuity}"
            ).strip()
        )

    scene_profile = scene_block.get("visual_profile", {})
    positive_lines = [
        f"Episode: {script_context.get('episode_title', episode_id)}",
        f"Scene: {scene_block.get('name', scene_id)}",
        f"Scene summary: {script_context.get('scene_summary') or scene_block.get('summary', '')}",
        f"Shot description: {script_context.get('shot_description', '')}",
        f"Emotion: {script_context.get('shot_emotion', '')}",
        f"Beat: {script_context.get('shot_beat', '')}",
        (
            f"Location {script_context.get('scene_location', '')}; time {script_context.get('scene_time', '')}; "
            f"weather {scene_profile.get('weather', '')}; lighting {visual.get('lighting') or scene_profile.get('lighting', '')}; "
            f"palette {visual.get('palette') or scene_profile.get('palette', '')}; style {visual.get('style', '')}; "
            f"architecture {scene_profile.get('architecture', '')}; atmosphere {scene_profile.get('atmosphere', '')}"
        ),
        (
            f"Shot config: aspect ratio {visual.get('aspect_ratio', '')}; resolution {visual.get('resolution', '')}; "
            f"shot size {visual.get('shot_size', '')}; camera angle {visual.get('camera_angle', '')}; "
            f"camera movement {visual.get('camera_movement', '')}; lens {visual.get('lens', '')}; "
            f"depth of field {visual.get('depth_of_field', '')}; duration {visual.get('duration_seconds', '')} seconds"
        ),
    ]

    if character_prompt_lines:
        positive_lines.append("Characters: " + " | ".join(character_prompt_lines))
    if dialogue_lines:
        positive_lines.append("Dialogue: " + " | ".join(dialogue_lines))

    key_props = _list_text(scene_profile.get("key_props"))
    if key_props:
        positive_lines.append("Key props: " + ", ".join(key_props))

    positive_prompt = "\n".join(line for line in positive_lines if _clean_text(line))

    negative_parts = []
    for item in [*character_negatives, *scene_negatives]:
        text = _clean_text(item)
        if text and text not in negative_parts:
            negative_parts.append(text)
    default_negative = "low detail, blurry face, inconsistent costume, extra limbs, duplicate people, distorted anatomy, text watermark"
    if default_negative not in negative_parts:
        negative_parts.append(default_negative)
    negative_prompt = "; ".join(negative_parts)

    assembled = {
        "positive": positive_prompt,
        "negative": negative_prompt,
        "reference_images": reference_images,
        "script_context": script_context,
        "scene_context": scene_block,
        "character_context": character_blocks,
        "video_payload": {
            "prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "reference_images": reference_images,
            "aspect_ratio": visual.get("aspect_ratio", ""),
            "resolution": visual.get("resolution", ""),
            "duration_seconds": visual.get("duration_seconds", 5),
        },
        "assembled_from": {
            "episode_id": episode_id,
            "scene_id": scene_id,
            "character_ids": shot.get("characters") or [],
        },
    }

    updated = save_shot(
        series_slug,
        storyboard_id,
        shot_id,
        {
            "prompt_package": assembled,
            "dialogue": dialogue_lines,
            "status": "package_ready",
        },
    )
    return updated
