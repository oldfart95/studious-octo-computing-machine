from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .importer import import_model_from_url
from .models import BatchItem, GenerationRequest, Preset
from .service import GenUIService
from .settings import ensure_directories, load_config
from .storage import list_presets, save_preset

app = FastAPI(title="GenUI API", version="0.1.0")
service = GenUIService()
config = load_config()
paths = ensure_directories(config)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.frontend.dev_url, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
async def get_config():
    return config.model_dump(mode="json")


@app.get("/api/presets")
async def presets():
    return [preset.model_dump(mode="json") for preset in service.list_presets()]


@app.post("/api/presets")
async def create_preset(preset: Preset):
    path = save_preset(preset)
    return {"saved": str(path)}


@app.get("/api/style-blocks")
async def style_blocks():
    return [block.model_dump(mode="json") for block in service.list_style_blocks()]


@app.get("/api/models")
async def models():
    refs = await service.list_models()
    return [ref.model_dump(mode="json") for ref in refs]


@app.get("/api/history")
async def history(limit: int = Query(default=50, ge=1, le=500)):
    return [entry.model_dump(mode="json") for entry in service.recent_history(limit)]


@app.post("/api/run")
async def run_generation(request: GenerationRequest):
    entry = await service.run_generation(request)
    return entry.model_dump(mode="json")


@app.post("/api/batch")
async def run_batch(items: list[BatchItem]):
    results = []
    for item in items:
        request = GenerationRequest(
            prompt=item.prompt,
            negative_prompt=item.negative_prompt,
            style_prompt=item.style_prompt,
            preset=item.preset,
            workflow_mode=item.workflow_mode,
            checkpoint=item.checkpoint,
            loras=item.loras,
            locked_style_blocks=item.locked_style_blocks,
            parameters=item.parameters or GenerationRequest(prompt=item.prompt).parameters,
        )
        results.append((await service.run_generation(request)).model_dump(mode="json"))
    return results


@app.post("/api/import-model")
async def import_model(url: str, dry_run: bool = False):
    manifest = await import_model_from_url(url, dry_run=dry_run)
    return manifest.model_dump(mode="json")


@app.get("/api/imports")
async def imports():
    return [item.model_dump(mode="json") for item in service.list_imports()]


@app.get("/api/gallery")
async def gallery():
    output_dir = Path(config.comfyui.output_dir)
    items = []
    if output_dir.exists():
        for path in sorted(output_dir.glob("**/*")):
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                items.append(
                    {
                        "name": path.name,
                        "path": str(path),
                        "url": f"/api/gallery/file?path={quote(str(path))}",
                    }
                )
    return items[-200:]


@app.get("/api/gallery/file")
async def gallery_file(path: str):
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
