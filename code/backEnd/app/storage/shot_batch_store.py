from pathlib import Path
from typing import Any

from app.storage.common import read_json, utc_now_iso, write_json_atomic
from app.storage.naming import next_numeric_id
from app.storage.storyboard_store import get_storyboard, get_storyboard_dir


def get_shot_batches_root(series_slug: str, storyboard_id: str) -> Path:
    return get_storyboard_dir(series_slug, storyboard_id) / "shot_batches"


def get_shot_batch_path(series_slug: str, storyboard_id: str, batch_id: str) -> Path:
    return get_shot_batches_root(series_slug, storyboard_id) / f"{batch_id}.json"


def get_shot_batch(series_slug: str, storyboard_id: str, batch_id: str) -> dict | None:
    path = get_shot_batch_path(series_slug, storyboard_id, batch_id)
    if not path.exists():
        return None
    return _normalize_shot_batch_manifest(read_json(path))


def list_shot_batches(series_slug: str, storyboard_id: str) -> list[dict]:
    root = get_shot_batches_root(series_slug, storyboard_id)
    if not root.exists():
        return []

    items: list[dict] = []
    for child in root.iterdir():
        if child.is_file() and child.suffix == ".json":
            items.append(_normalize_shot_batch_manifest(read_json(child)))

    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return items


def _recalculate_counts(payload: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items") or []
    total_count = len(items)
    success_statuses = {"draft_ready", "submitted", "completed"}
    failed_statuses = {"failed"}
    processing_statuses = {"pending", "running", "assembling_package", "snapshot_ready", "submitting"}

    success_count = sum(1 for item in items if item.get("status") in success_statuses)
    failed_count = sum(1 for item in items if item.get("status") in failed_statuses)
    processing_count = sum(1 for item in items if item.get("status") in processing_statuses)
    pending_count = sum(1 for item in items if item.get("status") == "pending")

    payload["total_count"] = total_count
    payload["success_count"] = success_count
    payload["failed_count"] = failed_count
    payload["processing_count"] = processing_count
    payload["pending_count"] = pending_count

    if total_count == 0:
        payload["status"] = "draft"
    elif processing_count > 0:
        payload["status"] = "running"
    elif success_count == total_count:
        payload["status"] = "completed"
    elif success_count > 0:
        payload["status"] = "partial_success"
    elif failed_count == total_count:
        payload["status"] = "failed"
    else:
        payload["status"] = "draft"

    return payload


def _normalize_shot_batch_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    payload = dict(manifest or {})
    payload.setdefault("name", "")
    payload.setdefault("mode", "shot_batch")
    payload.setdefault("shot_ids", [])
    payload.setdefault("provider", {})
    payload.setdefault("items", [])
    payload.setdefault("auto_assemble_if_missing", True)
    payload.setdefault("status", "draft")
    payload.setdefault("created_at", "")
    payload.setdefault("updated_at", "")
    return _recalculate_counts(payload)


def create_shot_batch(
    series_slug: str,
    storyboard_id: str,
    *,
    name: str,
    shot_ids: list[str],
    auto_assemble_if_missing: bool,
    provider: dict[str, Any] | None = None,
) -> dict:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    root = get_shot_batches_root(series_slug, storyboard_id)
    root.mkdir(parents=True, exist_ok=True)

    existing_ids = [item.get("id", "") for item in list_shot_batches(series_slug, storyboard_id)]
    batch_id, _ = next_numeric_id("shot_batch", existing_ids)
    now = utc_now_iso()
    manifest = _normalize_shot_batch_manifest(
        {
            "id": batch_id,
            "series_id": storyboard.get("series_id", ""),
            "storyboard_id": storyboard_id,
            "name": name,
            "mode": "shot_batch",
            "shot_ids": list(shot_ids),
            "auto_assemble_if_missing": bool(auto_assemble_if_missing),
            "provider": dict(provider or {}),
            "status": "draft",
            "created_at": now,
            "updated_at": now,
            "items": [
                {
                    "shot_id": shot_id,
                    "order": index + 1,
                    "status": "pending",
                    "snapshot_id": "",
                    "job_id": "",
                    "error": "",
                    "attempt_count": 0,
                    "started_at": "",
                    "finished_at": "",
                }
                for index, shot_id in enumerate(shot_ids)
            ],
        }
    )
    write_json_atomic(get_shot_batch_path(series_slug, storyboard_id, batch_id), manifest)
    return manifest


def update_shot_batch(series_slug: str, storyboard_id: str, batch_id: str, updates: dict[str, Any]) -> dict:
    existing = get_shot_batch(series_slug, storyboard_id, batch_id)
    if existing is None:
        raise FileNotFoundError(batch_id)

    merged = dict(existing)
    for key, value in (updates or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value

    merged["id"] = existing["id"]
    merged["series_id"] = existing.get("series_id", "")
    merged["storyboard_id"] = existing["storyboard_id"]
    merged["updated_at"] = utc_now_iso()
    normalized = _normalize_shot_batch_manifest(merged)
    write_json_atomic(get_shot_batch_path(series_slug, storyboard_id, batch_id), normalized)
    return normalized


def delete_shot_batch(series_slug: str, storyboard_id: str, batch_id: str) -> None:
    existing = get_shot_batch(series_slug, storyboard_id, batch_id)
    if existing is None:
        raise FileNotFoundError(batch_id)

    path = get_shot_batch_path(series_slug, storyboard_id, batch_id)
    if path.exists():
        path.unlink()


def clear_shot_batches(series_slug: str, storyboard_id: str) -> int:
    root = get_shot_batches_root(series_slug, storyboard_id)
    if not root.exists():
        return 0

    deleted = 0
    for child in list(root.iterdir()):
        if child.is_file() and child.suffix == ".json":
            child.unlink()
            deleted += 1
    return deleted
