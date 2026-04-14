$ErrorActionPreference = "Stop"

param(
  [string]$InstallRoot = "C:\StabilityMatrix",
  [switch]$WaitForComfyUI,
  [int]$ComfyTimeoutMinutes = 30
)

function Get-LatestReleaseAsset {
  $release = Invoke-RestMethod -Uri "https://api.github.com/repos/LykosAI/StabilityMatrix/releases/latest"
  $preferred = $release.assets |
    Where-Object { $_.browser_download_url -match "win.*x64.*\.zip$" } |
    Select-Object -First 1

  if (-not $preferred) {
    $preferred = $release.assets |
      Where-Object { $_.browser_download_url -match "\.zip$" } |
      Select-Object -First 1
  }

  if (-not $preferred) {
    throw "Could not find a Windows Stability Matrix release asset."
  }

  return $preferred
}

function Find-StabilityMatrixExe {
  param(
    [string]$Root
  )

  return Get-ChildItem -Path $Root -Filter "StabilityMatrix*.exe" -File -Recurse -ErrorAction SilentlyContinue |
    Select-Object -First 1
}

function Find-ComfyUiRoot {
  param(
    [string]$Root
  )

  $defaultPath = Join-Path $Root "Packages\ComfyUI"
  if (Test-Path (Join-Path $defaultPath "main.py")) {
    return $defaultPath
  }

  $match = Get-ChildItem -Path $Root -Directory -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq "ComfyUI" -and (Test-Path (Join-Path $_.FullName "main.py")) } |
    Select-Object -First 1

  if ($match) {
    return $match.FullName
  }

  return $null
}

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

$existingExe = Find-StabilityMatrixExe -Root $InstallRoot
if (-not $existingExe) {
  Write-Host "Downloading Stability Matrix..."
  $asset = Get-LatestReleaseAsset
  $archivePath = Join-Path $env:TEMP $asset.name
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archivePath
  Write-Host "Extracting Stability Matrix to $InstallRoot ..."
  Expand-Archive -Path $archivePath -DestinationPath $InstallRoot -Force
  Remove-Item -LiteralPath $archivePath -Force
  $existingExe = Find-StabilityMatrixExe -Root $InstallRoot
}

if (-not $existingExe) {
  throw "Stability Matrix executable was not found after extraction."
}

Write-Host "Launching Stability Matrix: $($existingExe.FullName)"
Start-Process -FilePath $existingExe.FullName -WorkingDirectory $existingExe.DirectoryName | Out-Null

if ($WaitForComfyUI) {
  Write-Host "Install the ComfyUI package in Stability Matrix now."
  Write-Host "This script will continue automatically when the ComfyUI folder appears."

  $deadline = (Get-Date).AddMinutes($ComfyTimeoutMinutes)
  do {
    Start-Sleep -Seconds 5
    $comfyRoot = Find-ComfyUiRoot -Root $InstallRoot
    if ($comfyRoot) {
      Write-Host "Detected ComfyUI at $comfyRoot"
      exit 0
    }
  } while ((Get-Date) -lt $deadline)

  throw "Timed out waiting for ComfyUI. Install it in Stability Matrix, then rerun the script."
}
