from pathlib import Path
from typing import Any

from app.storage.common import read_json, relative_to_series_root, utc_now_iso, write_json_atomic
from app.storage.series_store import get_series, get_series_path
from app.storage.snapshot_store import get_snapshot


def get_jobs_root(series_slug: str) -> Path:
    return get_series_path(series_slug) / "jobs"


def get_job_path(series_slug: str, job_id: str) -> Path:
    return get_jobs_root(series_slug) / f"{job_id}.json"


def get_job_response_dir(series_slug: str) -> Path:
    return get_jobs_root(series_slug) / "_responses"


def get_job(series_slug: str, job_id: str) -> dict | None:
    path = get_job_path(series_slug, job_id)
    if not path.exists():
        return None
    return read_json(path)


def list_jobs(series_slug: str) -> list[dict]:
    root = get_jobs_root(series_slug)
    if not root.exists():
        return []

    items: list[dict] = []
    for child in root.iterdir():
        if child.is_file() and child.suffix == ".json":
            items.append(read_json(child))

    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return items


def _next_job_id(series_slug: str) -> str:
    existing = [item.get("id", "") for item in list_jobs(series_slug)]
    sequence = 1
    while True:
        job_id = f"job_{utc_now_iso().replace('-', '').replace(':', '').replace('T', '_').replace('Z', '')}_{sequence:04d}"
        if job_id not in existing:
            return job_id
        sequence += 1


def create_job(
    series_slug: str,
    snapshot_id: str,
    job_type: str = "video_generation",
    provider: dict[str, Any] | None = None,
    initial_status: str = "queued",
) -> dict:
    series = get_series(series_slug)
    if series is None:
        raise FileNotFoundError(series_slug)

    snapshot = get_snapshot(series_slug, snapshot_id)
    if snapshot is None:
        raise FileNotFoundError(snapshot_id)

    job_id = _next_job_id(series_slug)
    manifest = {
        "id": job_id,
        "series_id": series["id"],
        "snapshot_id": snapshot_id,
        "type": job_type,
        "status": initial_status,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "attempt": 1,
        "provider": {
            **(provider or {}),
            "name": (provider or {}).get("name", ""),
            "model": (provider or {}).get("model", ""),
        },
        "remote": {
            "task_id": "",
            "raw_response_path": "",
            "raw_response": {},
        },
        "result": {
            "video_path": "",
            "cover_path": "",
            "metrics": {},
        },
        "error": {
            "message": "",
            "code": "",
        },
    }
    write_json_atomic(get_job_path(series_slug, job_id), manifest)
    return manifest


def update_job(series_slug: str, job_id: str, updates: dict[str, Any]) -> dict:
    existing = get_job(series_slug, job_id)
    if existing is None:
        raise FileNotFoundError(job_id)

    merged = dict(existing)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value

    merged["id"] = existing["id"]
    merged["series_id"] = existing["series_id"]
    merged["snapshot_id"] = existing["snapshot_id"]
    merged["updated_at"] = utc_now_iso()
    write_json_atomic(get_job_path(series_slug, job_id), merged)
    return merged


def save_job_remote_response(series_slug: str, job_id: str, payload: dict[str, Any]) -> str:
    series_root = get_series_path(series_slug)
    response_path = get_job_response_dir(series_slug) / f"{job_id}.response.json"
    write_json_atomic(response_path, payload)
    return relative_to_series_root(response_path, series_root)


def delete_job(series_slug: str, job_id: str) -> None:
    existing = get_job(series_slug, job_id)
    if existing is None:
        raise FileNotFoundError(job_id)

    status = str(existing.get("status", "")).strip().lower()
    remote_task_id = str((existing.get("remote") or {}).get("task_id", "")).strip()
    protected_statuses = {"submitting", "submitted", "completed"}
    if remote_task_id or status in protected_statuses:
        raise ValueError("当前任务已进入远端执行流程，不能直接删除")

    job_path = get_job_path(series_slug, job_id)
    if job_path.exists():
        job_path.unlink()

    response_path = get_job_response_dir(series_slug) / f"{job_id}.response.json"
    if response_path.exists():
        response_path.unlink()
