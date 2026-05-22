from typing import Any

from app.services.shot_assembly import assemble_shot_prompt_package
from app.services.video_generation import create_video_job_from_snapshot, refresh_video_job, submit_video_job
from app.storage.common import utc_now_iso
from app.storage.job_store import get_job
from app.storage.shot_batch_store import create_shot_batch, get_shot_batch, list_shot_batches, update_shot_batch
from app.storage.snapshot_store import create_snapshot
from app.storage.storyboard_store import get_shot, get_storyboard


DEFAULT_BATCH_PROVIDER = {
    "name": "doubao-seedance-2-0",
    "submit_mode": "generic_http",
    "model": "doubao-seedance-2-0-260128",
}

JOB_STATUSES_SUBMITTABLE = {"prepared", "failed"}
JOB_STATUSES_REFRESHABLE = {"submitted", "submitting"}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _default_batch_name(shot_ids: list[str]) -> str:
    if not shot_ids:
        return "空批次"
    if len(shot_ids) == 1:
        return f"镜头草稿批次 {shot_ids[0]}"
    return f"镜头草稿批次 {shot_ids[0]} - {shot_ids[-1]}"


def _normalize_provider(provider: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(DEFAULT_BATCH_PROVIDER)
    for key, value in (provider or {}).items():
        if value not in (None, ""):
            merged[key] = value
    return merged


def _map_job_status_to_batch_status(job_status: str) -> str:
    normalized = _clean_text(job_status)
    if normalized == "prepared":
        return "draft_ready"
    if normalized in {"submitted", "submitting"}:
        return "submitted"
    if normalized == "completed":
        return "completed"
    if normalized == "failed":
        return "failed"
    return normalized or "pending"


def _run_batch_item(
    *,
    series_slug: str,
    storyboard_id: str,
    batch_id: str,
    item: dict[str, Any],
    auto_assemble_if_missing: bool,
    provider: dict[str, Any],
) -> dict[str, Any]:
    shot_id = _clean_text(item.get("shot_id", ""))

    next_item = dict(item)
    next_item.update(
        {
            "status": "running",
            "error": "",
            "started_at": utc_now_iso(),
            "finished_at": "",
            "attempt_count": int(item.get("attempt_count") or 0) + 1,
        }
    )

    try:
        shot = get_shot(series_slug, storyboard_id, shot_id)
        if shot is None:
            raise FileNotFoundError(shot_id)

        prompt_package = shot.get("prompt_package") or {}
        if not _clean_text(prompt_package.get("positive", "")):
            if not auto_assemble_if_missing:
                raise ValueError(f"镜头 {shot_id} 还没有镜头包")
            next_item["status"] = "assembling_package"
            shot = assemble_shot_prompt_package(series_slug, storyboard_id, shot_id)
            prompt_package = shot.get("prompt_package") or {}
            if not _clean_text(prompt_package.get("positive", "")):
                raise ValueError(f"镜头 {shot_id} 镜头包生成失败")

        snapshot = create_snapshot(
            series_slug,
            storyboard_id,
            shot_id,
            provider_payload={
                "source": "shot-batch",
                "batch_id": batch_id,
                "shot_id": shot_id,
            },
        )
        next_item.update(
            {
                "status": "snapshot_ready",
                "snapshot_id": snapshot["id"],
            }
        )

        job = create_video_job_from_snapshot(
            series_slug,
            snapshot["id"],
            job_type="video_generation",
            provider_override=provider,
            auto_submit=False,
        )
        next_item.update(
            {
                "status": "draft_ready",
                "snapshot_id": snapshot["id"],
                "job_id": job["id"],
                "finished_at": utc_now_iso(),
            }
        )
        return next_item
    except Exception as exc:
        next_item.update(
            {
                "status": "failed",
                "error": str(exc),
                "finished_at": utc_now_iso(),
            }
        )
        return next_item


def _persist_batch_items(
    *,
    series_slug: str,
    storyboard_id: str,
    batch_id: str,
    provider: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return update_shot_batch(
        series_slug,
        storyboard_id,
        batch_id,
        {
            "provider": provider,
            "items": items,
        },
    )


def _ordered_items(current: dict[str, Any], item_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [item_map.get(item.get("shot_id", ""), item) for item in current.get("items") or []]


def _run_batch(
    *,
    series_slug: str,
    storyboard_id: str,
    batch: dict[str, Any],
    target_shot_ids: list[str],
) -> dict[str, Any]:
    auto_assemble_if_missing = bool(batch.get("auto_assemble_if_missing", True))
    provider = _normalize_provider(batch.get("provider") or {})
    current = update_shot_batch(series_slug, storyboard_id, batch["id"], {"status": "running"})

    item_map = {item.get("shot_id", ""): dict(item) for item in current.get("items") or []}
    for shot_id in target_shot_ids:
        existing_item = item_map.get(shot_id)
        if not existing_item:
            continue
        item_map[shot_id] = _run_batch_item(
            series_slug=series_slug,
            storyboard_id=storyboard_id,
            batch_id=batch["id"],
            item=existing_item,
            auto_assemble_if_missing=auto_assemble_if_missing,
            provider=provider,
        )
        current = _persist_batch_items(
            series_slug=series_slug,
            storyboard_id=storyboard_id,
            batch_id=batch["id"],
            provider=provider,
            items=_ordered_items(current, item_map),
        )

    return get_shot_batch(series_slug, storyboard_id, batch["id"]) or current


def create_shot_batch_and_generate(
    *,
    series_slug: str,
    storyboard_id: str,
    shot_ids: list[str],
    name: str = "",
    auto_assemble_if_missing: bool = True,
    provider: dict[str, Any] | None = None,
) -> dict[str, Any]:
    storyboard = get_storyboard(series_slug, storyboard_id)
    if storyboard is None:
        raise FileNotFoundError(storyboard_id)

    normalized_shot_ids = [_clean_text(shot_id) for shot_id in shot_ids if _clean_text(shot_id)]
    if not normalized_shot_ids:
        raise ValueError("至少选择一个镜头")

    existing_ids = {item.get("id", "") for item in list_shot_batches(series_slug, storyboard_id)}
    batch = create_shot_batch(
        series_slug,
        storyboard_id,
        name=_clean_text(name) or _default_batch_name(normalized_shot_ids),
        shot_ids=normalized_shot_ids,
        auto_assemble_if_missing=auto_assemble_if_missing,
        provider=_normalize_provider(provider),
    )
    if batch["id"] in existing_ids:
        raise ValueError("批次 ID 冲突，请重试")
    return _run_batch(
        series_slug=series_slug,
        storyboard_id=storyboard_id,
        batch=batch,
        target_shot_ids=normalized_shot_ids,
    )


def retry_failed_shot_batch_items(
    *,
    series_slug: str,
    storyboard_id: str,
    batch_id: str,
    provider: dict[str, Any] | None = None,
) -> dict[str, Any]:
    batch = get_shot_batch(series_slug, storyboard_id, batch_id)
    if batch is None:
        raise FileNotFoundError(batch_id)

    failed_shot_ids = [
        _clean_text(item.get("shot_id", ""))
        for item in batch.get("items") or []
        if item.get("status") == "failed"
    ]
    normalized_failed_shot_ids = [shot_id for shot_id in failed_shot_ids if shot_id]
    if not normalized_failed_shot_ids:
        raise ValueError("当前批次没有失败镜头可重试")

    updated_batch = update_shot_batch(
        series_slug,
        storyboard_id,
        batch_id,
        {
            "provider": _normalize_provider({**(batch.get("provider") or {}), **(provider or {})}),
        },
    )
    return _run_batch(
        series_slug=series_slug,
        storyboard_id=storyboard_id,
        batch=updated_batch,
        target_shot_ids=normalized_failed_shot_ids,
    )


def submit_shot_batch_jobs(
    *,
    series_slug: str,
    storyboard_id: str,
    batch_id: str,
    provider: dict[str, Any] | None = None,
) -> dict[str, Any]:
    batch = get_shot_batch(series_slug, storyboard_id, batch_id)
    if batch is None:
        raise FileNotFoundError(batch_id)

    merged_provider = _normalize_provider({**(batch.get("provider") or {}), **(provider or {})})
    current = update_shot_batch(series_slug, storyboard_id, batch_id, {"provider": merged_provider})

    item_map = {item.get("shot_id", ""): dict(item) for item in current.get("items") or []}
    touched = False

    for item in current.get("items") or []:
        shot_id = _clean_text(item.get("shot_id", ""))
        job_id = _clean_text(item.get("job_id", ""))
        if not shot_id or not job_id:
            continue

        job = get_job(series_slug, job_id)
        if job is None:
            item_map[shot_id] = {
                **dict(item),
                "status": "failed",
                "error": f"任务草稿不存在：{job_id}",
                "finished_at": utc_now_iso(),
            }
            touched = True
            continue

        job_status = _clean_text(job.get("status", ""))
        if job_status not in JOB_STATUSES_SUBMITTABLE:
            item_map[shot_id] = {
                **dict(item),
                "status": _map_job_status_to_batch_status(job_status),
                "error": _clean_text(((job.get("error") or {}).get("message", ""))),
            }
            touched = True
            continue

        item_map[shot_id] = {
            **dict(item),
            "status": "submitting",
            "error": "",
            "started_at": item.get("started_at") or utc_now_iso(),
        }
        current = _persist_batch_items(
            series_slug=series_slug,
            storyboard_id=storyboard_id,
            batch_id=batch_id,
            provider=merged_provider,
            items=_ordered_items(current, item_map),
        )

        submitted_job = submit_video_job(series_slug, job_id, merged_provider)
        submitted_status = _clean_text(submitted_job.get("status", ""))
        item_map[shot_id] = {
            **dict(item_map[shot_id]),
            "status": _map_job_status_to_batch_status(submitted_status),
            "error": _clean_text(((submitted_job.get("error") or {}).get("message", ""))),
            "finished_at": utc_now_iso() if submitted_status in {"submitted", "completed", "failed"} else item_map[shot_id].get("finished_at", ""),
        }
        touched = True
        current = _persist_batch_items(
            series_slug=series_slug,
            storyboard_id=storyboard_id,
            batch_id=batch_id,
            provider=merged_provider,
            items=_ordered_items(current, item_map),
        )

    if not touched:
        raise ValueError("当前批次没有失败/未提交的任务草稿")

    return get_shot_batch(series_slug, storyboard_id, batch_id) or current


def refresh_shot_batch_jobs(
    *,
    series_slug: str,
    storyboard_id: str,
    batch_id: str,
    provider: dict[str, Any] | None = None,
) -> dict[str, Any]:
    batch = get_shot_batch(series_slug, storyboard_id, batch_id)
    if batch is None:
        raise FileNotFoundError(batch_id)

    merged_provider = _normalize_provider({**(batch.get("provider") or {}), **(provider or {})})
    current = update_shot_batch(series_slug, storyboard_id, batch_id, {"provider": merged_provider})
    item_map = {item.get("shot_id", ""): dict(item) for item in current.get("items") or []}
    touched = False

    for item in current.get("items") or []:
        shot_id = _clean_text(item.get("shot_id", ""))
        job_id = _clean_text(item.get("job_id", ""))
        if not shot_id or not job_id:
            continue

        job = get_job(series_slug, job_id)
        if job is None:
            item_map[shot_id] = {
                **dict(item),
                "status": "failed",
                "error": f"任务不存在：{job_id}",
                "finished_at": utc_now_iso(),
            }
            touched = True
            continue

        job_status = _clean_text(job.get("status", ""))
        if job_status in JOB_STATUSES_REFRESHABLE:
            job = refresh_video_job(series_slug, job_id, merged_provider)
            job_status = _clean_text(job.get("status", ""))

        item_map[shot_id] = {
            **dict(item),
            "status": _map_job_status_to_batch_status(job_status),
            "error": _clean_text(((job.get("error") or {}).get("message", ""))),
            "finished_at": utc_now_iso() if job_status in {"completed", "failed"} else item.get("finished_at", ""),
        }
        touched = True

    if not touched:
        raise ValueError("当前批次没有可刷新的任务")

    current = _persist_batch_items(
        series_slug=series_slug,
        storyboard_id=storyboard_id,
        batch_id=batch_id,
        provider=merged_provider,
        items=_ordered_items(current, item_map),
    )
    return get_shot_batch(series_slug, storyboard_id, batch_id) or current
