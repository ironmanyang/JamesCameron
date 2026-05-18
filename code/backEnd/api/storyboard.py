from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from utils.file_ops import get_series_dir, save_json, load_json

router = APIRouter(prefix="/api/storyboard", tags=["storyboard"])


class ShotConfig(BaseModel):
    aspect_ratio: str = "16:9"
    style: str = "写实"
    resolution: str = "1080p"
    shot_size: str = "中景"
    angle: str = "平视"
    movement: str = "固定"
    lighting: str = "自然光"
    color_tone: str = "暖色"
    pace: str = "正常叙事"
    duration: float = 5.0


class StoryboardShot(BaseModel):
    shot_id: int
    description: str = ""
    characters: List[str] = []
    location: str = ""
    config: Optional[ShotConfig] = None


class StoryboardRequest(BaseModel):
    shots: List[Dict[str, Any]]


@router.get("/{series_name}/{ep}")
async def get_storyboard(series_name: str, ep: int = 1):
    try:
        if not series_name:
            raise ValueError("系列名称不能为空")

        storyboard_path = get_series_dir(series_name) / "storyboards" / f"ep{ep}_storyboard.json"

        if not storyboard_path.exists():
            return {"shots": []}

        data = load_json(storyboard_path)
        return {"shots": data.get("shots", [])}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{series_name}/{ep}")
async def save_storyboard(series_name: str, ep: int = 1, shots: List[Dict[str, Any]] = None):
    try:
        if not series_name:
            raise ValueError("系列名称不能为空")

        if shots is None:
            raise ValueError("shots 参数不能为空")

        storyboard_dir = get_series_dir(series_name) / "storyboards"
        storyboard_dir.mkdir(parents=True, exist_ok=True)

        storyboard_path = storyboard_dir / f"ep{ep}_storyboard.json"

        storyboard_data = {
            "series_name": series_name,
            "episode": ep,
            "shots": shots
        }

        save_json(storyboard_path, storyboard_data)

        return {
            "success": True,
            "message": f"分镜配置已保存到 ep{ep}",
            "path": str(storyboard_path)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/script/{series_name}/{ep}")
async def get_script_shots(series_name: str, ep: int = 1):
    try:
        if not series_name:
            raise ValueError("系列名称不能为空")

        script_path = get_series_dir(series_name) / "scripts" / f"ep{ep}_script.json"

        if not script_path.exists():
            return {"shots": []}

        script_data = load_json(script_path)

        shots = []
        for scene in script_data.get("scenes", []):
            scene_location = scene.get("location", "")
            scene_time = scene.get("time", "")
            for shot in scene.get("shots", []):
                shots.append({
                    "shot_id": shot.get("shot_id", 0),
                    "description": shot.get("description", ""),
                    "characters": shot.get("characters", []),
                    "location": scene_location,
                    "time": scene_time,
                    "emotion": shot.get("emotion", "")
                })

        return {"shots": shots}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
