$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$ConfigFile = Join-Path $ProjectRoot "config\local-config.json"
$Config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
$ManagerDir = Join-Path $Config.comfyui.root "custom_nodes\ComfyUI-Manager"

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e $BackendDir --upgrade

Push-Location $FrontendDir
npm install
Pop-Location

if (Test-Path $ManagerDir) {
  Push-Location $ManagerDir
  git pull
  Pop-Location
}

Write-Host "Package update complete."
