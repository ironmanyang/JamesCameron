from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.file_ops import get_series_dir, load_json


def build_shot_prompt(
    shot_data: Dict[str, Any],
    character_bibles: Dict[str, Dict[str, Any]],
    scene_data: Dict[str, Any],
    director_config: Dict[str, Any]
) -> str:
    shot_desc = shot_data.get("description", "")
    characters = shot_data.get("characters", [])
    location = shot_data.get("location", "")

    character_parts = []
    for char_name in characters:
        if char_name in character_bibles:
            bible = character_bibles[char_name].get("bible", {})
            layer1 = bible.get("layer_1_biology", "")
            layer2 = bible.get("layer_2_face", "")
            layer3 = bible.get("layer_3_costume", "")
            layer6 = bible.get("layer_6_aura", "")
            character_parts.append(f"{char_name}: {layer1}, {layer2}, {layer3}, 气质: {layer6}")

    scene_location = scene_data.get("location", "")
    scene_time = scene_data.get("time", "")

    style = director_config.get("style", "写实")
    shot_size = director_config.get("shot_size", "中景")
    lighting = director_config.get("lighting", "自然光")
    color_tone = director_config.get("color_tone", "暖色")

    prompt_parts = [
        f"Scene: {location} {scene_time}",
        f"Action: {shot_desc}",
        f"Style: {style}",
        f"Shot: {shot_size}",
        f"Lighting: {lighting}",
        f"Color: {color_tone}"
    ]

    if character_parts:
        prompt_parts.append(f"Characters: {'; '.join(character_parts)}")

    return ", ".join(prompt_parts)


def get_character_for_shot(shot_data: Dict[str, Any], character_dir: Path) -> Dict[str, Dict[str, Any]]:
    characters = shot_data.get("characters", [])
    result = {}

    if not character_dir.exists():
        return result

    for char_name in characters:
        char_bible_path = character_dir / char_name / "character_bible.json"
        if char_bible_path.exists():
            result[char_name] = load_json(char_bible_path)

    return result


def get_scene_for_location(location: str, scenes_dir: Path) -> Dict[str, Any]:
    if not scenes_dir.exists():
        return {}

    for scene_folder in scenes_dir.iterdir():
        if scene_folder.is_dir():
            meta_path = scene_folder / "scene_meta.json"
            if meta_path.exists():
                scene_meta = load_json(meta_path)
                if scene_meta.get("scene_name") == location:
                    return {
                        "name": scene_meta.get("scene_name"),
                        "description": scene_meta.get("description", ""),
                        "images": scene_meta.get("images", {})
                    }

    return {}
