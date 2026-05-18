from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
from utils.ai_clients import generate_character_images
from utils.file_ops import get_series_dir, save_json, load_json

router = APIRouter(prefix="/api/scene", tags=["scene"])


STYLE_PROMPT = "写实风格，低饱和度，暖色调，电影感"

VIEW_PROMPTS = {
    "establishing": "A wide establishing shot of {scene_name}, {style}. Cinematic composition, epic scale, golden hour lighting.",
    "closeup": "A close-up detail shot of {scene_name}, {style}. Intimate framing, shallow depth of field, textured surfaces.",
    "bird": "A bird's eye view of {scene_name}, {style}. Overhead perspective, pattern recognition, architectural clarity.",
    "detail": "An extra angle detail shot of {scene_name}, {style}. Dramatic lighting, moody atmosphere, cinematic quality."
}


def build_scene_prompts(scene_name: str, description: str = "") -> dict:
    desc_part = f", {description}" if description else ""
    prompts = {}
    for view_key, template in VIEW_PROMPTS.items():
        prompts[view_key] = template.format(
            scene_name=f"{scene_name}{desc_part}",
            style=STYLE_PROMPT
        )
    return prompts


class GenerateSceneRequest(BaseModel):
    series_name: str
    scene_name: str
    description: str = ""


class RegenerateViewRequest(BaseModel):
    series_name: str
    scene_name: str
    view_type: str


@router.post("/generate")
async def generate_scene(req: GenerateSceneRequest):
    try:
        series_name = req.series_name.strip()
        scene_name = req.scene_name.strip()

        if not series_name or not scene_name:
            raise ValueError("系列名称和场景名称不能为空")

        prompts = build_scene_prompts(scene_name, req.description)

        scene_dir = get_series_dir(series_name) / "scenes" / scene_name
        scene_dir.mkdir(parents=True, exist_ok=True)

        image_paths = generate_character_images(prompts, str(scene_dir))

        view_descriptions = {
            "establishing": "定场镜头 - 展示场景全貌",
            "closeup": "特写镜头 - 聚焦场景细节",
            "bird": "俯视镜头 - 从上方观察",
            "detail": "额外角度 - 补充视角"
        }

        meta_data = {
            "scene_name": scene_name,
            "description": req.description,
            "images": {}
        }

        for view_key, filepath in image_paths.items():
            meta_data["images"][view_key] = {
                "path": filepath,
                "prompt": prompts[view_key],
                "description": view_descriptions.get(view_key, view_key)
            }

        meta_path = scene_dir / "scene_meta.json"
        save_json(meta_path, meta_data)

        return {
            "success": True,
            "message": f"场景 '{scene_name}' 生成成功",
            "data": meta_data,
            "path": str(meta_path)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate-view")
async def regenerate_scene_view(req: RegenerateViewRequest):
    try:
        series_name = req.series_name.strip()
        scene_name = req.scene_name.strip()
        view_type = req.view_type.strip()

        valid_views = ["establishing", "closeup", "bird", "detail"]
        if view_type not in valid_views:
            raise ValueError(f"无效的视角类型。可选值: {valid_views}")

        scene_dir = get_series_dir(series_name) / "scenes" / scene_name
        meta_path = scene_dir / "scene_meta.json"

        if not meta_path.exists():
            raise ValueError("场景元数据不存在，请先生成场景")

        meta_data = load_json(meta_path)
        scene_desc = meta_data.get("description", "")

        prompts = build_scene_prompts(scene_name, scene_desc)
        new_paths = generate_character_images({view_type: prompts[view_type]}, str(scene_dir))

        meta_data["images"][view_type]["path"] = new_paths[view_type]
        meta_data["images"][view_type]["prompt"] = prompts[view_type]
        save_json(meta_path, meta_data)

        return {
            "success": True,
            "message": f"{view_type} 重新生成成功",
            "image_path": new_paths[view_type]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_scenes(series_name: str):
    try:
        if not series_name:
            raise ValueError("系列名称不能为空")

        scenes_dir = get_series_dir(series_name) / "scenes"

        if not scenes_dir.exists():
            return {"scenes": []}

        scenes = []
        for scene_folder in scenes_dir.iterdir():
            if scene_folder.is_dir():
                meta_path = scene_folder / "scene_meta.json"
                thumbnail = ""
                if meta_path.exists():
                    meta_data = load_json(meta_path)
                    thumbnail = meta_data.get("images", {}).get("establishing", {}).get("path", "")

                scenes.append({
                    "name": scene_folder.name,
                    "thumbnail": thumbnail,
                    "has_meta": meta_path.exists()
                })

        return {"scenes": scenes}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta")
async def get_scene_meta(series_name: str, scene_name: str):
    try:
        if not series_name or not scene_name:
            raise ValueError("系列名称和场景名称不能为空")

        meta_path = get_series_dir(series_name) / "scenes" / scene_name / "scene_meta.json"

        if not meta_path.exists():
            raise ValueError("场景元数据不存在")

        meta_data = load_json(meta_path)
        return {"success": True, "data": meta_data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
