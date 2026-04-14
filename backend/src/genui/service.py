from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .comfy import ComfyClient
from .models import GenerationRequest, HistoryEntry, ModelReference
from .settings import load_config
from .storage import (
    append_history,
    get_preset,
    iter_history,
    list_import_manifests,
    list_presets,
    list_style_blocks,
)
from .workflows import render_workflow


class GenUIService:
    def __init__(self) -> None:
        self.comfy = ComfyClient()

    async def run_generation(self, request: GenerationRequest) -> HistoryEntry:
        payload = await self.comfy.queue_generation(request)
        _, positive, negative, mode = render_workflow(request)
        entry = HistoryEntry(
            id=uuid4().hex,
            status="queued",
            request=request,
            prompt_compiled=positive,
            negative_compiled=negative,
            workflow_mode=mode,
            comfy_prompt_id=str(payload.get("prompt_id", "")),
        )
        append_history(entry)
        return entry

    async def list_models(self):
        try:
            return await self.comfy.list_models()
        except Exception:
            config = load_config()
            refs: list[ModelReference] = []
            mapping = {
                "checkpoint": config.comfyui.models.checkpoints,
                "lora": config.comfyui.models.loras,
                "vae": config.comfyui.models.vae,
                "embedding": config.comfyui.models.embeddings,
                "controlnet": config.comfyui.models.controlnet,
                "upscale_model": config.comfyui.models.upscale_models,
            }
            for category, folder in mapping.items():
                path = Path(folder)
                if not path.exists():
                    continue
                for file in sorted(path.iterdir()):
                    if file.is_file():
                        refs.append(ModelReference(name=file.name, category=category, path=str(file)))
            return refs

    def list_presets(self):
        return list_presets()

    def get_preset(self, name: str):
        return get_preset(name)

    def list_style_blocks(self):
        return list_style_blocks()

    def recent_history(self, limit: int = 50):
        return list(iter_history(limit=limit))

    def list_imports(self):
        return list_import_manifests()
