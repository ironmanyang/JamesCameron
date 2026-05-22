import shutil
from pathlib import Path
from typing import Any

from app.storage.common import read_json, utc_now_iso, write_json_atomic
from app.storage.naming import next_numeric_id
from app.storage.series_store import get_series, get_series_path, update_series_pointer


DEFAULT_PRODUCTION_MODE = "shot_pipeline"
SUPPORTED_PRODUCTION_MODES = {"shot_pipeline", "scene_direct"}
DEFAULT_SHOT_STORY = {
    "description": "",
    "emotion": "",
    "beat": "",
    "raw_script_excerpt": "",
}
DEFAULT_SHOT_ANCHOR_STRATEGY = {
    "mode": "auto",
    "per_character": {},
}


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


def get_storyboard_shot_media_root(series_slug: str, storyboard_id: str) -> Path:
    return get_storyboard_dir(series_slug, storyboard_id) / "shot_media"


def get_storyboard_draft_shot_media_dir(series_slug: str, storyboard_id: str) -> Path:
    return get_storyboard_shot_media_root(series_slug, storyboard_id) / "_draft"


def get_shot_media_uploads_dir(series_slug: str, storyboard_id: str, shot_id: str) -> Path:
    return get_storyboard_shot_media_root(series_slug, storyboard_id) / shot_id


def get_storyboard(series_slug: str, storyboard_id: str) -> dict | None:
    path = get_storyboard_manifest_path(series_slug, storyboard_id)
    if not path.exists():
        return None
    return _normalize_storyboard_manifest(read_json(path))


def list_storyboards(series_slug: str) -> list[dict]:
    root = get_storyboards_root(series_slug)
    if not root.exists():
        return []

    items: list[dict] = []
    for child in root.iterdir():
        manifest_path = child / "storyboard.json"
        if child.is_dir() and manifest_path.exists():
            items.append(_normalize_storyboard_manifest(read_json(manifest_path)))

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


def normalize_storyboard_production_mode(value: str | None) -> str:
    normalized = str(value or "").strip()
    return normalized if normalized in SUPPORTED_PRODUCTION_MODES else DEFAULT_PRODUCTION_MODE


def _normalize_storyboard_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    payload = dict(manifest or {})
    payload["production_mode"] = normalize_storyboard_production_mode(payload.get("production_mode"))
    payload.setdefault("scene_direct_config", {})
    payload.setdefault("scene_direct_package", {})
    return payload


def create_storyboard(series_slug: str, episode_id: str, production_mode: str | None = None) -> dict:
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
        "production_mode": normalize_storyboard_production_mode(production_mode),
        "scene_direct_config": {},
        "scene_direct_package": {},
        "shot_ids": [],
    }
    write_json_atomic(storyboard_dir / "storyboard.json", manifest)
    update_series_pointer(series_slug, "current_storyboard_id", storyboard_id)
    return manifest


def save_storyboard(series_slug: str, storyboard_id: str, storyboard_data: dict[str, Any]) -> dict:
    existing = get_storyboard(series_slug, storyboard_id)
    if existing is None:
        raise FileNotFoundError(storyboard_id)

    merged = dict(existing)
    merged.update(storyboard_data or {})
    merged["id"] = storyboard_id
    merged["production_mode"] = normalize_storyboard_production_mode(merged.get("production_mode"))
    merged["updated_at"] = utc_now_iso()
    write_json_atomic(get_storyboard_manifest_path(series_slug, storyboard_id), merged)
    return merged


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
        "story": dict(DEFAULT_SHOT_STORY),
        "anchor_strategy": dict(DEFAULT_SHOT_ANCHOR_STRATEGY),
        "dialogue": [],
        "media": {
            "mode": "reference_image",
            "generate_audio": True,
            "first_frame_path": "",
            "last_frame_path": "",
            "reference_image_paths": [],
        },
        "visual": {
            "aspect_ratio": "16:9",
            "style": "cinematic realism",
            "resolution": "1080p",
            "generation_count": 1,
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
        payload["story"] = {
            **DEFAULT_SHOT_STORY,
            **((payload.get("story") or {}) if isinstance(payload.get("story"), dict) else {}),
        }
        payload["anchor_strategy"] = {
            **DEFAULT_SHOT_ANCHOR_STRATEGY,
            **((payload.get("anchor_strategy") or {}) if isinstance(payload.get("anchor_strategy"), dict) else {}),
        }
        payload.setdefault("dialogue", [])
        payload.setdefault("media", {})
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
    merged["story"] = {
        **DEFAULT_SHOT_STORY,
        **((existing.get("story") or {}) if isinstance(existing.get("story"), dict) else {}),
        **((shot_data.get("story") or {}) if isinstance(shot_data.get("story"), dict) else {}),
    }
    merged["anchor_strategy"] = {
        **DEFAULT_SHOT_ANCHOR_STRATEGY,
        **((existing.get("anchor_strategy") or {}) if isinstance(existing.get("anchor_strategy"), dict) else {}),
        **((shot_data.get("anchor_strategy") or {}) if isinstance(shot_data.get("anchor_strategy"), dict) else {}),
    }
    merged.setdefault("dialogue", existing.get("dialogue", []))
    merged.setdefault("media", existing.get("media", {}))
    merged.setdefault("visual", existing.get("visual", {}))
    merged.setdefault("prompt_package", existing.get("prompt_package", {}))
    merged.setdefault("status", existing.get("status", "draft"))

    write_json_atomic(get_shot_path(series_slug, storyboard_id, shot_id), merged)
    storyboard["updated_at"] = utc_now_iso()
    write_json_atomic(get_storyboard_manifest_path(series_slug, storyboard_id), storyboard)
    return merged


def delete_storyboard(series_slug: str, storyboard_id: str) -> None:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    from app.storage.job_store import list_jobs
    from app.storage.snapshot_store import list_snapshots

    linked_snapshots = [item["id"] for item in list_snapshots(series_slug) if item.get("storyboard_id") == storyboard_id]
    if linked_snapshots:
        raise ValueError(f"当前分镜板仍被快照引用，无法删除：{', '.join(linked_snapshots[:5])}")

    linked_jobs: list[str] = []
    snapshot_id_set = {item.get("id", "") for item in list_snapshots(series_slug) if item.get("storyboard_id") == storyboard_id}
    for job in list_jobs(series_slug):
        if job.get("snapshot_id") in snapshot_id_set:
            linked_jobs.append(job["id"])
    if linked_jobs:
        raise ValueError(f"当前分镜板仍被任务引用，无法删除：{', '.join(linked_jobs[:5])}")

    shutil.rmtree(get_storyboard_dir(series_slug, storyboard_id))


def delete_shot(series_slug: str, storyboard_id: str, shot_id: str) -> None:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    shot = get_shot(series_slug, storyboard_id, shot_id)
    if shot is None:
        raise FileNotFoundError(shot_id)

    from app.storage.job_store import list_jobs
    from app.storage.snapshot_store import list_snapshots

    linked_snapshots = [item["id"] for item in list_snapshots(series_slug) if item.get("shot_id") == shot_id]
    if linked_snapshots:
        raise ValueError(f"当前镜头仍被快照引用，无法删除：{', '.join(linked_snapshots[:5])}")

    linked_jobs: list[str] = []
    snapshot_id_set = {item.get("id", "") for item in list_snapshots(series_slug) if item.get("shot_id") == shot_id}
    for job in list_jobs(series_slug):
        if job.get("snapshot_id") in snapshot_id_set:
            linked_jobs.append(job["id"])
    if linked_jobs:
        raise ValueError(f"当前镜头仍被任务引用，无法删除：{', '.join(linked_jobs[:5])}")

    get_shot_path(series_slug, storyboard_id, shot_id).unlink()
    storyboard["shot_ids"] = [item for item in storyboard.get("shot_ids", []) if item != shot_id]
    storyboard["updated_at"] = utc_now_iso()
    write_json_atomic(get_storyboard_manifest_path(series_slug, storyboard_id), storyboard)
