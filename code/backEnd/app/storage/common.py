import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from app.config import STORAGE_MANIFEST_PATH, SYSTEM_ROOT


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_storage_manifest() -> None:
    ensure_directory(SYSTEM_ROOT)
    if STORAGE_MANIFEST_PATH.exists():
        return

    manifest = {
        "storage_version": "1.0.0",
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "series_root": "output",
        "notes": "Local file storage manifest for AI video workflow",
    }
    write_json_atomic(STORAGE_MANIFEST_PATH, manifest)


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, data: Any) -> None:
    ensure_directory(path.parent)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def write_text_atomic(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def write_bytes_atomic(path: Path, content: bytes) -> None:
    ensure_directory(path.parent)
    with NamedTemporaryFile("wb", delete=False, dir=path.parent, suffix=".tmp") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def relative_to_series_root(path: Path, series_root: Path) -> str:
    return path.relative_to(series_root).as_posix()
