from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.video_generation import create_video_job_from_snapshot, refresh_video_job, submit_video_job
from app.storage.job_store import create_job, get_job, list_jobs, update_job


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    type: str = Field(default="video_generation", min_length=1)
    provider: dict[str, Any] = Field(default_factory=dict)


class UpdateJobRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    updates: dict[str, Any]


class CreateJobFromSnapshotRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    type: str = Field(default="video_generation", min_length=1)
    provider: dict[str, Any] = Field(default_factory=dict)
    auto_submit: bool = Field(default=False)


class SubmitJobRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    provider: dict[str, Any] = Field(default_factory=dict)


class RefreshJobRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    provider: dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def list_jobs_api(series_slug: str = Query(min_length=1)):
    return {"items": list_jobs(series_slug.strip())}


@router.post("")
async def create_job_api(payload: CreateJobRequest):
    try:
        item = create_job(
            series_slug=payload.series_slug.strip(),
            snapshot_id=payload.snapshot_id.strip(),
            job_type=payload.type.strip(),
            provider=payload.provider,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="任务来源数据不存在") from exc
    return {"item": item}


@router.post("/from-snapshot")
async def create_job_from_snapshot_api(payload: CreateJobFromSnapshotRequest):
    try:
        item = create_video_job_from_snapshot(
            series_slug=payload.series_slug.strip(),
            snapshot_id=payload.snapshot_id.strip(),
            job_type=payload.type.strip(),
            provider_override=payload.provider,
            auto_submit=payload.auto_submit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="快照不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@router.get("/{job_id}")
async def get_job_api(job_id: str, series_slug: str = Query(min_length=1)):
    item = get_job(series_slug.strip(), job_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"item": item}


@router.put("/{job_id}")
async def update_job_api(job_id: str, payload: UpdateJobRequest):
    try:
        item = update_job(
            series_slug=payload.series_slug.strip(),
            job_id=job_id.strip(),
            updates=payload.updates,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="任务不存在") from exc
    return {"item": item}


@router.post("/{job_id}/submit")
async def submit_job_api(job_id: str, payload: SubmitJobRequest):
    try:
        item = submit_video_job(
            series_slug=payload.series_slug.strip(),
            job_id=job_id.strip(),
            provider_override=payload.provider,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="任务不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@router.post("/{job_id}/refresh")
async def refresh_job_api(job_id: str, payload: RefreshJobRequest):
    try:
        item = refresh_video_job(
            series_slug=payload.series_slug.strip(),
            job_id=job_id.strip(),
            provider_override=payload.provider,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="任务不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}
