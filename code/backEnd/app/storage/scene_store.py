import shutil
from pathlib import Path
from typing import Any

from app.storage.common import read_json, relative_to_series_root, utc_now_iso, write_json_atomic
from app.storage.naming import ensure_unique_id, make_entity_id
from app.storage.series_store import get_series, get_series_path
from app.storage.storyboard_store import list_shots, list_storyboards


def get_scenes_root(series_slug: str) -> Path:
    return get_series_path(series_slug) / "scenes"


def get_scene_dir(series_slug: str, scene_id: str) -> Path:
    return get_scenes_root(series_slug) / scene_id


def get_scene_manifest_path(series_slug: str, scene_id: str) -> Path:
    return get_scene_dir(series_slug, scene_id) / "scene.json"


def get_scene_prompt_package_path(series_slug: str, scene_id: str) -> Path:
    return get_scene_dir(series_slug, scene_id) / "prompt_package.json"


def get_scene(series_slug: str, scene_id: str) -> dict | None:
    path = get_scene_manifest_path(series_slug, scene_id)
    if not path.exists():
        return None
    return read_json(path)


def get_scene_prompt_package(series_slug: str, scene_id: str) -> dict:
    return read_json(
        get_scene_prompt_package_path(series_slug, scene_id),
        default={
            "scene_id": scene_id,
            "version": 1,
            "summary": "",
            "visual_profile": {},
            "view_prompts": {},
            "negative_prompt": "",
            "generated_from": {"episode_ids": []},
            "reference_images": {"sheet": ""},
        },
    )


def list_scenes(series_slug: str) -> list[dict]:
    root = get_scenes_root(series_slug)
    if not root.exists():
        return []

    items: list[dict] = []
    for child in root.iterdir():
        manifest_path = child / "scene.json"
        if child.is_dir() and manifest_path.exists():
            items.append(read_json(manifest_path))

    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return items


def create_scene(
    series_slug: str,
    name: str,
    description: str = "",
    episode_id: str = "",
) -> dict:
    series = get_series(series_slug)
    if series is None:
        raise FileNotFoundError(series_slug)

    scenes_root = get_scenes_root(series_slug)
    scene_id = ensure_unique_id(make_entity_id("scene", name), scenes_root)
    scene_dir = get_scene_dir(series_slug, scene_id)
    refs_dir = scene_dir / "refs"
    generated_dir = scene_dir / "generated"
    versions_dir = scene_dir / "versions"
    refs_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)

    now = utc_now_iso()
    manifest = {
        "id": scene_id,
        "name": name,
        "series_id": series["id"],
        "episode_id": episode_id,
        "created_at": now,
        "updated_at": now,
        "status": "draft",
        "description": description,
        "visual_profile": {
            "time": "",
            "weather": "",
            "lighting": "",
            "palette": "",
            "style": "",
            "architecture": "",
            "atmosphere": "",
            "key_props": [],
        },
        "prompt_package_path": f"scenes/{scene_id}/prompt_package.json",
        "reference_images": {
            "sheet": "",
        },
        "latest_version": 1,
    }
    prompt_package = {
        "scene_id": scene_id,
        "version": 1,
        "summary": "",
        "visual_profile": manifest["visual_profile"],
        "view_prompts": {
            "establishing": "",
            "closeup": "",
            "bird_eye": "",
            "detail": "",
        },
        "negative_prompt": "",
        "generated_from": {
            "episode_ids": [episode_id] if episode_id else [],
        },
        "reference_images": manifest["reference_images"],
    }

    write_json_atomic(get_scene_manifest_path(series_slug, scene_id), manifest)
    write_json_atomic(get_scene_prompt_package_path(series_slug, scene_id), prompt_package)
    write_json_atomic(scene_dir / "versions" / "scene_v001.json", manifest)
    return manifest


def save_scene_manifest(series_slug: str, scene_id: str, scene_data: dict[str, Any]) -> dict:
    manifest = get_scene(series_slug, scene_id)
    if manifest is None:
        raise FileNotFoundError(scene_id)

    merged = dict(manifest)
    merged.update(scene_data)
    merged["id"] = scene_id
    merged["series_id"] = manifest["series_id"]
    merged["created_at"] = manifest["created_at"]
    merged["updated_at"] = utc_now_iso()
    merged.setdefault("visual_profile", manifest.get("visual_profile", {}))
    merged.setdefault("reference_images", manifest.get("reference_images", {}))
    merged.setdefault("prompt_package_path", manifest.get("prompt_package_path", f"scenes/{scene_id}/prompt_package.json"))

    version = int(manifest.get("latest_version", 1))
    write_json_atomic(get_scene_manifest_path(series_slug, scene_id), merged)
    write_json_atomic(get_scene_dir(series_slug, scene_id) / "versions" / f"scene_v{version:03d}.json", merged)
    return merged


def save_scene_assets(
    series_slug: str,
    scene_id: str,
    *,
    version: int,
    visual_profile: dict[str, Any],
    prompt_package: dict[str, Any],
    reference_images: dict[str, str],
) -> dict:
    manifest = get_scene(series_slug, scene_id)
    if manifest is None:
        raise FileNotFoundError(scene_id)

    series_root = get_series_path(series_slug)
    refs_dir = get_scene_dir(series_slug, scene_id) / "refs"
    versions_dir = get_scene_dir(series_slug, scene_id) / "versions"

    manifest["visual_profile"] = {
        "time": str(visual_profile.get("time", "")).strip(),
        "weather": str(visual_profile.get("weather", "")).strip(),
        "lighting": str(visual_profile.get("lighting", "")).strip(),
        "palette": str(visual_profile.get("palette", "")).strip(),
        "style": str(visual_profile.get("style", "")).strip(),
        "architecture": str(visual_profile.get("architecture", "")).strip(),
        "atmosphere": str(visual_profile.get("atmosphere", "")).strip(),
        "key_props": visual_profile.get("key_props") or [],
    }
    manifest["reference_images"] = {
        "sheet": relative_to_series_root(
            Path(reference_images.get("sheet") or refs_dir / "scene_reference_sheet.jpg"), series_root
        ),
    }
    manifest["latest_version"] = version
    manifest["status"] = "reference_ready"
    manifest["updated_at"] = utc_now_iso()

    payload = dict(prompt_package)
    payload["scene_id"] = scene_id
    payload["version"] = version
    payload.setdefault("summary", "")
    payload.setdefault("visual_profile", manifest["visual_profile"])
    payload.setdefault("view_prompts", {})
    payload.setdefault("negative_prompt", "")
    payload.setdefault("generated_from", {"episode_ids": []})
    payload["reference_images"] = manifest["reference_images"]

    write_json_atomic(get_scene_prompt_package_path(series_slug, scene_id), payload)
    write_json_atomic(get_scene_manifest_path(series_slug, scene_id), manifest)
    write_json_atomic(versions_dir / f"scene_v{version:03d}.json", manifest)
    return manifest


def update_scene(series_slug: str, scene_id: str, name: str, description: str = "", episode_id: str = "") -> dict:
    manifest = get_scene(series_slug, scene_id)
    if manifest is None:
        raise FileNotFoundError(scene_id)

    manifest["name"] = name
    manifest["description"] = description
    manifest["episode_id"] = episode_id
    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_scene_manifest_path(series_slug, scene_id), manifest)
    return manifest


def delete_scene(series_slug: str, scene_id: str) -> None:
    manifest = get_scene(series_slug, scene_id)
    if manifest is None:
        raise FileNotFoundError(scene_id)

    linked_shots: list[str] = []
    for storyboard in list_storyboards(series_slug):
        for shot in list_shots(series_slug, storyboard["id"]):
            if shot.get("scene_id") == scene_id:
                linked_shots.append(shot["id"])

    if linked_shots:
        raise ValueError(f"当前场景仍被镜头引用，无法删除：{', '.join(linked_shots[:5])}")

    shutil.rmtree(get_scene_dir(series_slug, scene_id))
