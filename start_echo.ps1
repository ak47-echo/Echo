$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "06_Code"
$frontendDir = Join-Path $root "07_Web"
$frontendUrl = "http://127.0.0.1:5173"

Write-Host "Backend starting on http://127.0.0.1:8000"
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    "Set-Location -LiteralPath '$backendDir'; python -m uvicorn echo_api:app --reload --env-file ../.env"
)

Write-Host "Frontend starting on http://127.0.0.1:5173"
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    "Set-Location -LiteralPath '$frontendDir'; python -m http.server 5173"
)

Start-Sleep -Seconds 2
Start-Process $frontendUrl

Write-Host "Echo ready"
