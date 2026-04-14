from __future__ import annotations

from typing import Any

import httpx

from .models import GenerationRequest, ModelReference
from .settings import load_config
from .workflows import render_workflow


class ComfyClient:
    def __init__(self) -> None:
        self.config = load_config()
        self.base_url = self.config.comfyui.api_url.rstrip("/")

    async def queue_generation(self, request: GenerationRequest) -> dict[str, Any]:
        workflow, positive, negative, mode = render_workflow(request)
        payload = {"prompt": workflow, "client_id": "genui"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/prompt", json=payload)
            response.raise_for_status()
            body = response.json()
        body["compiled_positive"] = positive
        body["compiled_negative"] = negative
        body["workflow_mode"] = mode
        return body

    async def get_queue(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/queue")
            response.raise_for_status()
            return response.json()

    async def get_history(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/history")
            response.raise_for_status()
            return response.json()

    async def list_models(self) -> list[ModelReference]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/object_info")
            response.raise_for_status()
            info = response.json()
        refs: list[ModelReference] = []
        checkpoints = (
            info.get("CheckpointLoaderSimple", {})
            .get("input", {})
            .get("required", {})
            .get("ckpt_name", [[]])[0]
        )
        loras = (
            info.get("LoraLoader", {})
            .get("input", {})
            .get("required", {})
            .get("lora_name", [[]])[0]
        )
        for name in checkpoints:
            refs.append(ModelReference(name=name, category="checkpoint", path=name))
        for name in loras:
            refs.append(ModelReference(name=name, category="lora", path=name))
        return refs
