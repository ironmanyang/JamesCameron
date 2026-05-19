from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.storage.series_store import create_series, get_series, list_series


router = APIRouter(prefix="/api/series", tags=["series"])


class CreateSeriesRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


@router.get("")
async def list_series_api():
    return {"items": list_series()}


@router.post("")
async def create_series_api(payload: CreateSeriesRequest):
    try:
        series = create_series(payload.name.strip(), payload.description.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": series}


@router.get("/{series_slug}")
async def get_series_api(series_slug: str):
    item = get_series(series_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Series not found")
    return {"item": item}

