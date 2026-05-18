import json
import re
from typing import Dict

SENSITIVE_WORDS_MAP: Dict[str, str] = {
    "血迹": "深色液体痕迹",
    "鲜血": "红色液体",
    "血腥": "紧张氛围",
    "暴力": "激烈对抗",
    "死亡": "失去生命迹象",
    "杀人": "伤害行为",
    "谋杀": "可疑行为",
    "尸体": "静止的身体",
    "血淋淋": "带有痕迹的",
    "溅血": "留下痕迹",
    "爆头": "严重伤害",
    "枪击": "突然的巨响",
    "自杀": "自我伤害",
    "虐待": "不公正对待",
    "折磨": "持续的压力",
}


def sanitize_text(text: str) -> str:
    result = text
    for word, replacement in SENSITIVE_WORDS_MAP.items():
        result = result.replace(word, replacement)
    return result
