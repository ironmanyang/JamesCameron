import shutil
from pathlib import Path

from app.config import OUTPUT_ROOT
from app.storage.common import ensure_directory, ensure_storage_manifest, read_json, utc_now_iso, write_json_atomic
from app.storage.naming import ensure_unique_slug, make_series_id, slugify


SERIES_SUBDIRECTORIES = (
    "episodes",
    "characters",
    "scenes",
    "props",
    "storyboards",
    "snapshots",
    "jobs",
    "outputs/images",
    "outputs/videos",
    "outputs/audio",
    "outputs/exports",
    "trash",
)


def get_series_path(series_slug: str) -> Path:
    return OUTPUT_ROOT / series_slug


def get_series_manifest_path(series_slug: str) -> Path:
    return get_series_path(series_slug) / "series.json"


def list_series() -> list[dict]:
    ensure_storage_manifest()
    ensure_directory(OUTPUT_ROOT)

    items: list[dict] = []
    for child in OUTPUT_ROOT.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue

        manifest_path = child / "series.json"
        if not manifest_path.exists():
            continue
        items.append(read_json(manifest_path))

    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return items


def get_series(series_slug: str) -> dict | None:
    manifest_path = get_series_manifest_path(series_slug)
    if not manifest_path.exists():
        return None
    return read_json(manifest_path)


def create_series(name: str, description: str = "") -> dict:
    ensure_storage_manifest()
    ensure_directory(OUTPUT_ROOT)

    slug = ensure_unique_slug(slugify(name), OUTPUT_ROOT)
    series_id = make_series_id(slug)
    now = utc_now_iso()

    series_root = get_series_path(slug)
    for subdirectory in SERIES_SUBDIRECTORIES:
        ensure_directory(series_root / subdirectory)

    manifest = {
        "id": series_id,
        "slug": slug,
        "name": name,
        "description": description,
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "defaults": {
            "aspect_ratio": "16:9",
            "style": "cinematic realism",
            "resolution": "1080p",
            "language": "zh-CN",
        },
        "providers": {
            "script_llm": "deepseek",
            "image_model": "gpt-image",
            "video_model": "",
        },
        "pointers": {
            "current_episode_id": "",
            "current_storyboard_id": "",
        },
    }
    write_json_atomic(series_root / "series.json", manifest)
    return manifest


def update_series_pointer(series_slug: str, pointer_key: str, pointer_value: str) -> dict:
    manifest = get_series(series_slug)
    if manifest is None:
        raise FileNotFoundError(series_slug)

    manifest.setdefault("pointers", {})
    manifest["pointers"][pointer_key] = pointer_value
    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_series_manifest_path(series_slug), manifest)
    return manifest


def update_series(series_slug: str, name: str, description: str = "") -> dict:
    manifest = get_series(series_slug)
    if manifest is None:
        raise FileNotFoundError(series_slug)

    manifest["name"] = name
    manifest["description"] = description
    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_series_manifest_path(series_slug), manifest)
    return manifest


def delete_series(series_slug: str) -> None:
    series_root = get_series_path(series_slug)
    manifest = get_series(series_slug)
    if manifest is None:
        raise FileNotFoundError(series_slug)
    shutil.rmtree(series_root)
