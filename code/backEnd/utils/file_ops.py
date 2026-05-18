from pathlib import Path
import json
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


def get_series_dir(name: str) -> Path:
    return ROOT_DIR / name


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_series() -> List[str]:
    if not ROOT_DIR.exists():
        return []
    return [d.name for d in ROOT_DIR.iterdir() if d.is_dir()]