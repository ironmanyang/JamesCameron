from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.services.scene_video_assembly import assemble_scene_direct_package
from app.services.shot_assembly import assemble_shot_prompt_package
from app.storage.common import relative_to_series_root, utc_now_iso, write_bytes_atomic
from app.storage.series_store import get_series_path
from app.storage.storyboard_store import (
    create_shot,
    create_storyboard,
    delete_shot,
    delete_storyboard,
    get_shot,
    get_shot_media_uploads_dir,
    get_storyboard,
    get_storyboard_draft_shot_media_dir,
    list_shots,
    list_storyboards,
    save_storyboard,
    save_shot,
)


router = APIRouter(prefix="/api/storyboards", tags=["storyboards"])


class CreateStoryboardRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    episode_id: str = Field(min_length=1, max_length=32)
    production_mode: str = Field(default="shot_pipeline", max_length=32)


class SaveStoryboardRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    storyboard_data: dict[str, Any]


class CreateShotRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    scene_id: str = Field(min_length=1, max_length=120)
    shot_payload: dict[str, Any] = Field(default_factory=dict)


class SaveShotRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    shot_data: dict[str, Any]


class AssembleShotPackageRequest(BaseModel):
    series_slug: str = Field(min_length=1)


class AssembleScenePackageRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    scene_id: str = Field(min_length=1, max_length=120)
    scene_payload: dict[str, Any] = Field(default_factory=dict)


SHOT_IMAGE_UPLOAD_TARGETS = {"first_frame", "last_frame", "reference_images"}


@router.get("")
async def list_storyboards_api(series_slug: str = Query(min_length=1)):
    return {"items": list_storyboards(series_slug.strip())}


@router.post("")
async def create_storyboard_api(payload: CreateStoryboardRequest):
    try:
        item = create_storyboard(
            payload.series_slug.strip(),
            payload.episode_id.strip(),
            payload.production_mode.strip(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="系列不存在") from exc
    return {"item": item}


@router.post("/{storyboard_id}/shot-media-images")
async def upload_shot_media_images_api(
    storyboard_id: str,
    series_slug: str = Form(min_length=1),
    target: str = Form(min_length=1),
    shot_id: str = Form(default=""),
    files: list[UploadFile] = File(...),
):
    normalized_series_slug = series_slug.strip()
    normalized_storyboard_id = storyboard_id.strip()
    normalized_target = target.strip()
    normalized_shot_id = shot_id.strip()

    storyboard = get_storyboard(normalized_series_slug, normalized_storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="鍒嗛暅鏉夸笉瀛樺湪")

    if normalized_target not in SHOT_IMAGE_UPLOAD_TARGETS:
        raise HTTPException(status_code=400, detail="涓嶆敮鎸佺殑闀滃ご鍥剧墖涓婁紶绫诲瀷")

    if not files:
        raise HTTPException(status_code=400, detail="鏈笂浼犱换浣曟枃浠?")

    if normalized_shot_id:
        shot = get_shot(normalized_series_slug, normalized_storyboard_id, normalized_shot_id)
        if shot is None:
            raise HTTPException(status_code=404, detail="闀滃ご涓嶅瓨鍦?")
        upload_dir = get_shot_media_uploads_dir(normalized_series_slug, normalized_storyboard_id, normalized_shot_id)
    else:
        upload_dir = get_storyboard_draft_shot_media_dir(normalized_series_slug, normalized_storyboard_id)

    series_root = get_series_path(normalized_series_slug)
    uploaded_items: list[dict[str, str]] = []
    timestamp = utc_now_iso().replace(":", "").replace("-", "").replace("T", "_").replace("Z", "")

    for index, file in enumerate(files, start=1):
        payload = await file.read()
        if not payload:
            continue

        suffix = Path(file.filename or f"{normalized_target}_{index}.png").suffix.lower() or ".png"
        stored_name = f"{normalized_target}_{timestamp}_{index:02d}{suffix}"
        absolute_path = upload_dir / stored_name
        write_bytes_atomic(absolute_path, payload)
        uploaded_items.append(
            {
                "path": relative_to_series_root(absolute_path, series_root),
                "original_name": file.filename or stored_name,
                "content_type": file.content_type or "",
            }
        )

    if not uploaded_items:
        raise HTTPException(status_code=400, detail="涓婁紶鏂囦欢涓虹┖")

    return {
        "items": uploaded_items,
        "target": normalized_target,
        "shot_id": normalized_shot_id,
    }


@router.get("/{storyboard_id}")
async def get_storyboard_api(storyboard_id: str, series_slug: str = Query(min_length=1)):
    item = get_storyboard(series_slug.strip(), storyboard_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="分镜板不存在")
    return {"item": item}


@router.put("/{storyboard_id}")
async def save_storyboard_api(storyboard_id: str, payload: SaveStoryboardRequest):
    try:
        item = save_storyboard(
            series_slug=payload.series_slug.strip(),
            storyboard_id=storyboard_id.strip(),
            storyboard_data=payload.storyboard_data,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="分镜板不存在") from exc
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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@router.post("/{storyboard_id}/assemble-scene-package")
async def assemble_scene_package_api(storyboard_id: str, payload: AssembleScenePackageRequest):
    try:
        item = assemble_scene_direct_package(
            series_slug=payload.series_slug.strip(),
            storyboard_id=storyboard_id.strip(),
            scene_id=payload.scene_id.strip(),
            scene_payload=payload.scene_payload,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="场景来源数据不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}
