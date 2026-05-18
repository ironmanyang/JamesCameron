from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from api.series import router as series_router
from api.script import router as script_router
from api.character import router as character_router
from api.scene import router as scene_router
from api.storyboard import router as storyboard_router
from api.video import router as video_router

load_dotenv()

app = FastAPI(title="AI Video Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(series_router)
app.include_router(script_router)
app.include_router(character_router)
app.include_router(scene_router)
app.include_router(storyboard_router)
app.include_router(video_router)


class HealthResponse(BaseModel):
    status: str


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}


@app.get("/api")
async def api_root():
    return {"message": "AI Video Backend API", "version": "1.0.0"}


@app.get("/api/files")
async def serve_file(path: str):
    file_path = Path(path)
    if not file_path.exists():
        return {"error": "File not found"}, 404
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)