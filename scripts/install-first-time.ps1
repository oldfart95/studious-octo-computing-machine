$ErrorActionPreference = "Stop"

param(
  [switch]$BootstrapStabilityMatrix = $true,
  [string]$StabilityMatrixRoot = "C:\StabilityMatrix"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$ConfigExample = Join-Path $ProjectRoot "config\local-config.example.json"
$ConfigFile = Join-Path $ProjectRoot "config\local-config.json"
$VenvDir = Join-Path $ProjectRoot ".venv"
$LogsDir = Join-Path $ProjectRoot "logs"
$DataDir = Join-Path $ProjectRoot "data"
$BootstrapScript = Join-Path $PSScriptRoot "bootstrap-stability-matrix.ps1"

function Find-ComfyUiRoot {
  param(
    [string[]]$CandidateRoots
  )

  foreach ($root in $CandidateRoots) {
    if (-not $root) {
      continue
    }

    $normalizedRoot = [Environment]::ExpandEnvironmentVariables($root)
    if (-not (Test-Path $normalizedRoot)) {
      continue
    }

    if (Test-Path (Join-Path $normalizedRoot "main.py")) {
      return $normalizedRoot
    }

    $match = Get-ChildItem -Path $normalizedRoot -Directory -Recurse -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -eq "ComfyUI" -and (Test-Path (Join-Path $_.FullName "main.py")) } |
      Select-Object -First 1

    if ($match) {
      return $match.FullName
    }
  }

  return $null
}

function Set-ConfigComfyPaths {
  param(
    [string]$ResolvedComfyRoot
  )

  $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
  $config.comfyui.root = $ResolvedComfyRoot
  $config.comfyui.output_dir = Join-Path $ResolvedComfyRoot "output"
  $config.comfyui.models.checkpoints = Join-Path $ResolvedComfyRoot "models\checkpoints"
  $config.comfyui.models.loras = Join-Path $ResolvedComfyRoot "models\loras"
  $config.comfyui.models.vae = Join-Path $ResolvedComfyRoot "models\vae"
  $config.comfyui.models.embeddings = Join-Path $ResolvedComfyRoot "models\embeddings"
  $config.comfyui.models.controlnet = Join-Path $ResolvedComfyRoot "models\controlnet"
  $config.comfyui.models.upscale_models = Join-Path $ResolvedComfyRoot "models\upscale_models"
  $config | ConvertTo-Json -Depth 8 | Set-Content $ConfigFile
}

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

$ConfiguredComfyRoot = (Get-Content $ConfigFile -Raw | ConvertFrom-Json).comfyui.root
$ComfyRoot = Find-ComfyUiRoot -CandidateRoots @(
  $ConfiguredComfyRoot,
  (Join-Path $StabilityMatrixRoot "Packages\ComfyUI"),
  $StabilityMatrixRoot
)

if (-not $ComfyRoot -and $BootstrapStabilityMatrix) {
  Write-Host "Opening Stability Matrix handoff..."
  & $BootstrapScript -InstallRoot $StabilityMatrixRoot -PromptForComfyUI
  $ComfyRoot = Find-ComfyUiRoot -CandidateRoots @(
    $ConfiguredComfyRoot,
    (Join-Path $StabilityMatrixRoot "Packages\ComfyUI"),
    $StabilityMatrixRoot
  )
}

if (-not $ComfyRoot) {
  throw "ComfyUI was not found. Install ComfyUI through Stability Matrix, then rerun this script."
}

Set-ConfigComfyPaths -ResolvedComfyRoot $ComfyRoot

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
