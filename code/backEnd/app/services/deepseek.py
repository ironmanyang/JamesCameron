import json
import os
import re
from typing import Any

import requests


SYSTEM_PROMPT = """
你是影视剧本拆解助手。你的任务是把用户提供的中文剧本文本，拆解成严格合法的 JSON。
要求：
1. 只输出 JSON，不要输出解释、标题、Markdown、代码块。
2. 场景、镜头、对白、角色、情绪、镜头语言都要尽量结构化。
3. 如果原文信息不足，可以合理补足，但不要过度发散。
4. 角色名称尽量统一。
5. 输出字段必须稳定，便于程序直接保存。
"""


USER_PROMPT_TEMPLATE = """
请把下面的剧本拆解成 JSON，目标结构如下：

{{
  "title": "剧集标题",
  "acts": [],
  "scenes": [
    {{
      "scene_id": 1,
      "location": "场景地点",
      "time": "时间",
      "summary": "该场景摘要",
      "shots": [
        {{
          "shot_id": 1,
          "description": "镜头画面描述",
          "camera": {{
            "angle": "机位角度",
            "movement": "运镜方式",
            "shot_size": "景别"
          }},
          "dialogues": [
            {{
              "character": "角色名",
              "text": "对白"
            }}
          ],
          "characters": ["角色A", "角色B"],
          "emotion": "核心情绪",
          "beat": "剧情动作节拍"
        }}
      ]
    }}
  ],
  "extracted_entities": {{
    "characters": [],
    "scenes": [],
    "props": []
  }}
}}

补充要求：
- scene_id 和 shot_id 从 1 开始编号
- acts 没有时返回空数组
- extracted_entities.characters 要汇总去重后的角色名
- extracted_entities.scenes 要汇总去重后的场景地点
- extracted_entities.props 要尽量提取重要道具
剧集标题：{episode_name}

剧本文本：
{raw_text}
"""


def _strip_code_fences(content: str) -> str:
    content = content.strip()
    content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    return content.strip()


def _extract_json_block(content: str) -> str:
    content = _strip_code_fences(content)
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if match:
        candidate = match.group(0).strip()
        json.loads(candidate)
        return candidate

    return content


def _join_display(values: list[str], sep: str = "；") -> str:
    return sep.join([str(item).strip() for item in values if str(item).strip()])


def _dialogue_readable(dialogues: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in dialogues or []:
        character = str(item.get("character", "")).strip()
        text = str(item.get("text", "")).strip()
        if character and text:
            lines.append(f"{character}：{text}")
        elif text:
            lines.append(text)
    return " / ".join(lines)


def _normalize_parsed_script(payload: dict[str, Any], episode_id: str, episode_name: str) -> dict[str, Any]:
    title = payload.get("title") or episode_name
    acts = payload.get("acts") or []
    scenes = payload.get("scenes") or []
    extracted = payload.get("extracted_entities") or {}

    character_names: list[str] = []
    scene_names: list[str] = []
    props = extracted.get("props") or []

    normalized_scenes = []
    for scene_index, scene in enumerate(scenes, start=1):
        location = scene.get("location", "")
        time = scene.get("time", "")
        summary = scene.get("summary", "")
        shots = scene.get("shots") or []

        if location and location not in scene_names:
            scene_names.append(location)

        normalized_shots = []
        for shot_index, shot in enumerate(shots, start=1):
            shot_characters = shot.get("characters") or []
            for name in shot_characters:
                if name and name not in character_names:
                    character_names.append(name)

            dialogues = shot.get("dialogues") or []
            for dialogue in dialogues:
                speaker = dialogue.get("character", "")
                if speaker and speaker not in character_names:
                    character_names.append(speaker)

            camera = shot.get("camera") or {}
            angle = camera.get("angle", "")
            movement = camera.get("movement", "")
            shot_size = camera.get("shot_size", "")
            description = shot.get("description", "")
            emotion = shot.get("emotion", "")
            beat = shot.get("beat", "")
            dialogue_summary = _dialogue_readable(dialogues)

            normalized_shots.append(
                {
                    "shot_id": shot.get("shot_id", shot_index),
                    "description": description,
                    "camera": {
                        "angle": angle,
                        "movement": movement,
                        "shot_size": shot_size,
                        "readable": {
                            "机位角度": angle,
                            "运镜方式": movement,
                            "景别": shot_size,
                        },
                        "summary": "；".join(
                            [
                                item
                                for item in [
                                    angle and f"机位角度：{angle}",
                                    movement and f"运镜方式：{movement}",
                                    shot_size and f"景别：{shot_size}",
                                ]
                                if item
                            ]
                        ),
                    },
                    "dialogues": dialogues,
                    "characters": shot_characters,
                    "emotion": emotion,
                    "beat": beat,
                    "readable": {
                        "镜头编号": shot.get("shot_id", shot_index),
                        "画面描述": description,
                        "镜头信息": _join_display(
                            [
                                angle and f"机位角度：{angle}",
                                movement and f"运镜方式：{movement}",
                                shot_size and f"景别：{shot_size}",
                            ]
                        ),
                        "出场角色": "、".join(shot_characters),
                        "对白": dialogue_summary,
                        "情绪": emotion,
                        "剧情节拍": beat,
                    },
                    "summary": _join_display(
                        [
                            description and f"画面：{description}",
                            shot_characters and f"角色：{'、'.join(shot_characters)}",
                            dialogue_summary and f"对白：{dialogue_summary}",
                            emotion and f"情绪：{emotion}",
                            beat and f"节拍：{beat}",
                        ]
                    ),
                }
            )

        scene_readable_shots = [
            {
                "镜头编号": shot.get("shot_id", ""),
                "一句话": shot.get("summary", ""),
            }
            for shot in normalized_shots
        ]
        normalized_scenes.append(
            {
                "scene_id": scene.get("scene_id", scene_index),
                "location": location,
                "time": time,
                "summary": summary,
                "shots": normalized_shots,
                "readable": {
                    "场景编号": scene.get("scene_id", scene_index),
                    "场景地点": location,
                    "时间": time,
                    "场景摘要": summary,
                    "镜头数": len(normalized_shots),
                    "镜头导读": scene_readable_shots,
                },
            }
        )

    readable_outline = [
        {
            "场景编号": scene.get("scene_id", ""),
            "场景地点": scene.get("location", ""),
            "时间": scene.get("time", ""),
            "场景摘要": scene.get("summary", ""),
            "镜头数": len(scene.get("shots") or []),
        }
        for scene in normalized_scenes
    ]

    return {
        "episode_id": episode_id,
        "title": title,
        "acts": acts,
        "scenes": normalized_scenes,
        "extracted_entities": {
            "characters": extracted.get("characters") or character_names,
            "scenes": extracted.get("scenes") or scene_names,
            "props": props,
            "readable": {
                "角色": extracted.get("characters") or character_names,
                "场景": extracted.get("scenes") or scene_names,
                "道具": props,
            },
        },
        "readable_outline": {
            "剧集标题": title,
            "场景总数": len(normalized_scenes),
            "角色总览": extracted.get("characters") or character_names,
            "场景导读": readable_outline,
        },
    }


def analyze_script_with_deepseek(raw_text: str, episode_id: str, episode_name: str) -> dict[str, Any]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("缺少 DEEPSEEK_API_KEY 配置")

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://www.packyapi.com/v1").rstrip("/")
    model = os.getenv("DEEPSEEK_SCRIPT_MODEL", "deepseek-v4-pro")

    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0.2,
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        episode_name=episode_name,
                        raw_text=raw_text.strip(),
                    ).strip(),
                },
            ],
        },
        timeout=180,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ValueError(f"DeepSeek 请求失败：{response.text}") from exc

    payload = response.json()
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not content:
        raise ValueError("DeepSeek 返回内容为空")

    try:
        parsed = json.loads(_extract_json_block(content))
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek JSON 解析失败：{content}") from exc

    return _normalize_parsed_script(parsed, episode_id=episode_id, episode_name=episode_name)
