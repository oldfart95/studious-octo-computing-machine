$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BackendLog = Join-Path $ProjectRoot "logs\backend.log"

if (-not (Test-Path $VenvPython)) {
  throw "Virtual environment not found. Run .\scripts\install-first-time.ps1 first."
}

Set-Location $ProjectRoot
& $VenvPython -m genui.main 2>&1 | Tee-Object -FilePath $BackendLog -Append
