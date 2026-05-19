from typing import Any

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.services.character_generation import ImageProviderError, generate_character_assets
from app.storage.character_store import (
    create_character,
    get_character,
    get_character_bible,
    get_character_source_uploads_dir,
    list_characters,
    save_character_bible,
    save_character_source_images,
)
from app.storage.common import relative_to_series_root, utc_now_iso, write_bytes_atomic
from app.storage.series_store import get_series_path


router = APIRouter(prefix="/api/characters", tags=["characters"])


class CreateCharacterRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    brief: str = Field(default="", max_length=2000)


class SaveCharacterBibleRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    bible_data: dict[str, Any]


class GenerateCharacterAssetsRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    episode_ids: list[str] = Field(default_factory=list)
    generation_mode: str = Field(default="reference_plus_text")


@router.get("")
async def list_characters_api(series_slug: str = Query(min_length=1)):
    return {"items": list_characters(series_slug.strip())}


@router.post("")
async def create_character_api(payload: CreateCharacterRequest):
    try:
        item = create_character(
            series_slug=payload.series_slug.strip(),
            name=payload.name.strip(),
            brief=payload.brief.strip(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Series not found") from exc
    return {"item": item}


@router.get("/{character_id}")
async def get_character_api(character_id: str, series_slug: str = Query(min_length=1)):
    item = get_character(series_slug.strip(), character_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"item": item}


@router.get("/{character_id}/bible")
async def get_character_bible_api(character_id: str, series_slug: str = Query(min_length=1)):
    item = get_character(series_slug.strip(), character_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"item": get_character_bible(series_slug.strip(), character_id.strip())}


@router.put("/{character_id}/bible")
async def save_character_bible_api(character_id: str, payload: SaveCharacterBibleRequest):
    try:
        item = save_character_bible(
            series_slug=payload.series_slug.strip(),
            character_id=character_id.strip(),
            bible_data=payload.bible_data,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Character not found") from exc
    return {"item": item}


@router.post("/{character_id}/generate-assets")
async def generate_character_assets_api(character_id: str, payload: GenerateCharacterAssetsRequest):
    try:
        result = generate_character_assets(
            series_slug=payload.series_slug.strip(),
            character_id=character_id.strip(),
            episode_ids=[item.strip() for item in payload.episode_ids if item.strip()],
            generation_mode=payload.generation_mode.strip(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Character not found") from exc
    except ImageProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/{character_id}/source-images")
async def upload_character_source_images_api(
    character_id: str,
    series_slug: str = Form(min_length=1),
    files: list[UploadFile] = File(...),
):
    normalized_series_slug = series_slug.strip()
    normalized_character_id = character_id.strip()
    character = get_character(normalized_series_slug, normalized_character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    series_root = get_series_path(normalized_series_slug)
    upload_dir = get_character_source_uploads_dir(normalized_series_slug, normalized_character_id)
    source_images = list(character.get("source_images") or [])

    for index, file in enumerate(files, start=1):
        payload = await file.read()
        if not payload:
            continue

        suffix = Path(file.filename or f"source_{index}.png").suffix.lower() or ".png"
        stored_name = f"source_{utc_now_iso().replace(':', '').replace('-', '').replace('T', '_').replace('Z', '')}_{index:02d}{suffix}"
        absolute_path = upload_dir / stored_name
        write_bytes_atomic(absolute_path, payload)
        source_images.append(
            {
                "path": relative_to_series_root(absolute_path, series_root),
                "original_name": file.filename or stored_name,
                "content_type": file.content_type or "",
                "uploaded_at": utc_now_iso(),
            }
        )

    manifest = save_character_source_images(normalized_series_slug, normalized_character_id, source_images)
    return {
        "item": manifest,
        "source_images": source_images,
    }
