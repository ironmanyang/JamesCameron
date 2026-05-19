from pathlib import Path

from app.storage.character_store import get_character
from app.storage.common import read_json, utc_now_iso, write_json_atomic
from app.storage.scene_store import get_scene
from app.storage.series_store import get_series, get_series_path
from app.storage.storyboard_store import get_shot


def get_snapshots_root(series_slug: str) -> Path:
    return get_series_path(series_slug) / "snapshots"


def get_snapshot_dir(series_slug: str, snapshot_id: str) -> Path:
    return get_snapshots_root(series_slug) / snapshot_id


def get_snapshot_manifest_path(series_slug: str, snapshot_id: str) -> Path:
    return get_snapshot_dir(series_slug, snapshot_id) / "snapshot.json"


def get_snapshot(series_slug: str, snapshot_id: str) -> dict | None:
    path = get_snapshot_manifest_path(series_slug, snapshot_id)
    if not path.exists():
        return None
    return read_json(path)


def list_snapshots(series_slug: str) -> list[dict]:
    root = get_snapshots_root(series_slug)
    if not root.exists():
        return []

    items: list[dict] = []
    for child in root.iterdir():
        manifest_path = child / "snapshot.json"
        if child.is_dir() and manifest_path.exists():
            items.append(read_json(manifest_path))

    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return items


def _snapshot_asset_paths(series_slug: str, shot: dict) -> dict:
    shot_id = shot["id"]
    storyboard_id = shot["storyboard_id"]
    shot_media = shot.get("media") or {}

    character_paths = []
    scene_paths = []
    prop_paths = []
    images = []
    videos = []
    audio = []

    for character_id in shot.get("characters", []):
        character = get_character(series_slug, character_id)
        if character:
            character_paths.append(f"characters/{character_id}/character.json")
            refs = character.get("reference_images", {})
            images.extend([path for path in refs.values() if path])
            images.extend([item.get("path", "") for item in character.get("source_images", []) if item.get("path")])

    scene_id = shot.get("scene_id", "")
    if scene_id:
        scene = get_scene(series_slug, scene_id)
        if scene:
            scene_paths.append(f"scenes/{scene_id}/scene.json")
            refs = scene.get("reference_images", {})
            images.extend([path for path in refs.values() if path])

    for prop_id in shot.get("props", []):
        prop_path = f"props/{prop_id}/prop.json"
        prop_paths.append(prop_path)

    for path in [
        shot_media.get("first_frame_path", ""),
        shot_media.get("last_frame_path", ""),
        *(shot_media.get("reference_image_paths") or []),
    ]:
        normalized = str(path or "").strip()
        if normalized:
            images.append(normalized)

    for path in shot_media.get("reference_video_paths") or []:
        normalized = str(path or "").strip()
        if normalized:
            videos.append(normalized)

    for path in shot_media.get("reference_audio_paths") or []:
        normalized = str(path or "").strip()
        if normalized:
            audio.append(normalized)

    return {
        "snapshot_id_seed": f"snap_{shot_id}",
        "inputs": {
            "shot_card_path": f"storyboards/{storyboard_id}/shots/{shot_id}.json",
            "character_paths": character_paths,
            "scene_paths": scene_paths,
            "prop_paths": prop_paths,
            "media": shot_media,
            "prompt_package": shot.get("prompt_package", {}),
        },
        "resolved_assets": {
            "images": list(dict.fromkeys(images)),
            "videos": list(dict.fromkeys(videos)),
            "audio": list(dict.fromkeys(audio)),
        },
    }


def create_snapshot(series_slug: str, storyboard_id: str, shot_id: str, provider_payload: dict | None = None) -> dict:
    series = get_series(series_slug)
    if series is None:
        raise FileNotFoundError(series_slug)

    shot = get_shot(series_slug, storyboard_id, shot_id)
    if shot is None:
        raise FileNotFoundError(shot_id)

    snapshots = list_snapshots(series_slug)
    prefix = f"snap_{shot_id}_v"
    versions = []
    for item in snapshots:
        snapshot_id = item.get("id", "")
        if snapshot_id.startswith(prefix):
            try:
                versions.append(int(snapshot_id.split("_v")[-1]))
            except ValueError:
                continue
    version = max(versions, default=0) + 1
    snapshot_id = f"snap_{shot_id}_v{version:03d}"

    snapshot_dir = get_snapshot_dir(series_slug, snapshot_id)
    bundle_dir = snapshot_dir / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    asset_bundle = _snapshot_asset_paths(series_slug, shot)
    manifest = {
        "id": snapshot_id,
        "series_id": series["id"],
        "storyboard_id": storyboard_id,
        "shot_id": shot_id,
        "created_at": utc_now_iso(),
        "inputs": asset_bundle["inputs"],
        "resolved_assets": asset_bundle["resolved_assets"],
        "provider_payload": {
            "model": "",
            "request_body": provider_payload or {},
        },
    }
    write_json_atomic(snapshot_dir / "snapshot.json", manifest)
    return manifest
