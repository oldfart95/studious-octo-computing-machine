# GenUI Local Image Pipeline

GenUI is a local-first Windows image generation pipeline that uses Stability Matrix for package/bootstrap management, ComfyUI for inference/workflows, and a custom backend/frontend for a calmer daily-use experience.

## What This Includes

- `Stability Matrix` as the package and shared model manager
- `ComfyUI` as the inference backend
- `ComfyUI-Manager` installed during setup
- Python backend service with REST API and CLI
- Mobile-first React frontend for browser and tablet use
- Presets and style blocks stored as readable JSON
- Conservative model importer with quarantine, manifests, and duplicate detection
- Tailscale Serve documentation for tailnet-only access

## Core Principles

- Local-first by default
- No public exposure by default
- Touch-friendly UI
- Text metadata first for imports
- Imported previews hidden by default
- Reusable locked prompt sections and presets

## Project Layout

```text
backend/                 Python API, CLI, importer, ComfyUI integration
frontend/                React mobile-first web app
scripts/                 Windows PowerShell install/launch/update scripts
config/                  Local config defaults, presets, style blocks, examples
comfyui-workflows/       ComfyUI workflow templates
logs/                    Runtime logs
data/                    Gallery metadata, history, manifests, imports, outputs
```

## Install

1. Clone or place this project at `C:\My-Image-Gen-Pipeline`.
2. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install-first-time.ps1
```

This script will:

- bootstrap `Stability Matrix` into `C:\StabilityMatrix` if missing
- launch `Stability Matrix` and wait for you to install the `ComfyUI` package there
- auto-detect the installed `ComfyUI` package path and update local config
- create local folders
- create a Python virtual environment
- install backend dependencies
- install frontend dependencies
- install `ComfyUI-Manager` into your ComfyUI custom nodes folder
- write a local config file if missing

## Update

```powershell
.\scripts\update-packages.ps1
```

## Launch

Normal full stack:

```powershell
.\scripts\launch.ps1
```

Backend only:

```powershell
.\scripts\launch-backend.ps1
```

Frontend only:

```powershell
.\scripts\launch-frontend.ps1
```

Rebuild frontend:

```powershell
.\scripts\rebuild-frontend.ps1
```

## Local Use

After launch:

- Frontend UI: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8008`
- ComfyUI should remain local on the address you configured in `config\local-config.json`

## Tailscale Use

Do not expose services publicly by default. Keep everything bound locally or on your LAN/Tailscale interface, then publish only the frontend over your tailnet with Tailscale Serve.

Example flow:

1. Start the stack locally.
2. On the Windows machine running GenUI:

```powershell
tailscale serve --bg 443 http://127.0.0.1:5173
```

3. Open the shown tailnet HTTPS URL from your tablet while signed into your tailnet.

If you want the frontend to talk to the backend through the same origin, use the frontend proxy in dev or build the frontend and serve it behind a small local reverse proxy later. For this project, the default dev path uses Vite proxying `/api` to the backend.

## Model Import Rules

Supported source inputs:

- Civitai model page links
- direct download URLs
- Hugging Face file links
- generic `.safetensors`, `.ckpt`, `.pt`, `.pth` URLs

Importer behavior:

- downloads to `data\imports\quarantine`
- guesses asset type from URL, filename, extension, and light metadata
- classifies into checkpoint, LoRA, VAE, embedding, ControlNet, or upscale model when possible
- calculates SHA256
- detects duplicates by filename and hash
- writes a human-readable manifest JSON per asset
- moves validated assets into the configured ComfyUI model folder
- marks incomplete imports as `needs_review`

## Safe Preview Behavior

- Imported preview images are not shown in the main gallery by default.
- Metadata previews remain hidden unless you deliberately open the import review area.
- Import cards prioritize text metadata:
  - model name
  - source URL
  - file type guess
  - base model guess
  - trigger words
  - tags
- Each import has a `safe_preview_default: false` flag in its manifest unless you change it.

## Presets And Locked Style Blocks

- Presets are saved as JSON under `config\presets`.
- Style blocks are saved as JSON under `config\style-blocks`.
- Locked style blocks remain attached to new runs unless you explicitly unlock or remove them.
- Presets can select workflow mode, defaults, model choices, LoRAs, and generation parameters.

## Default Workflows

- `txt2img-standard.json`
- `txt2img-lora.json`
- `art-card-batch.json`

The backend swaps workflow templates based on mode or preset, then injects prompt and parameter values before queueing to ComfyUI.

## CLI Examples

```powershell
genui run --preset ritual-card --prompt "cathedral engine"
genui batch --file .\config\examples\batches\art-cards.json
genui import-model --url "https://example.com/model.safetensors"
genui preset save --name dark-fantasy-style
genui preset apply --name dark-fantasy-style
genui models list
genui presets list
```

## First Commands To Run

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd C:\My-Image-Gen-Pipeline
.\scripts\install-first-time.ps1
.\scripts\launch.ps1
```

If Stability Matrix is not already present, `install-first-time.ps1` now downloads the latest Windows release, launches it, and pauses while you install the `ComfyUI` package from inside Stability Matrix. Once the ComfyUI package folder appears, setup continues automatically.

## Notes

- Stability Matrix remains the owner of your installed package runtimes and shared model storage.
- GenUI treats ComfyUI as the execution engine and keeps its own config, presets, manifests, logs, and UI in this project.
- See `MAINTENANCE.md` for operational notes and troubleshooting.
