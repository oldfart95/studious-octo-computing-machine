from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


AssetType = Literal[
    "checkpoint",
    "lora",
    "vae",
    "embedding",
    "controlnet",
    "upscale_model",
    "unknown",
]

WorkflowMode = Literal["txt2img-standard", "txt2img-lora", "art-card-batch"]


class GenerationParameters(BaseModel):
    width: int = 1024
    height: int = 1024
    steps: int = 28
    cfg: float = 6.0
    sampler: str = "euler"
    scheduler: str = "normal"
    seed: int = -1
    batch_size: int = 1


class LoraSelection(BaseModel):
    name: str
    strength_model: float = 0.8
    strength_clip: float = 0.8


class StyleBlock(BaseModel):
    name: str
    prompt: str
    locked: bool = False
    tags: list[str] = Field(default_factory=list)


class Preset(BaseModel):
    name: str
    workflow_mode: WorkflowMode
    checkpoint: str
    loras: list[LoraSelection | str] = Field(default_factory=list)
    positive_prefix: str = ""
    negative_prompt: str = ""
    style_prompt: str = ""
    locked_style_blocks: list[str] = Field(default_factory=list)
    parameters: GenerationParameters = Field(default_factory=GenerationParameters)


class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    style_prompt: str = ""
    preset: str | None = None
    workflow_mode: WorkflowMode | None = None
    checkpoint: str | None = None
    loras: list[LoraSelection] = Field(default_factory=list)
    locked_style_blocks: list[str] = Field(default_factory=list)
    parameters: GenerationParameters = Field(default_factory=GenerationParameters)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchItem(BaseModel):
    prompt: str
    negative_prompt: str = ""
    style_prompt: str = ""
    preset: str | None = None
    workflow_mode: WorkflowMode | None = None
    checkpoint: str | None = None
    loras: list[LoraSelection] = Field(default_factory=list)
    locked_style_blocks: list[str] = Field(default_factory=list)
    parameters: GenerationParameters | None = None


class AssetManifest(BaseModel):
    id: str
    source_url: str
    filename: str
    sha256: str
    size_bytes: int
    probable_asset_type: AssetType = "unknown"
    destination_path: str = ""
    duplicate_of: str | None = None
    file_type_guess: str = ""
    base_model_guess: str = ""
    trigger_words: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    needs_review: bool = False
    safe_preview_default: bool = False
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    notes: list[str] = Field(default_factory=list)


class HistoryEntry(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "queued"
    request: GenerationRequest
    prompt_compiled: str
    negative_compiled: str
    workflow_mode: WorkflowMode
    comfy_prompt_id: str | None = None
    output_files: list[str] = Field(default_factory=list)


class ModelReference(BaseModel):
    name: str
    category: AssetType
    path: str


class AppPaths(BaseModel):
    root: Path
    config_dir: Path
    data_dir: Path
    logs_dir: Path
    presets_dir: Path
    style_blocks_dir: Path
    workflows_dir: Path
    output_dir: Path
    import_quarantine_dir: Path
    import_manifest_dir: Path
    import_review_dir: Path
    history_file: Path
