from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from utils.ai_clients import analyze_script_with_deepseek
from utils.file_ops import get_series_dir, save_json

router = APIRouter(prefix="/api/script", tags=["script"])


class ScriptAnalyzeRequest(BaseModel):
    series_name: str
    raw_text: str


@router.post("/analyze")
async def analyze_script(req: ScriptAnalyzeRequest):
    try:
        series_name = req.series_name.strip()
        if not series_name:
            raise ValueError("系列名称不能为空")
        if not req.raw_text.strip():
            raise ValueError("剧本内容不能为空")

        result = analyze_script_with_deepseek(req.raw_text)

        series_dir = get_series_dir(series_name)
        scripts_dir = series_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        script_path = scripts_dir / "ep1_script.json"
        save_json(script_path, result)

        return {
            "success": True,
            "message": "剧本拆解成功",
            "data": result,
            "path": str(script_path)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
