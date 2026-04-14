from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, TypeVar

from pydantic import BaseModel

from .models import AssetManifest, HistoryEntry, Preset, StyleBlock
from .settings import build_paths, dump_json

T = TypeVar("T", bound=BaseModel)


def _load_models_from_dir(path: Path, model_type: type[T]) -> list[T]:
    if not path.exists():
        return []
    items: list[T] = []
    for file in sorted(path.glob("*.json")):
        items.append(model_type.model_validate_json(file.read_text(encoding="utf-8")))
    return items


def list_presets() -> list[Preset]:
    return _load_models_from_dir(build_paths().presets_dir, Preset)


def get_preset(name: str) -> Preset | None:
    for preset in list_presets():
        if preset.name == name:
            return preset
    return None


def save_preset(preset: Preset) -> Path:
    path = build_paths().presets_dir / f"{preset.name}.json"
    dump_json(path, preset.model_dump(mode="json"))
    return path


def list_style_blocks() -> list[StyleBlock]:
    return _load_models_from_dir(build_paths().style_blocks_dir, StyleBlock)


def get_style_block(name: str) -> StyleBlock | None:
    for item in list_style_blocks():
        if item.name == name:
            return item
    return None


def save_style_block(block: StyleBlock) -> Path:
    path = build_paths().style_blocks_dir / f"{block.name}.json"
    dump_json(path, block.model_dump(mode="json"))
    return path


def append_history(entry: HistoryEntry) -> None:
    history_file = build_paths().history_file
    with history_file.open("a", encoding="utf-8") as handle:
        handle.write(entry.model_dump_json())
        handle.write("\n")


def iter_history(limit: int = 100) -> Iterable[HistoryEntry]:
    history_file = build_paths().history_file
    if not history_file.exists():
        return []
    rows = history_file.read_text(encoding="utf-8").splitlines()
    selected = rows[-limit:]
    return [HistoryEntry.model_validate(json.loads(row)) for row in selected if row.strip()]


def list_import_manifests() -> list[AssetManifest]:
    return _load_models_from_dir(build_paths().import_manifest_dir, AssetManifest)
