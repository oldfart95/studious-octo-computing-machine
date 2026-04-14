# Maintenance Notes

## Logs

- Backend logs: `logs\backend.log`
- Frontend logs: use terminal output during `npm run dev`
- Import manifests: `data\imports\manifests`
- Job history: `data\history\jobs.jsonl`

## Config

Primary config lives in:

- `config\local-config.json`

This file points to:

- ComfyUI root
- ComfyUI API URL
- ComfyUI model folders
- output directories
- backend host/port

## Safe Import Review

- Imported preview media should stay hidden by default.
- If you later add metadata image fetching, keep it behind the import review page only.
- Do not automatically mix import previews into the generation gallery.

## Stability Matrix

Stability Matrix should remain the source of truth for:

- ComfyUI installation
- shared model placement
- package updates you explicitly choose to make there

GenUI can now open the Stability Matrix download page, launch Stability Matrix if it is already installed under `C:\StabilityMatrix`, and then pause for you to finish installing the ComfyUI package before it rewrites `config\local-config.json` to the detected ComfyUI package path.

If you already use a different Stability Matrix location, either:

```powershell
.\scripts\install-first-time.ps1 -StabilityMatrixRoot "D:\StabilityMatrix"
```

or edit `config\local-config.json` manually after install.

## Upgrades

When updating ComfyUI:

1. Update from Stability Matrix or your existing ComfyUI process.
2. Run `.\scripts\update-packages.ps1`.
3. Verify `ComfyUI-Manager` still exists under `custom_nodes`.
4. Restart `.\scripts\launch.ps1`.

## Backend Service Notes

- The backend writes line-delimited history for easy recovery.
- Presets and style blocks remain plain JSON on disk.
- Workflow templates are kept separate from presets so they can evolve independently.

## Tailscale

Recommended:

```powershell
tailscale serve --bg 443 http://127.0.0.1:5173
```

Check status:

```powershell
tailscale serve status
```

Stop serving:

```powershell
tailscale serve reset
```
