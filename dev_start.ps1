# Heimdall 开发环境启动脚本

Write-Host "Launching Heimdall development environment..." -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$frontendRoot = Join-Path $projectRoot "frontend"
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }
$npmCmd = try { (Get-Command "npm.cmd" -ErrorAction Stop).Source } catch { "npm.cmd" }

$apiHost = "127.0.0.1"
$apiPort = 8000
$frontendHost = "127.0.0.1"
$frontendPort = 4173

$backendCommand = @(
    "Set-Location -LiteralPath '$projectRoot'"
    "`$env:HEIMDALL_API_HOST='$apiHost'"
    "`$env:HEIMDALL_API_PORT='$apiPort'"
    "& '$pythonExe' scripts\\prepare_db.py"
    "if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }"
    "& '$pythonExe' -m uvicorn app.main:app --host $apiHost --reload --port $apiPort"
) -join "; "

$frontendCommand = @(
    "Set-Location -LiteralPath '$frontendRoot'"
    "`$env:HEIMDALL_API_HOST='$apiHost'"
    "`$env:HEIMDALL_API_PORT='$apiPort'"
    "`$env:HEIMDALL_FRONTEND_HOST='$frontendHost'"
    "`$env:HEIMDALL_FRONTEND_PORT='$frontendPort'"
    "& '$npmCmd' run dev"
) -join "; "

Write-Host "Starting backend..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $projectRoot -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand

Start-Sleep -Seconds 3

Write-Host "Starting frontend..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $frontendRoot -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand

Write-Host ""
Write-Host "Backend API:  http://${apiHost}:$apiPort" -ForegroundColor Yellow
Write-Host "Frontend:     http://${frontendHost}:$frontendPort" -ForegroundColor Yellow
Write-Host "API docs:     http://${apiHost}:$apiPort/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Close the backend/frontend windows to stop the services." -ForegroundColor DarkGray
