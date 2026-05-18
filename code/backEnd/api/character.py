from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from utils.ai_clients import (
    generate_character_bible,
    generate_character_images,
    extract_character_context_from_script,
    load_json
)
from utils.file_ops import get_series_dir, save_json

router = APIRouter(prefix="/api/character", tags=["character"])


class GenerateBibleRequest(BaseModel):
    series_name: str
    character_name: str
    brief_description: str = ""


class RegenerateImageRequest(BaseModel):
    series_name: str
    character_name: str
    image_type: str


@router.post("/generate-bible")
async def generate_character_bible_api(req: GenerateBibleRequest):
    try:
        series_name = req.series_name.strip()
        character_name = req.character_name.strip()

        if not series_name or not character_name:
            raise ValueError("系列名称和角色名称不能为空")

        script_path = get_series_dir(series_name) / "scripts" / "ep1_script.json"
        series_context = extract_character_context_from_script(script_path, character_name)

        bible_data = generate_character_bible(character_name, series_context, req.brief_description)

        character_dir = get_series_dir(series_name) / "characters" / character_name
        character_dir.mkdir(parents=True, exist_ok=True)

        bible_path = character_dir / "character_bible.json"
        save_json(bible_path, bible_data)

        visual_prompts = bible_data.get("visual_prompts", {})
        if visual_prompts:
            image_paths = generate_character_images(visual_prompts, str(character_dir))
            bible_data["image_paths"] = image_paths
            save_json(bible_path, bible_data)

        return {
            "success": True,
            "message": f"角色 '{character_name}' 圣经生成成功",
            "data": bible_data,
            "path": str(bible_path)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate-image")
async def regenerate_character_image(req: RegenerateImageRequest):
    try:
        series_name = req.series_name.strip()
        character_name = req.character_name.strip()
        image_type = req.image_type.strip()

        valid_types = ["front_view", "side_view", "back_view", "decomposition_sheet"]
        if image_type not in valid_types:
            raise ValueError(f"无效的图片类型。可选值: {valid_types}")

        character_dir = get_series_dir(series_name) / "characters" / character_name
        bible_path = character_dir / "character_bible.json"

        if not bible_path.exists():
            raise ValueError("角色圣经不存在，请先生成圣经")

        bible_data = load_json(bible_path)
        visual_prompts = bible_data.get("visual_prompts", {})

        if image_type not in visual_prompts:
            raise ValueError(f"角色圣经中不存在 {image_type} 的提示词")

        prompt = visual_prompts[image_type]
        image_paths = generate_character_images({image_type: prompt}, str(character_dir))

        bible_data["image_paths"] = bible_data.get("image_paths", {})
        bible_data["image_paths"][image_type] = image_paths[image_type]
        save_json(bible_path, bible_data)

        return {
            "success": True,
            "message": f"{image_type} 重新生成成功",
            "image_path": image_paths[image_type]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_characters(series_name: str):
    try:
        if not series_name:
            raise ValueError("系列名称不能为空")

        character_dir = get_series_dir(series_name) / "characters"

        if not character_dir.exists():
            return {"characters": []}

        characters = []
        for char_folder in character_dir.iterdir():
            if char_folder.is_dir():
                bible_path = char_folder / "character_bible.json"
                image_paths = {}
                if bible_path.exists():
                    bible_data = load_json(bible_path)
                    image_paths = bible_data.get("image_paths", {})

                characters.append({
                    "name": char_folder.name,
                    "front_view": image_paths.get("front_view", ""),
                    "has_bible": bible_path.exists()
                })

        return {"characters": characters}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bible")
async def get_character_bible(series_name: str, character_name: str):
    try:
        if not series_name or not character_name:
            raise ValueError("系列名称和角色名称不能为空")

        bible_path = get_series_dir(series_name) / "characters" / character_name / "character_bible.json"

        if not bible_path.exists():
            raise ValueError("角色圣经不存在")

        bible_data = load_json(bible_path)
        return {"success": True, "data": bible_data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/save-bible")
async def save_character_bible(series_name: str, character_name: str, bible_data: dict):
    try:
        if not series_name or not character_name:
            raise ValueError("系列名称和角色名称不能为空")

        character_dir = get_series_dir(series_name) / "characters" / character_name
        character_dir.mkdir(parents=True, exist_ok=True)

        bible_path = character_dir / "character_bible.json"
        save_json(bible_path, bible_data)

        return {"success": True, "message": "角色圣经保存成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
