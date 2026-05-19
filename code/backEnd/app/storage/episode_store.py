import shutil
from pathlib import Path
from typing import Any

from app.storage.common import (
    read_json,
    relative_to_series_root,
    utc_now_iso,
    write_json_atomic,
    write_text_atomic,
)
from app.storage.naming import next_episode_id
from app.storage.series_store import get_series, get_series_path, update_series_pointer
from app.storage.scene_store import list_scenes
from app.storage.storyboard_store import list_storyboards


def get_episode_dir(series_slug: str, episode_id: str) -> Path:
    return get_series_path(series_slug) / "episodes" / episode_id


def get_episode_manifest_path(series_slug: str, episode_id: str) -> Path:
    return get_episode_dir(series_slug, episode_id) / "episode.json"


def get_episode(series_slug: str, episode_id: str) -> dict | None:
    manifest_path = get_episode_manifest_path(series_slug, episode_id)
    if not manifest_path.exists():
        return None
    return read_json(manifest_path)


def list_episodes(series_slug: str) -> list[dict]:
    episodes_root = get_series_path(series_slug) / "episodes"
    if not episodes_root.exists():
        return []

    items: list[dict] = []
    for child in episodes_root.iterdir():
        manifest_path = child / "episode.json"
        if child.is_dir() and manifest_path.exists():
            items.append(read_json(manifest_path))

    items.sort(key=lambda item: item.get("episode_number", 0))
    return items


def create_episode(series_slug: str, name: str = "", episode_number: int | None = None) -> dict:
    series = get_series(series_slug)
    if series is None:
        raise FileNotFoundError(series_slug)

    existing = list_episodes(series_slug)
    existing_ids = [item["id"] for item in existing]

    if episode_number is None:
        episode_id, episode_number = next_episode_id(existing_ids)
    else:
        episode_id = f"ep_{episode_number:03d}"
        if episode_id in existing_ids:
            raise ValueError(f"剧集已存在：{episode_id}")

    now = utc_now_iso()
    episode_dir = get_episode_dir(series_slug, episode_id)
    raw_path = episode_dir / "script.raw.txt"
    parsed_path = episode_dir / "script.parsed.json"
    versions_dir = episode_dir / "script.versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    series_root = get_series_path(series_slug)

    manifest = {
        "id": episode_id,
        "series_id": series["id"],
        "episode_number": episode_number,
        "name": name or f"第{episode_number}集",
        "status": "draft",
        "created_at": now,
        "updated_at": now,
        "script": {
            "raw_text_path": relative_to_series_root(raw_path, series_root),
            "parsed_path": relative_to_series_root(parsed_path, series_root),
            "latest_version": 0,
        },
    }
    write_json_atomic(get_episode_manifest_path(series_slug, episode_id), manifest)
    write_text_atomic(raw_path, "")
    write_json_atomic(parsed_path, {})
    update_series_pointer(series_slug, "current_episode_id", episode_id)
    return manifest


def save_raw_script(series_slug: str, episode_id: str, raw_text: str) -> dict:
    manifest = get_episode(series_slug, episode_id)
    if manifest is None:
        raise FileNotFoundError(episode_id)

    episode_dir = get_episode_dir(series_slug, episode_id)
    latest_version = int(manifest.get("script", {}).get("latest_version", 0)) + 1
    raw_path = episode_dir / "script.raw.txt"
    versioned_raw_path = episode_dir / "script.versions" / f"raw_v{latest_version:03d}.txt"

    write_text_atomic(raw_path, raw_text)
    write_text_atomic(versioned_raw_path, raw_text)

    manifest["script"]["latest_version"] = latest_version
    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_episode_manifest_path(series_slug, episode_id), manifest)
    update_series_pointer(series_slug, "current_episode_id", episode_id)
    return manifest


def save_parsed_script(series_slug: str, episode_id: str, parsed_script: dict[str, Any]) -> dict:
    manifest = get_episode(series_slug, episode_id)
    if manifest is None:
        raise FileNotFoundError(episode_id)

    episode_dir = get_episode_dir(series_slug, episode_id)
    latest_version = int(manifest.get("script", {}).get("latest_version", 0))
    if latest_version == 0:
        latest_version = 1
        manifest["script"]["latest_version"] = latest_version

    payload = dict(parsed_script)
    payload.setdefault("episode_id", episode_id)
    payload.setdefault("source_version", latest_version)
    payload.setdefault("acts", [])
    payload.setdefault("scenes", [])
    payload.setdefault("extracted_entities", {"characters": [], "scenes": [], "props": []})

    parsed_path = episode_dir / "script.parsed.json"
    versioned_parsed_path = episode_dir / "script.versions" / f"parsed_v{latest_version:03d}.json"

    write_json_atomic(parsed_path, payload)
    write_json_atomic(versioned_parsed_path, payload)

    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_episode_manifest_path(series_slug, episode_id), manifest)
    update_series_pointer(series_slug, "current_episode_id", episode_id)
    return manifest


def load_raw_script(series_slug: str, episode_id: str) -> str:
    manifest = get_episode(series_slug, episode_id)
    if manifest is None:
        raise FileNotFoundError(episode_id)

    raw_path = get_episode_dir(series_slug, episode_id) / "script.raw.txt"
    if not raw_path.exists():
        return ""
    return raw_path.read_text(encoding="utf-8")


def load_parsed_script(series_slug: str, episode_id: str) -> dict[str, Any]:
    manifest = get_episode(series_slug, episode_id)
    if manifest is None:
        raise FileNotFoundError(episode_id)

    parsed_path = get_episode_dir(series_slug, episode_id) / "script.parsed.json"
    if not parsed_path.exists():
        return {}
    return read_json(parsed_path)


def update_episode(series_slug: str, episode_id: str, name: str) -> dict:
    manifest = get_episode(series_slug, episode_id)
    if manifest is None:
        raise FileNotFoundError(episode_id)

    manifest["name"] = name
    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_episode_manifest_path(series_slug, episode_id), manifest)
    return manifest


def delete_episode(series_slug: str, episode_id: str) -> None:
    manifest = get_episode(series_slug, episode_id)
    if manifest is None:
        raise FileNotFoundError(episode_id)

    linked_scenes = [item["id"] for item in list_scenes(series_slug) if item.get("episode_id") == episode_id]
    if linked_scenes:
        raise ValueError(f"当前剧集仍被场景引用，无法删除：{', '.join(linked_scenes[:5])}")

    linked_storyboards = [item["id"] for item in list_storyboards(series_slug) if item.get("episode_id") == episode_id]
    if linked_storyboards:
        raise ValueError(f"当前剧集仍被分镜板引用，无法删除：{', '.join(linked_storyboards[:5])}")

    shutil.rmtree(get_episode_dir(series_slug, episode_id))
