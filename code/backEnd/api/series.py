from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.file_ops import get_series_dir, save_json, list_series

router = APIRouter(prefix="/api/series", tags=["series"])


class SeriesCreateRequest(BaseModel):
    name: str


class SeriesCreateResponse(BaseModel):
    success: bool
    message: str


class SeriesListResponse(BaseModel):
    series_list: list


@router.get("", response_model=SeriesListResponse)
async def get_series_list():
    try:
        series = list_series()
        return {"series_list": series}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SeriesCreateResponse)
async def create_series(req: SeriesCreateRequest):
    try:
        series_name = req.name.strip()
        if not series_name:
            raise ValueError("系列名称不能为空")

        series_dir = get_series_dir(series_name)
        if series_dir.exists():
            return SeriesCreateResponse(
                success=False,
                message=f"系列 '{series_name}' 已存在"
            )

        manifest = {
            "series_name": series_name,
            "created_at": datetime.now().isoformat()
        }
        manifest_path = series_dir / "manifest.json"
        save_json(manifest_path, manifest)

        return SeriesCreateResponse(
            success=True,
            message=f"系列 '{series_name}' 创建成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))