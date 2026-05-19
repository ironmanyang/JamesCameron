from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"
SYSTEM_ROOT = OUTPUT_ROOT / "_system"
STORAGE_MANIFEST_PATH = SYSTEM_ROOT / "storage_manifest.json"
FRONTEND_ROOT = PROJECT_ROOT / "code" / "frontEnd"

