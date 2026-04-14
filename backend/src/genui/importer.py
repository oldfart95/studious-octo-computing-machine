from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from .models import AssetManifest, AssetType
from .settings import ensure_directories, load_config


EXTENSION_MAP: dict[str, AssetType] = {
    ".safetensors": "unknown",
    ".ckpt": "checkpoint",
    ".pt": "unknown",
    ".pth": "unknown",
    ".bin": "unknown",
}


def _filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name or "downloaded-model"
    return name.split("?")[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _probable_asset_type(filename: str) -> AssetType:
    lowered = filename.lower()
    suffix = Path(lowered).suffix
    if suffix in EXTENSION_MAP and EXTENSION_MAP[suffix] != "unknown":
        return EXTENSION_MAP[suffix]
    if "lora" in lowered or "lycoris" in lowered:
        return "lora"
    if "vae" in lowered:
        return "vae"
    if "embed" in lowered or "textualinversion" in lowered:
        return "embedding"
    if "controlnet" in lowered or "control" in lowered:
        return "controlnet"
    if "upscal" in lowered or "esrgan" in lowered:
        return "upscale_model"
    if suffix == ".ckpt":
        return "checkpoint"
    return "unknown"


def _base_model_guess(filename: str) -> str:
    lowered = filename.lower()
    if "sdxl" in lowered:
        return "sdxl"
    if "sd15" in lowered or "1.5" in lowered:
        return "sd1.5"
    if "flux" in lowered:
        return "flux"
    return ""


def _extract_tags(filename: str) -> list[str]:
    parts = re.split(r"[_\-\s\.]+", filename.lower())
    return [part for part in parts if len(part) > 2][:12]


def _target_dir(asset_type: AssetType) -> Path | None:
    config = load_config()
    model_paths = config.comfyui.models
    mapping = {
        "checkpoint": Path(model_paths.checkpoints),
        "lora": Path(model_paths.loras),
        "vae": Path(model_paths.vae),
        "embedding": Path(model_paths.embeddings),
        "controlnet": Path(model_paths.controlnet),
        "upscale_model": Path(model_paths.upscale_models),
    }
    return mapping.get(asset_type)


def _find_duplicate(filename: str, sha256: str) -> str | None:
    paths = ensure_directories()
    for manifest_path in paths.import_manifest_dir.glob("*.json"):
        manifest = AssetManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        if manifest.sha256 == sha256 or manifest.filename.lower() == filename.lower():
            return manifest.id
    return None


async def import_model_from_url(url: str, dry_run: bool = False) -> AssetManifest:
    paths = ensure_directories()
    filename = _filename_from_url(url)
    temp_name = f"{uuid4().hex}-{filename}"
    quarantine_path = paths.import_quarantine_dir / temp_name

    async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with quarantine_path.open("wb") as handle:
                async for chunk in response.aiter_bytes():
                    handle.write(chunk)

    sha256 = _sha256(quarantine_path)
    probable = _probable_asset_type(filename)
    target_dir = _target_dir(probable)
    duplicate_of = _find_duplicate(filename, sha256)
    destination_path = ""
    needs_review = probable == "unknown" or target_dir is None

    if target_dir is not None:
        destination_path = str(target_dir / filename)

    manifest = AssetManifest(
        id=uuid4().hex,
        source_url=url,
        filename=filename,
        sha256=sha256,
        size_bytes=quarantine_path.stat().st_size,
        probable_asset_type=probable,
        destination_path=destination_path,
        duplicate_of=duplicate_of,
        file_type_guess=quarantine_path.suffix.lower().lstrip("."),
        base_model_guess=_base_model_guess(filename),
        trigger_words=[],
        tags=_extract_tags(filename),
        needs_review=needs_review or duplicate_of is not None,
        safe_preview_default=False,
        notes=["Downloaded to quarantine first."],
    )

    manifest_path = paths.import_manifest_dir / f"{manifest.id}.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    if dry_run:
        quarantine_path.unlink(missing_ok=True)
        return manifest

    if duplicate_of:
        quarantine_path.unlink(missing_ok=True)
        return manifest

    if target_dir is None:
        review_path = paths.import_review_dir / filename
        shutil.move(str(quarantine_path), review_path)
        return manifest

    target_dir.mkdir(parents=True, exist_ok=True)
    final_path = target_dir / filename
    shutil.move(str(quarantine_path), final_path)
    return manifest
