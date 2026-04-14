from __future__ import annotations

import json
from pathlib import Path
from random import randint
from typing import Any

from .models import GenerationRequest, WorkflowMode
from .prompts import compile_prompts, merge_request_with_preset
from .settings import build_paths


def workflow_file_for_mode(mode: WorkflowMode) -> Path:
    return build_paths().workflows_dir / f"{mode}.json"


def load_workflow_template(mode: WorkflowMode) -> dict[str, Any]:
    return json.loads(workflow_file_for_mode(mode).read_text(encoding="utf-8"))


def _resolved_seed(seed: int) -> int:
    return randint(1, 2**31 - 1) if seed == -1 else seed


def render_workflow(request: GenerationRequest) -> tuple[dict[str, Any], str, str, WorkflowMode]:
    merged = merge_request_with_preset(request)
    mode: WorkflowMode = merged.workflow_mode or "txt2img-standard"
    template = load_workflow_template(mode)
    workflow = template["workflow"]
    positive, negative = compile_prompts(merged)
    parameters = merged.parameters

    workflow[template["checkpoint_node_id"]]["inputs"]["ckpt_name"] = (
        merged.checkpoint or workflow[template["checkpoint_node_id"]]["inputs"]["ckpt_name"]
    )
    workflow[template["positive_node_id"]]["inputs"]["text"] = positive
    workflow[template["negative_node_id"]]["inputs"]["text"] = negative
    workflow[template["latent_node_id"]]["inputs"]["width"] = parameters.width
    workflow[template["latent_node_id"]]["inputs"]["height"] = parameters.height
    workflow[template["latent_node_id"]]["inputs"]["batch_size"] = parameters.batch_size
    workflow[template["ksampler_node_id"]]["inputs"]["seed"] = _resolved_seed(parameters.seed)
    workflow[template["ksampler_node_id"]]["inputs"]["steps"] = parameters.steps
    workflow[template["ksampler_node_id"]]["inputs"]["cfg"] = parameters.cfg
    workflow[template["ksampler_node_id"]]["inputs"]["sampler_name"] = parameters.sampler
    workflow[template["ksampler_node_id"]]["inputs"]["scheduler"] = parameters.scheduler

    if mode == "txt2img-lora" and merged.loras:
        lora = merged.loras[0]
        workflow[template["lora_node_id"]]["inputs"]["lora_name"] = lora.name
        workflow[template["lora_node_id"]]["inputs"]["strength_model"] = lora.strength_model
        workflow[template["lora_node_id"]]["inputs"]["strength_clip"] = lora.strength_clip

    return workflow, positive, negative, mode
