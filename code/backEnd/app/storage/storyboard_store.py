from pathlib import Path
from typing import Any

from app.storage.common import read_json, utc_now_iso, write_json_atomic
from app.storage.naming import next_numeric_id
from app.storage.series_store import get_series, get_series_path, update_series_pointer


def get_storyboards_root(series_slug: str) -> Path:
    return get_series_path(series_slug) / "storyboards"


def get_storyboard_dir(series_slug: str, storyboard_id: str) -> Path:
    return get_storyboards_root(series_slug) / storyboard_id


def get_storyboard_manifest_path(series_slug: str, storyboard_id: str) -> Path:
    return get_storyboard_dir(series_slug, storyboard_id) / "storyboard.json"


def get_shots_root(series_slug: str, storyboard_id: str) -> Path:
    return get_storyboard_dir(series_slug, storyboard_id) / "shots"


def get_shot_path(series_slug: str, storyboard_id: str, shot_id: str) -> Path:
    return get_shots_root(series_slug, storyboard_id) / f"{shot_id}.json"


def get_storyboard(series_slug: str, storyboard_id: str) -> dict | None:
    path = get_storyboard_manifest_path(series_slug, storyboard_id)
    if not path.exists():
        return None
    return read_json(path)


def list_storyboards(series_slug: str) -> list[dict]:
    root = get_storyboards_root(series_slug)
    if not root.exists():
        return []

    items: list[dict] = []
    for child in root.iterdir():
        manifest_path = child / "storyboard.json"
        if child.is_dir() and manifest_path.exists():
            items.append(read_json(manifest_path))

    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return items


def list_shots(series_slug: str, storyboard_id: str) -> list[dict]:
    shots_root = get_shots_root(series_slug, storyboard_id)
    if not shots_root.exists():
        return []

    items: list[dict] = []
    for child in shots_root.iterdir():
        if child.is_file() and child.suffix == ".json":
            items.append(read_json(child))

    items.sort(key=lambda item: item.get("id", ""))
    return items


def get_shot(series_slug: str, storyboard_id: str, shot_id: str) -> dict | None:
    path = get_shot_path(series_slug, storyboard_id, shot_id)
    if not path.exists():
        return None
    return read_json(path)


def _next_storyboard_id(series_slug: str, episode_id: str) -> tuple[str, int]:
    existing = [
        item["id"]
        for item in list_storyboards(series_slug)
        if item.get("episode_id") == episode_id
    ]
    prefix = f"sb_{episode_id}"
    version_numbers = []
    for item_id in existing:
        if item_id.startswith(f"{prefix}_v"):
            try:
                version_numbers.append(int(item_id.split("_v")[-1]))
            except ValueError:
                continue

    next_version = max(version_numbers, default=0) + 1
    return f"{prefix}_v{next_version:03d}", next_version


def create_storyboard(series_slug: str, episode_id: str) -> dict:
    series = get_series(series_slug)
    if series is None:
        raise FileNotFoundError(series_slug)

    storyboard_id, version = _next_storyboard_id(series_slug, episode_id)
    storyboard_dir = get_storyboard_dir(series_slug, storyboard_id)
    shots_root = storyboard_dir / "shots"
    shots_root.mkdir(parents=True, exist_ok=True)

    now = utc_now_iso()
    manifest = {
        "id": storyboard_id,
        "series_id": series["id"],
        "episode_id": episode_id,
        "version": version,
        "created_at": now,
        "updated_at": now,
        "status": "draft",
        "shot_ids": [],
    }
    write_json_atomic(storyboard_dir / "storyboard.json", manifest)
    update_series_pointer(series_slug, "current_storyboard_id", storyboard_id)
    return manifest


def create_shot(
    series_slug: str,
    storyboard_id: str,
    scene_id: str,
    shot_payload: dict[str, Any] | None = None,
) -> dict:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    existing_ids = storyboard.get("shot_ids", [])
    shot_id, _ = next_numeric_id("shot", existing_ids)
    payload = {
        "id": shot_id,
        "storyboard_id": storyboard_id,
        "scene_id": scene_id,
        "characters": [],
        "props": [],
        "script_source": {
            "episode_id": storyboard["episode_id"],
            "scene_index": 0,
            "shot_index": 0,
        },
        "dialogue": [],
        "visual": {
            "aspect_ratio": "16:9",
            "style": "cinematic realism",
            "resolution": "1080p",
            "shot_size": "wide",
            "camera_angle": "eye_level",
            "camera_movement": "static",
            "lens": "35mm",
            "depth_of_field": "medium",
            "lighting": "",
            "palette": "",
            "duration_seconds": 5,
        },
        "prompt_package": {
            "positive": "",
            "negative": "",
            "reference_images": [],
            "script_context": {},
            "scene_context": {},
            "character_context": [],
            "video_payload": {},
            "assembled_from": {},
        },
        "status": "draft",
    }
    if shot_payload:
        payload.update(shot_payload)
        payload["id"] = shot_id
        payload["storyboard_id"] = storyboard_id
        payload["scene_id"] = scene_id
        payload.setdefault("script_source", {"episode_id": storyboard["episode_id"], "scene_index": 0, "shot_index": 0})
        payload.setdefault("dialogue", [])
        payload.setdefault("characters", [])
        payload.setdefault("props", [])
        payload.setdefault("visual", {})
        payload.setdefault("prompt_package", {})
        payload.setdefault("status", "draft")

    write_json_atomic(get_shot_path(series_slug, storyboard_id, shot_id), payload)
    storyboard["shot_ids"] = [*existing_ids, shot_id]
    storyboard["updated_at"] = utc_now_iso()
    write_json_atomic(get_storyboard_manifest_path(series_slug, storyboard_id), storyboard)
    return payload


def save_shot(series_slug: str, storyboard_id: str, shot_id: str, shot_data: dict[str, Any]) -> dict:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    existing = get_shot(series_slug, storyboard_id, shot_id)
    if existing is None:
        raise FileNotFoundError(shot_id)

    merged = dict(existing)
    merged.update(shot_data)
    merged["id"] = shot_id
    merged["storyboard_id"] = storyboard_id
    merged.setdefault("scene_id", existing.get("scene_id", ""))
    merged.setdefault("characters", existing.get("characters", []))
    merged.setdefault("props", existing.get("props", []))
    merged.setdefault("dialogue", existing.get("dialogue", []))
    merged.setdefault("visual", existing.get("visual", {}))
    merged.setdefault("prompt_package", existing.get("prompt_package", {}))
    merged.setdefault("status", existing.get("status", "draft"))

    write_json_atomic(get_shot_path(series_slug, storyboard_id, shot_id), merged)
    storyboard["updated_at"] = utc_now_iso()
    write_json_atomic(get_storyboard_manifest_path(series_slug, storyboard_id), storyboard)
    return merged
