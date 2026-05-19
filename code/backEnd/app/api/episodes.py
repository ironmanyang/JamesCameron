from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.deepseek import analyze_script_with_deepseek
from app.storage.episode_store import (
    create_episode,
    get_episode,
    load_parsed_script,
    load_raw_script,
    list_episodes,
    save_parsed_script,
    save_raw_script,
)


router = APIRouter(prefix="/api/episodes", tags=["episodes"])


class CreateEpisodeRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    name: str = Field(default="", max_length=120)
    episode_number: int | None = Field(default=None, ge=1, le=999)


class SaveRawScriptRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    raw_text: str


class SaveParsedScriptRequest(BaseModel):
    series_slug: str = Field(min_length=1)
    parsed_script: dict[str, Any]


class AnalyzeScriptRequest(BaseModel):
    series_slug: str = Field(min_length=1)


@router.get("")
async def list_episodes_api(series_slug: str = Query(min_length=1)):
    return {"items": list_episodes(series_slug.strip())}


@router.post("")
async def create_episode_api(payload: CreateEpisodeRequest):
    try:
        item = create_episode(
            series_slug=payload.series_slug.strip(),
            name=payload.name.strip(),
            episode_number=payload.episode_number,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Series not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item}


@router.get("/{episode_id}")
async def get_episode_api(episode_id: str, series_slug: str = Query(min_length=1)):
    item = get_episode(series_slug.strip(), episode_id.strip())
    if item is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {"item": item}


@router.get("/{episode_id}/raw-script")
async def get_raw_script_api(episode_id: str, series_slug: str = Query(min_length=1)):
    try:
        content = load_raw_script(series_slug.strip(), episode_id.strip())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    return {"content": content}


@router.get("/{episode_id}/parsed-script")
async def get_parsed_script_api(episode_id: str, series_slug: str = Query(min_length=1)):
    try:
        content = load_parsed_script(series_slug.strip(), episode_id.strip())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    return {"content": content}


@router.put("/{episode_id}/raw-script")
async def save_raw_script_api(episode_id: str, payload: SaveRawScriptRequest):
    try:
        item = save_raw_script(
            series_slug=payload.series_slug.strip(),
            episode_id=episode_id.strip(),
            raw_text=payload.raw_text,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    return {"item": item}


@router.put("/{episode_id}/parsed-script")
async def save_parsed_script_api(episode_id: str, payload: SaveParsedScriptRequest):
    try:
        item = save_parsed_script(
            series_slug=payload.series_slug.strip(),
            episode_id=episode_id.strip(),
            parsed_script=payload.parsed_script,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    return {"item": item}


@router.post("/{episode_id}/analyze-script")
async def analyze_script_api(episode_id: str, payload: AnalyzeScriptRequest):
    try:
        series_slug = payload.series_slug.strip()
        normalized_episode_id = episode_id.strip()
        episode = get_episode(series_slug, normalized_episode_id)
        if episode is None:
            raise FileNotFoundError(normalized_episode_id)

        raw_text = load_raw_script(series_slug, normalized_episode_id).strip()
        if not raw_text:
            raise ValueError("Raw script is empty")

        parsed_script = analyze_script_with_deepseek(
            raw_text=raw_text,
            episode_id=normalized_episode_id,
            episode_name=episode.get("name", normalized_episode_id),
        )
        item = save_parsed_script(
            series_slug=series_slug,
            episode_id=normalized_episode_id,
            parsed_script=parsed_script,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Episode not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": item, "parsed_script": parsed_script}
