from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.characters import router as characters_router
from app.api.episodes import router as episodes_router
from app.api.jobs import router as jobs_router
from app.api.scenes import router as scenes_router
from app.api.series import router as series_router
from app.api.snapshots import router as snapshots_router
from app.api.storyboards import router as storyboards_router
from app.config import BACKEND_ROOT, FRONTEND_ROOT, OUTPUT_ROOT, PROJECT_ROOT
from app.storage.common import ensure_storage_manifest

load_dotenv(BACKEND_ROOT / ".env")

app = FastAPI(
    title="AI Video Workflow Backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(series_router)
app.include_router(episodes_router)
app.include_router(characters_router)
app.include_router(scenes_router)
app.include_router(storyboards_router)
app.include_router(snapshots_router)
app.include_router(jobs_router)


@app.on_event("startup")
async def on_startup() -> None:
    ensure_storage_manifest()


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/meta")
async def project_meta():
    return {
        "project_root": str(PROJECT_ROOT),
        "output_dir": str(OUTPUT_ROOT),
        "frontend_dir": str(FRONTEND_ROOT),
        "backend_dir": str(BACKEND_ROOT),
    }


app.mount("/output", StaticFiles(directory=OUTPUT_ROOT), name="output")
