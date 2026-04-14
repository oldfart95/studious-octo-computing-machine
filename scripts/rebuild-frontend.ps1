$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"

Push-Location $FrontendDir
npm run build
Pop-Location

Write-Host "Frontend rebuilt."
