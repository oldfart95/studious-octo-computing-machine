from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .models import AppPaths


class BackendConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8008


class FrontendConfig(BaseModel):
    dev_url: str = "http://127.0.0.1:5173"


class ComfyModelPaths(BaseModel):
    checkpoints: str
    loras: str
    vae: str
    embeddings: str
    controlnet: str
    upscale_models: str


class ComfyConfig(BaseModel):
    root: str
    api_url: str = "http://127.0.0.1:8188"
    output_dir: str
    models: ComfyModelPaths


class PathConfig(BaseModel):
    logs: str
    data: str
    presets: str
    style_blocks: str
    workflows: str


class SafetyConfig(BaseModel):
    safe_preview_default: bool = False
    hide_import_previews_in_main_gallery: bool = True
    blur_flagged_import_thumbnails: bool = True


class AppConfig(BaseModel):
    app_name: str = "GenUI"
    backend: BackendConfig = Field(default_factory=BackendConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    comfyui: ComfyConfig
    paths: PathConfig
    safety: SafetyConfig = Field(default_factory=SafetyConfig)


def project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def config_path() -> Path:
    return project_root() / "config" / "local-config.json"


def ensure_local_config() -> Path:
    path = config_path()
    if not path.exists():
        example = project_root() / "config" / "local-config.example.json"
        path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    return path


@lru_cache(maxsize=1)
def load_config() -> AppConfig:
    path = ensure_local_config()
    return AppConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))


def build_paths(config: AppConfig | None = None) -> AppPaths:
    config = config or load_config()
    root = project_root()
    cfg = config.paths
    data_dir = Path(cfg.data)
    output_dir = Path(config.comfyui.output_dir)
    paths = AppPaths(
        root=root,
        config_dir=root / "config",
        data_dir=data_dir,
        logs_dir=Path(cfg.logs),
        presets_dir=Path(cfg.presets),
        style_blocks_dir=Path(cfg.style_blocks),
        workflows_dir=Path(cfg.workflows),
        output_dir=output_dir,
        import_quarantine_dir=data_dir / "imports" / "quarantine",
        import_manifest_dir=data_dir / "imports" / "manifests",
        import_review_dir=data_dir / "imports" / "review",
        history_file=data_dir / "history" / "jobs.jsonl",
    )
    return paths


def ensure_directories(config: AppConfig | None = None) -> AppPaths:
    paths = build_paths(config)
    needed = [
        paths.logs_dir,
        paths.data_dir,
        paths.presets_dir,
        paths.style_blocks_dir,
        paths.workflows_dir,
        paths.output_dir,
        paths.import_quarantine_dir,
        paths.import_manifest_dir,
        paths.import_review_dir,
        paths.history_file.parent,
        paths.data_dir / "gallery",
    ]
    for folder in needed:
        folder.mkdir(parents=True, exist_ok=True)
    paths.history_file.touch(exist_ok=True)
    return paths


def dump_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
