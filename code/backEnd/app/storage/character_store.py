import shutil
from pathlib import Path
from typing import Any

from app.storage.common import read_json, relative_to_series_root, utc_now_iso, write_json_atomic
from app.storage.naming import ensure_unique_id, make_entity_id
from app.storage.series_store import get_series, get_series_path
from app.storage.storyboard_store import list_shots, list_storyboards


def get_characters_root(series_slug: str) -> Path:
    return get_series_path(series_slug) / "characters"


def get_character_dir(series_slug: str, character_id: str) -> Path:
    return get_characters_root(series_slug) / character_id


def get_character_manifest_path(series_slug: str, character_id: str) -> Path:
    return get_character_dir(series_slug, character_id) / "character.json"


def get_character_bible_path(series_slug: str, character_id: str) -> Path:
    return get_character_dir(series_slug, character_id) / "bible.json"


def get_character_source_uploads_dir(series_slug: str, character_id: str) -> Path:
    return get_character_dir(series_slug, character_id) / "source_uploads"


def get_character(series_slug: str, character_id: str) -> dict | None:
    path = get_character_manifest_path(series_slug, character_id)
    if not path.exists():
        return None
    return read_json(path)


def get_character_bible(series_slug: str, character_id: str) -> dict:
    return read_json(
        get_character_bible_path(series_slug, character_id),
        default={
            "character_id": character_id,
            "version": 1,
            "brief": "",
            "bible": {},
            "visual_prompts": {},
            "notes": [],
            "generated_from": {"episode_ids": []},
            "reference_images": {"sheet": ""},
            "component_images": {},
            "source_images": [],
        },
    )


def list_characters(series_slug: str) -> list[dict]:
    root = get_characters_root(series_slug)
    if not root.exists():
        return []

    items: list[dict] = []
    for child in root.iterdir():
        manifest_path = child / "character.json"
        if child.is_dir() and manifest_path.exists():
            items.append(read_json(manifest_path))

    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return items


def create_character(series_slug: str, name: str, brief: str = "") -> dict:
    series = get_series(series_slug)
    if series is None:
        raise FileNotFoundError(series_slug)

    characters_root = get_characters_root(series_slug)
    character_id = ensure_unique_id(make_entity_id("char", name), characters_root)
    character_dir = get_character_dir(series_slug, character_id)
    refs_dir = character_dir / "refs"
    generated_dir = character_dir / "generated"
    source_uploads_dir = character_dir / "source_uploads"
    versions_dir = character_dir / "versions"
    refs_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    source_uploads_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)

    now = utc_now_iso()
    manifest = {
        "id": character_id,
        "name": name,
        "aliases": [],
        "series_id": series["id"],
        "created_at": now,
        "updated_at": now,
        "status": "draft",
        "anchors": {
            "biology": "",
            "face": "",
            "hair": "",
            "costume": "",
            "palette": "",
            "aura": "",
        },
        "brief": brief,
        "bible_path": f"characters/{character_id}/bible.json",
        "reference_images": {
            "sheet": "",
        },
        "component_images": {
            "front": "",
            "side": "",
            "back": "",
            "features": "",
        },
        "source_images": [],
        "latest_version": 1,
    }
    bible = {
        "character_id": character_id,
        "version": 1,
        "brief": brief,
        "summary": "",
        "anchors": manifest["anchors"],
        "bible": {},
        "visual_prompts": {},
        "negative_prompt": "",
        "notes": [],
        "generated_from": {
            "episode_ids": [],
        },
        "reference_images": manifest["reference_images"],
        "component_images": manifest["component_images"],
        "source_images": manifest["source_images"],
    }

    write_json_atomic(get_character_manifest_path(series_slug, character_id), manifest)
    write_json_atomic(get_character_bible_path(series_slug, character_id), bible)
    return manifest


def save_character_bible(series_slug: str, character_id: str, bible_data: dict[str, Any]) -> dict:
    manifest = get_character(series_slug, character_id)
    if manifest is None:
        raise FileNotFoundError(character_id)

    character_dir = get_character_dir(series_slug, character_id)
    version = int(manifest.get("latest_version", 1))
    payload = dict(bible_data)
    payload.setdefault("character_id", character_id)
    payload.setdefault("version", version)
    payload.setdefault("brief", manifest.get("brief", ""))
    payload.setdefault("summary", "")
    payload.setdefault("anchors", manifest.get("anchors", {}))
    payload.setdefault("bible", {})
    payload.setdefault("visual_prompts", {})
    payload.setdefault("negative_prompt", "")
    payload.setdefault("notes", [])
    payload.setdefault("generated_from", {"episode_ids": []})
    payload.setdefault("reference_images", manifest.get("reference_images", {"sheet": ""}))
    payload.setdefault("component_images", manifest.get("component_images", {}))
    payload.setdefault("source_images", manifest.get("source_images", []))

    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_character_bible_path(series_slug, character_id), payload)
    write_json_atomic(character_dir / "versions" / f"bible_v{version:03d}.json", payload)
    write_json_atomic(get_character_manifest_path(series_slug, character_id), manifest)
    return manifest


def save_character_assets(
    series_slug: str,
    character_id: str,
    *,
    version: int,
    anchors: dict[str, str],
    bible_data: dict[str, Any],
    reference_images: dict[str, str],
    component_images: dict[str, str],
) -> dict:
    manifest = get_character(series_slug, character_id)
    if manifest is None:
        raise FileNotFoundError(character_id)

    series_root = get_series_path(series_slug)
    versions_dir = get_character_dir(series_slug, character_id) / "versions"

    manifest["anchors"] = {
        "biology": anchors.get("biology", ""),
        "face": anchors.get("face", ""),
        "hair": anchors.get("hair", ""),
        "costume": anchors.get("costume", ""),
        "palette": anchors.get("palette", ""),
        "aura": anchors.get("aura", ""),
    }
    manifest["reference_images"] = {
        "sheet": relative_to_series_root(Path(reference_images.get("sheet", "")), series_root)
        if reference_images.get("sheet")
        else "",
    }
    manifest["component_images"] = {
        "front": relative_to_series_root(Path(component_images.get("front", "")), series_root)
        if component_images.get("front")
        else "",
        "side": relative_to_series_root(Path(component_images.get("side", "")), series_root)
        if component_images.get("side")
        else "",
        "back": relative_to_series_root(Path(component_images.get("back", "")), series_root)
        if component_images.get("back")
        else "",
        "features": relative_to_series_root(Path(component_images.get("features", "")), series_root)
        if component_images.get("features")
        else "",
    }
    manifest["latest_version"] = version
    manifest["status"] = "reference_ready"
    manifest["updated_at"] = utc_now_iso()

    payload = dict(bible_data)
    payload["character_id"] = character_id
    payload["version"] = version
    payload.setdefault("brief", manifest.get("brief", ""))
    payload.setdefault("summary", "")
    payload.setdefault("anchors", manifest["anchors"])
    payload.setdefault("bible", {})
    payload.setdefault("visual_prompts", {})
    payload.setdefault("negative_prompt", "")
    payload.setdefault("notes", [])
    payload.setdefault("generated_from", {"episode_ids": []})
    payload["reference_images"] = manifest["reference_images"]
    payload["component_images"] = manifest["component_images"]
    payload["source_images"] = manifest.get("source_images", [])

    write_json_atomic(get_character_bible_path(series_slug, character_id), payload)
    write_json_atomic(versions_dir / f"bible_v{version:03d}.json", payload)
    write_json_atomic(get_character_manifest_path(series_slug, character_id), manifest)
    return manifest


def save_character_source_images(series_slug: str, character_id: str, source_images: list[dict[str, Any]]) -> dict:
    manifest = get_character(series_slug, character_id)
    if manifest is None:
        raise FileNotFoundError(character_id)

    manifest["source_images"] = source_images
    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_character_manifest_path(series_slug, character_id), manifest)

    bible = get_character_bible(series_slug, character_id)
    bible["source_images"] = source_images
    write_json_atomic(get_character_bible_path(series_slug, character_id), bible)
    return manifest


def update_character(series_slug: str, character_id: str, name: str, brief: str = "") -> dict:
    manifest = get_character(series_slug, character_id)
    if manifest is None:
        raise FileNotFoundError(character_id)

    manifest["name"] = name
    manifest["brief"] = brief
    manifest["updated_at"] = utc_now_iso()
    write_json_atomic(get_character_manifest_path(series_slug, character_id), manifest)

    bible = get_character_bible(series_slug, character_id)
    bible["brief"] = brief
    write_json_atomic(get_character_bible_path(series_slug, character_id), bible)
    return manifest


def delete_character(series_slug: str, character_id: str) -> None:
    manifest = get_character(series_slug, character_id)
    if manifest is None:
        raise FileNotFoundError(character_id)

    linked_shots: list[str] = []
    for storyboard in list_storyboards(series_slug):
        for shot in list_shots(series_slug, storyboard["id"]):
            if character_id in (shot.get("characters") or []):
                linked_shots.append(shot["id"])

    if linked_shots:
        raise ValueError(f"当前角色仍被镜头引用，无法删除：{', '.join(linked_shots[:5])}")

    shutil.rmtree(get_character_dir(series_slug, character_id))


def delete_character_source_image(series_slug: str, character_id: str, image_path: str) -> dict:
    manifest = get_character(series_slug, character_id)
    if manifest is None:
        raise FileNotFoundError(character_id)

    normalized_path = image_path.strip()
    source_images = list(manifest.get("source_images") or [])
    matched_item = next((item for item in source_images if str(item.get("path", "")).strip() == normalized_path), None)
    if matched_item is None:
        raise FileNotFoundError(normalized_path)

    absolute_path = get_series_path(series_slug) / normalized_path
    if absolute_path.exists():
        absolute_path.unlink()

    remaining = [item for item in source_images if str(item.get("path", "")).strip() != normalized_path]
    return save_character_source_images(series_slug, character_id, remaining)
