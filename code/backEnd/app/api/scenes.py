from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.scene_generation import generate_scene_assets
from app.storage.scene_store import (
    create_scene,
    get_scene,
    get_scene_prompt_package,
    list_scenes,
    save_scene_manifest,
)


router = APIRouter(prefix="/api/scenes", tags=["scenes"])


class CreateSceneRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=4000)
    episode_id: str = Field(default="", max_length=32)


class SaveSceneRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    scene_data: dict[str, Any]


class GenerateSceneAssetsRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    episode_ids: list[str] = Field(default_factory=list)


@router.get("")
async def list_scenes_api(series_slug: str = Query(min_length=1)):
    return {"items": list_scenes(series_slug.strip())}


@router.post("")
async def create_scene_api(payload: CreateSceneRequest):
    try:
        item = create_scene(
            series_slug=payload.series_slug.strip(),
            name=payload.name.strip(),
            description=payload.description.strip(),
            episode_id=payload.episode_id.strip(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Series not found") from exc
    return {"item": item}


@router.get("/{scene_id}")
async def get_scene_api(scene_id: str, series_slug: str = Query(min_length=1)):
    item = get_scene(series_slug.strip(), scene_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"item": item}


@router.get("/{scene_id}/prompt-package")
async def get_scene_prompt_package_api(scene_id: str, series_slug: str = Query(min_length=1)):
    item = get_scene(series_slug.strip(), scene_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"item": get_scene_prompt_package(series_slug.strip(), scene_id.strip())}


@router.put("/{scene_id}")
async def save_scene_api(scene_id: str, payload: SaveSceneRequest):
    try:
        item = save_scene_manifest(
            series_slug=payload.series_slug.strip(),
            scene_id=scene_id.strip(),
            scene_data=payload.scene_data,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Scene not found") from exc
    return {"item": item}


@router.post("/{scene_id}/generate-assets")
async def generate_scene_assets_api(scene_id: str, payload: GenerateSceneAssetsRequest):
    try:
        result = generate_scene_assets(
            series_slug=payload.series_slug.strip(),
            scene_id=scene_id.strip(),
            episode_ids=[item.strip() for item in payload.episode_ids if item.strip()],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Scene not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result
