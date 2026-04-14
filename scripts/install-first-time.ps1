$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$ConfigExample = Join-Path $ProjectRoot "config\local-config.example.json"
$ConfigFile = Join-Path $ProjectRoot "config\local-config.json"
$VenvDir = Join-Path $ProjectRoot ".venv"
$LogsDir = Join-Path $ProjectRoot "logs"
$DataDir = Join-Path $ProjectRoot "data"

Write-Host "Preparing folders..."
@(
  $LogsDir,
  $DataDir,
  (Join-Path $DataDir "history"),
  (Join-Path $DataDir "imports"),
  (Join-Path $DataDir "imports\quarantine"),
  (Join-Path $DataDir "imports\manifests"),
  (Join-Path $DataDir "imports\review"),
  (Join-Path $DataDir "gallery")
) | ForEach-Object {
  New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

if (-not (Test-Path $ConfigFile)) {
  Copy-Item $ConfigExample $ConfigFile
  Write-Host "Wrote local config template to $ConfigFile"
}

if (-not (Test-Path $VenvDir)) {
  Write-Host "Creating Python virtual environment..."
  python -m venv $VenvDir
}

$Python = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host "Installing backend dependencies..."
& $Python -m pip install --upgrade pip
& $Pip install -e $BackendDir

Write-Host "Installing frontend dependencies..."
Push-Location $FrontendDir
npm install
Pop-Location

$Config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
$ComfyRoot = $Config.comfyui.root
$CustomNodes = Join-Path $ComfyRoot "custom_nodes"
$ManagerDir = Join-Path $CustomNodes "ComfyUI-Manager"

if (-not (Test-Path $CustomNodes)) {
  New-Item -ItemType Directory -Force -Path $CustomNodes | Out-Null
}

if (-not (Test-Path $ManagerDir)) {
  Write-Host "Installing ComfyUI-Manager..."
  git clone https://github.com/ltdrdata/ComfyUI-Manager.git $ManagerDir
} else {
  Write-Host "ComfyUI-Manager already present."
}

Write-Host ""
Write-Host "Install complete."
Write-Host "Review config at $ConfigFile before first launch."
