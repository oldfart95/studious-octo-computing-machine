from __future__ import annotations

import json
import shutil
from pathlib import Path

import anyio
import typer

from .importer import import_model_from_url
from .models import GenerationRequest, Preset
from .service import GenUIService
from .settings import ensure_directories
from .storage import get_preset, list_presets, save_preset

app = typer.Typer(help="GenUI command line interface")
preset_app = typer.Typer(help="Preset operations")
models_app = typer.Typer(help="Model operations")
app.add_typer(preset_app, name="preset")
app.add_typer(models_app, name="models")


def _service() -> GenUIService:
    ensure_directories()
    return GenUIService()


@app.command()
def run(
    prompt: str = typer.Option(..., "--prompt"),
    preset: str | None = typer.Option(None, "--preset"),
    negative_prompt: str = typer.Option("", "--negative-prompt"),
    style_prompt: str = typer.Option("", "--style-prompt"),
) -> None:
    request = GenerationRequest(
        prompt=prompt,
        preset=preset,
        negative_prompt=negative_prompt,
        style_prompt=style_prompt,
    )
    entry = anyio.run(_service().run_generation, request)
    typer.echo(entry.model_dump_json(indent=2))


@app.command()
def batch(file: Path = typer.Option(..., "--file", exists=True, dir_okay=False)) -> None:
    payload = json.loads(file.read_text(encoding="utf-8"))
    service = _service()
    for item in payload:
        request = GenerationRequest.model_validate(item)
        entry = anyio.run(service.run_generation, request)
        typer.echo(entry.model_dump_json(indent=2))


@app.command("batch-folder")
def batch_folder(folder: Path = typer.Option(..., "--folder", exists=True, file_okay=False)) -> None:
    service = _service()
    for file in sorted(folder.glob("*.json")):
        request = GenerationRequest.model_validate_json(file.read_text(encoding="utf-8"))
        entry = anyio.run(service.run_generation, request)
        typer.echo(entry.model_dump_json(indent=2))


@app.command("import-model")
def import_model(
    url: str = typer.Option(..., "--url"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    manifest = anyio.run(import_model_from_url, url, dry_run)
    typer.echo(manifest.model_dump_json(indent=2))


@preset_app.command("save")
def preset_save(name: str = typer.Option(..., "--name")) -> None:
    existing = get_preset(name)
    if existing:
        save_preset(existing)
        typer.echo(f"Preset refreshed: {name}")
        return
    sample = Preset(
        name=name,
        workflow_mode="txt2img-standard",
        checkpoint="sdxl_base_1.0.safetensors",
    )
    save_preset(sample)
    typer.echo(f"Preset created: {name}")


@preset_app.command("apply")
def preset_apply(name: str = typer.Option(..., "--name")) -> None:
    preset = get_preset(name)
    if not preset:
        raise typer.Exit(code=1)
    typer.echo(preset.model_dump_json(indent=2))


@preset_app.command("list")
def preset_list() -> None:
    for preset in list_presets():
        typer.echo(preset.name)


@preset_app.command("export")
def preset_export(
    name: str = typer.Option(..., "--name"),
    out: Path = typer.Option(..., "--out"),
) -> None:
    preset = get_preset(name)
    if not preset:
        raise typer.Exit(code=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(preset.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Exported preset to {out}")


@preset_app.command("import")
def preset_import(file: Path = typer.Option(..., "--file", exists=True, dir_okay=False)) -> None:
    preset = Preset.model_validate_json(file.read_text(encoding="utf-8"))
    saved = save_preset(preset)
    typer.echo(f"Imported preset to {saved}")


@models_app.command("list")
def models_list() -> None:
    refs = anyio.run(_service().list_models)
    for ref in refs:
        typer.echo(f"{ref.category}: {ref.name}")
