import asyncio
import time
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

from utils.file_ops import get_series_dir, save_json, load_json
from utils.prompt_builder import build_shot_prompt, get_character_for_shot, get_scene_for_location

router = APIRouter(prefix="/api/video", tags=["video"])


class GenerateRequest(BaseModel):
    series_name: str
    episode: int = 1
    shot_ids: Optional[List[int]] = None


class TaskStatus(BaseModel):
    task_id: str
    shot_id: int
    status: str
    prompt: str = ""
    output_path: str = ""
    error: str = ""
    created_at: str = ""
    completed_at: str = ""


def load_tasks(series_dir: Path) -> dict:
    tasks_file = series_dir / "tasks.json"
    if not tasks_file.exists():
        return {"tasks": [], "updated_at": ""}
    return load_json(tasks_file)


def save_tasks(series_dir: Path, tasks_data: dict):
    tasks_file = series_dir / "tasks.json"
    tasks_data["updated_at"] = datetime.now().isoformat()
    save_json(tasks_file, tasks_data)


def load_script_shots(series_dir: Path, episode: int) -> List[dict]:
    script_path = series_dir / "scripts" / f"ep{episode}_script.json"
    if not script_path.exists():
        return []

    script_data = load_json(script_path)
    shots = []
    for scene in script_data.get("scenes", []):
        for shot in scene.get("shots", []):
            shots.append({
                "shot_id": shot.get("shot_id"),
                "description": shot.get("description", ""),
                "characters": shot.get("characters", []),
                "location": scene.get("location", ""),
                "time": scene.get("time", ""),
                "emotion": shot.get("emotion", "")
            })
    return shots


def load_storyboard_config(series_dir: Path, episode: int) -> dict:
    config_path = series_dir / "storyboards" / f"ep{episode}_storyboard.json"
    if not config_path.exists():
        return {}

    config_data = load_json(config_path)
    config_map = {}
    for shot in config_data.get("shots", []):
        config_map[shot.get("shot_id")] = shot.get("config", {})
    return config_map


async def generate_video_for_shot(
    series_name: str,
    episode: int,
    shot_id: int,
    task_id: str,
    prompt: str
):
    series_dir = get_series_dir(series_name)
    tasks_data = load_tasks(series_dir)

    for task in tasks_data.get("tasks", []):
        if task.get("task_id") == task_id:
            task["status"] = "processing"
            break

    save_tasks(series_dir, tasks_data)

    try:
        await asyncio.sleep(5)

        output_dir = series_dir / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"ep{episode}_shot{shot_id}.mp4"

        with open(output_path, "w") as f:
            f.write(f"Mock video file for shot {shot_id}")

        tasks_data = load_tasks(series_dir)
        for task in tasks_data.get("tasks", []):
            if task.get("task_id") == task_id:
                task["status"] = "completed"
                task["output_path"] = str(output_path)
                task["completed_at"] = datetime.now().isoformat()
                break

        save_tasks(series_dir, tasks_data)

    except Exception as e:
        tasks_data = load_tasks(series_dir)
        for task in tasks_data.get("tasks", []):
            if task.get("task_id") == task_id:
                task["status"] = "failed"
                task["error"] = str(e)
                break
        save_tasks(series_dir, tasks_data)


@router.post("/generate")
async def generate_videos(
    req: GenerateRequest,
    background_tasks: BackgroundTasks
):
    try:
        series_name = req.series_name.strip()
        if not series_name:
            raise ValueError("系列名称不能为空")

        series_dir = get_series_dir(series_name)

        shots = load_script_shots(series_dir, req.episode)
        if not shots:
            raise ValueError("剧本中未找到分镜数据，请先生成剧本")

        storyboard_config = load_storyboard_config(series_dir, req.episode)

        if req.shot_ids:
            shots = [s for s in shots if s.get("shot_id") in req.shot_ids]
            if not shots:
                raise ValueError("未找到匹配的分镜")

        character_dir = series_dir / "characters"
        scenes_dir = series_dir / "scenes"

        tasks_data = load_tasks(series_dir)
        new_tasks = []

        for shot in shots:
            shot_id = shot.get("shot_id")
            config = storyboard_config.get(shot_id, {})

            character_bibles = get_character_for_shot(shot, character_dir)
            scene_info = get_scene_for_location(shot.get("location", ""), scenes_dir)

            prompt = build_shot_prompt(shot, character_bibles, scene_info, config)

            task_id = str(uuid.uuid4())

            task_entry = {
                "task_id": task_id,
                "shot_id": shot_id,
                "status": "pending",
                "prompt": prompt,
                "output_path": "",
                "error": "",
                "created_at": datetime.now().isoformat(),
                "completed_at": ""
            }

            new_tasks.append(task_entry)

            background_tasks.add_task(
                generate_video_for_shot,
                series_name,
                req.episode,
                shot_id,
                task_id,
                prompt
            )

        tasks_data["tasks"] = tasks_data.get("tasks", []) + new_tasks
        save_tasks(series_dir, tasks_data)

        return {
            "success": True,
            "message": f"已提交 {len(new_tasks)} 个生成任务",
            "task_count": len(new_tasks),
            "task_ids": [t["task_id"] for t in new_tasks]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{series_name}")
async def get_tasks(series_name: str):
    try:
        if not series_name:
            raise ValueError("系列名称不能为空")

        series_dir = get_series_dir(series_name)
        tasks_data = load_tasks(series_dir)

        return {
            "tasks": tasks_data.get("tasks", []),
            "updated_at": tasks_data.get("updated_at", "")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{series_name}")
async def clear_tasks(series_name: str):
    try:
        if not series_name:
            raise ValueError("系列名称不能为空")

        series_dir = get_series_dir(series_name)
        save_tasks(series_dir, {"tasks": [], "updated_at": datetime.now().isoformat()})

        return {"success": True, "message": "任务队列已清空"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
