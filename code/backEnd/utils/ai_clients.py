import json
import os
import re
from pathlib import Path
import requests
from openai import OpenAI
from utils.security import sanitize_text

SYSTEM_PROMPT = """你是一位资深影视编剧与分镜师。请严格将用户提供的剧本拆解为标准JSON，不要任何解释或Markdown标记。"""

USER_PROMPT_TEMPLATE = """请将以下剧本拆解为JSON，结构如下：

{{
  "series": "...",
  "episode": 1,
  "scenes": [
    {{
      "scene_id": 1,
      "location": "...",
      "time": "...",
      "shots": [
        {{
          "shot_id": 1,
          "description": "...",
          "camera": {{"angle": "...", "movement": "..."}},
          "dialogues": [{{"character":"...","text":"..."}}],
          "characters": ["..."],
          "emotion": "..."
        }}
      ]
    }}
  ]
}}

角色名统一用中文。暴力/血腥词汇改用温和暗示。description 30~80字。

剧本内容：{raw_text}"""

CHARACTER_BIBLE_SYSTEM_PROMPT = """你是顶级角色概念艺术家。根据输入信息生成角色圣经JSON。"""

CHARACTER_BIBLE_USER_TEMPLATE = """角色名：{name}
剧本背景：{series_context}
初始描述：{brief}
输出JSON：
{{
  "character_name": "...",
  "bible": {{
    "layer_1_biology": "种族、性别、年龄段、身高、体型",
    "layer_2_face": "脸型、眉形、眼型颜色、鼻型、唇形、发型发色、标记",
    "layer_3_costume": "服装风格、颜色、材质、配饰、武器",
    "layer_4_color_palette": "主色调、次级色调",
    "layer_5_texture": "皮肤质感、衣料材质",
    "layer_6_aura": "默认表情、气质、情绪范围"
  }},
  "visual_prompts": {{
    "front_view": "正面全身英文提示词，高质量，概念艺术风格",
    "side_view": "侧面全身英文提示词",
    "back_view": "背面全身英文提示词",
    "decomposition_sheet": "特征分解九宫格英文提示词，含面部特写、服装细节、饰品、典型姿势"
  }}
}}
所有visual_prompts必须用英文，详细准确。"""


def analyze_script_with_deepseek(raw_text: str) -> dict:
    safe_text = sanitize_text(raw_text)

    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1"
    )

    user_prompt = USER_PROMPT_TEMPLATE.format(raw_text=safe_text)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=4096
    )

    content = response.choices[0].message.content.strip()

    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nRaw content: {content}")

    return result


def generate_character_bible(character_name: str, series_context: str, brief: str) -> dict:
    client = OpenAI(
        api_key=os.getenv("GPT_IMAGE_API_KEY"),
        base_url=os.getenv("GPT_IMAGE_BASE_URL", "https://api.gpt-image.ai/v1")
    )

    user_prompt = CHARACTER_BIBLE_USER_TEMPLATE.format(
        name=character_name,
        series_context=series_context,
        brief=brief
    )

    response = client.chat.completions.create(
        model=os.getenv("GPT_IMAGE_MODEL", "gpt-image-2"),
        messages=[
            {"role": "system", "content": CHARACTER_BIBLE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=4096
    )

    content = response.choices[0].message.content.strip()

    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse character bible JSON: {e}\nRaw content: {content}")

    return result


def generate_character_images(prompts: dict, save_dir: str) -> dict:
    client = OpenAI(
        api_key=os.getenv("GPT_IMAGE_API_KEY"),
        base_url=os.getenv("GPT_IMAGE_BASE_URL", "https://api.gpt-image.ai/v1")
    )

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    image_types = ["front_view", "side_view", "back_view", "decomposition_sheet"]
    result_paths = {}

    for img_type in image_types:
        if img_type not in prompts:
            continue

        prompt = prompts[img_type]
        try:
            image_response = client.images.generate(
                prompt=prompt,
                size="1024x1024",
                model=os.getenv("GPT_IMAGE_MODEL", "gpt-image-2")
            )

            image_url = image_response.data[0].url

            img_data = requests.get(image_url).content
            filename = f"{img_type}.png"
            filepath = save_path / filename
            with open(filepath, "wb") as f:
                f.write(img_data)

            result_paths[img_type] = str(filepath)
        except Exception as e:
            raise ValueError(f"Failed to generate {img_type}: {str(e)}")

    return result_paths


def extract_character_context_from_script(script_path: Path, character_name: str) -> str:
    if not script_path.exists():
        return ""

    script_data = load_json(script_path)
    scenes = script_data.get("scenes", [])

    context_parts = []
    for scene in scenes:
        for shot in scene.get("shots", []):
            characters = shot.get("characters", [])
            if character_name in characters:
                location = scene.get("location", "")
                time = scene.get("time", "")
                description = shot.get("description", "")
                context_parts.append(f"场景{scene.get('scene_id', '')} {location} {time}：{description}")

    return "；".join(context_parts) if context_parts else "剧本中未找到该角色详细上下文。"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
