import hashlib
import re
import unicodedata
from pathlib import Path


def _tokenize(value: str, empty_prefix: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if normalized:
        return normalized
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{empty_prefix}-{digest}"


def slugify(value: str) -> str:
    return _tokenize(value, "s")


def make_series_id(slug: str) -> str:
    normalized = slug.replace("-", "_")
    if normalized.startswith("series_"):
        return normalized
    return f"series_{normalized}"


def make_entity_id(prefix: str, name: str) -> str:
    token = _tokenize(name, prefix)
    token = token.replace("-", "_")
    if token.startswith(f"{prefix}_"):
        return token
    return f"{prefix}_{token}"


def ensure_unique_slug(base_slug: str, output_root: Path) -> str:
    if not (output_root / base_slug).exists():
        return base_slug

    suffix = 2
    while True:
        candidate = f"{base_slug}-{suffix}"
        if not (output_root / candidate).exists():
            return candidate
        suffix += 1


def ensure_unique_id(base_id: str, parent_root: Path) -> str:
    if not (parent_root / base_id).exists():
        return base_id

    suffix = 2
    while True:
        candidate = f"{base_id}_{suffix}"
        if not (parent_root / candidate).exists():
            return candidate
        suffix += 1


def next_numeric_id(prefix: str, existing_ids: list[str]) -> tuple[str, int]:
    pattern = re.compile(rf"{re.escape(prefix)}_(\d{{3}})$")
    numbers = []
    for item_id in existing_ids:
        match = pattern.fullmatch(item_id)
        if match:
            numbers.append(int(match.group(1)))

    next_number = max(numbers, default=0) + 1
    return f"{prefix}_{next_number:03d}", next_number


def next_episode_id(existing_ids: list[str]) -> tuple[str, int]:
    numbers = []
    for episode_id in existing_ids:
        match = re.fullmatch(r"ep_(\d{3})", episode_id)
        if match:
            numbers.append(int(match.group(1)))

    next_number = max(numbers, default=0) + 1
    return f"ep_{next_number:03d}", next_number
