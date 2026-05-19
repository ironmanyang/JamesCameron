from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.shot_assembly import assemble_shot_prompt_package
from app.storage.storyboard_store import (
    create_shot,
    create_storyboard,
    delete_shot,
    delete_storyboard,
    get_shot,
    get_storyboard,
    list_shots,
    list_storyboards,
    save_shot,
)


router = APIRouter(prefix="/api/storyboards", tags=["storyboards"])


class CreateStoryboardRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    episode_id: str = Field(min_length=1, max_length=32)


class CreateShotRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    scene_id: str = Field(min_length=1, max_length=120)
    shot_payload: dict[str, Any] = Field(default_factory=dict)


class SaveShotRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    shot_data: dict[str, Any]


class AssembleShotPackageRequest(BaseModel):
    series_slug: str = Field(min_length=1)


@router.get("")
async def list_storyboards_api(series_slug: str = Query(min_length=1)):
    return {"items": list_storyboards(series_slug.strip())}


@router.post("")
async def create_storyboard_api(payload: CreateStoryboardRequest):
    try:
        item = create_storyboard(payload.series_slug.strip(), payload.episode_id.strip())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="系列不存在") from exc
    return {"item": item}


@router.get("/{storyboard_id}")
async def get_storyboard_api(storyboard_id: str, series_slug: str = Query(min_length=1)):
    item = get_storyboard(series_slug.strip(), storyboard_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="分镜板不存在")
    return {"item": item}


@router.delete("/{storyboard_id}")
async def delete_storyboard_api(storyboard_id: str, series_slug: str = Query(min_length=1)):
    try:
        delete_storyboard(series_slug.strip(), storyboard_id.strip())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="分镜板不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/{storyboard_id}/shots")
async def list_shots_api(storyboard_id: str, series_slug: str = Query(min_length=1)):
    return {"items": list_shots(series_slug.strip(), storyboard_id.strip())}


@router.post("/{storyboard_id}/shots")
async def create_shot_api(storyboard_id: str, payload: CreateShotRequest):
    try:
        item = create_shot(
            series_slug=payload.series_slug.strip(),
            storyboard_id=storyboard_id.strip(),
            scene_id=payload.scene_id.strip(),
            shot_payload=payload.shot_payload,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="分镜板不存在") from exc
    return {"item": item}


@router.get("/{storyboard_id}/shots/{shot_id}")
async def get_shot_api(storyboard_id: str, shot_id: str, series_slug: str = Query(min_length=1)):
    item = get_shot(series_slug.strip(), storyboard_id.strip(), shot_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="镜头不存在")
    return {"item": item}


@router.put("/{storyboard_id}/shots/{shot_id}")
async def save_shot_api(storyboard_id: str, shot_id: str, payload: SaveShotRequest):
    try:
        item = save_shot(
            series_slug=payload.series_slug.strip(),
            storyboard_id=storyboard_id.strip(),
            shot_id=shot_id.strip(),
            shot_data=payload.shot_data,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="镜头不存在") from exc
    return {"item": item}


@router.delete("/{storyboard_id}/shots/{shot_id}")
async def delete_shot_api(storyboard_id: str, shot_id: str, series_slug: str = Query(min_length=1)):
    try:
        delete_shot(
            series_slug=series_slug.strip(),
            storyboard_id=storyboard_id.strip(),
            shot_id=shot_id.strip(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="镜头不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/{storyboard_id}/shots/{shot_id}/assemble-package")
async def assemble_shot_package_api(storyboard_id: str, shot_id: str, payload: AssembleShotPackageRequest):
    try:
        item = assemble_shot_prompt_package(
            series_slug=payload.series_slug.strip(),
            storyboard_id=storyboard_id.strip(),
            shot_id=shot_id.strip(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="镜头来源数据不存在") from exc
    return {"item": item}
