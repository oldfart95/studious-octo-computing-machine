$ErrorActionPreference = "Stop"

param(
  [string]$InstallRoot = "C:\StabilityMatrix",
  [switch]$PromptForComfyUI
)

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

$downloadUrl = "https://github.com/LykosAI/StabilityMatrix/releases/latest"
$docsUrl = "https://github.com/LykosAI/StabilityMatrix"

$existingExe = Find-StabilityMatrixExe -Root $InstallRoot
Write-Host ""
Write-Host "Stability Matrix setup handoff"
Write-Host "1. Your browser will open the Stability Matrix download page."
Write-Host "2. If Stability Matrix is already installed, it will be launched."
Write-Host "3. In Stability Matrix, download and install the ComfyUI package if needed."
Write-Host "4. Come back here and choose Continue to carry on with GenUI setup."
Write-Host ""
Write-Host "Download page: $downloadUrl"
Write-Host "Project page:  $docsUrl"
Write-Host ""

Start-Process $downloadUrl | Out-Null

if ($existingExe) {
  Write-Host "Launching Stability Matrix: $($existingExe.FullName)"
  Start-Process -FilePath $existingExe.FullName -WorkingDirectory $existingExe.DirectoryName | Out-Null
} else {
  Write-Host "No local Stability Matrix executable was found under $InstallRoot."
  Write-Host "Download and install Stability Matrix from the opened page, then install ComfyUI there."
}

if ($PromptForComfyUI) {
  $choices = @(
    (New-Object System.Management.Automation.Host.ChoiceDescription "&Continue", "Continue after ComfyUI is installed."),
    (New-Object System.Management.Automation.Host.ChoiceDescription "&Cancel", "Stop setup for now.")
  )

  $selection = $Host.UI.PromptForChoice(
    "Continue Setup",
    "After Stability Matrix is ready and ComfyUI has been installed, choose Continue.",
    $choices,
    0
  )

  if ($selection -ne 0) {
    throw "Setup paused. Re-run install-first-time.ps1 when you are ready to continue."
  }

  $comfyRoot = Find-ComfyUiRoot -Root $InstallRoot
  if ($comfyRoot) {
    Write-Host "Detected ComfyUI at $comfyRoot"
    exit 0
  }

  throw "ComfyUI was not found after Continue. Install ComfyUI in Stability Matrix, then rerun the script."
}
