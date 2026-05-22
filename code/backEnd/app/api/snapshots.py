from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.storage.snapshot_store import create_scene_direct_snapshot, create_snapshot, delete_snapshot, get_snapshot, list_snapshots


router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


class CreateSnapshotRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    storyboard_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    provider_payload: dict = Field(default_factory=dict)


class CreateSceneDirectSnapshotRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    storyboard_id: str = Field(min_length=1)
    provider_payload: dict = Field(default_factory=dict)


@router.get("")
async def list_snapshots_api(series_slug: str = Query(min_length=1)):
    return {"items": list_snapshots(series_slug.strip())}


@router.post("")
async def create_snapshot_api(payload: CreateSnapshotRequest):
    try:
        item = create_snapshot(
            series_slug=payload.series_slug.strip(),
            storyboard_id=payload.storyboard_id.strip(),
            shot_id=payload.shot_id.strip(),
            provider_payload=payload.provider_payload,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="快照来源数据不存在") from exc
    return {"item": item}


@router.post("/scene-direct")
async def create_scene_direct_snapshot_api(payload: CreateSceneDirectSnapshotRequest):
    try:
        item = create_scene_direct_snapshot(
            series_slug=payload.series_slug.strip(),
            storyboard_id=payload.storyboard_id.strip(),
            provider_payload=payload.provider_payload,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="场景直出来源数据不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@router.get("/{snapshot_id}")
async def get_snapshot_api(snapshot_id: str, series_slug: str = Query(min_length=1)):
    item = get_snapshot(series_slug.strip(), snapshot_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="快照不存在")
    return {"item": item}


@router.delete("/{snapshot_id}")
async def delete_snapshot_api(snapshot_id: str, series_slug: str = Query(min_length=1)):
    try:
        delete_snapshot(series_slug.strip(), snapshot_id.strip())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="快照不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}
