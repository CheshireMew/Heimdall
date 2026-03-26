# PowerShell entrypoint for the Windows development launcher.

$projectRoot = [System.IO.Directory]::GetCurrentDirectory()
if (-not (Test-Path (Join-Path $projectRoot "frontend"))) {
    $projectRoot = $PSScriptRoot
}

$frontendRoot = Join-Path $projectRoot "frontend"
$venvPython = Join-Path $projectRoot "venv\\Scripts\\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }
$apiPort = 8000
$frontendPort = 4173

Write-Host "Launching Heimdall development environment..." -ForegroundColor Cyan

$backend = Start-Process $pythonExe -WorkingDirectory $projectRoot -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--reload-dir", "app", "--reload-dir", "config", "--reload-dir", "utils", "--reload-exclude", "data/*", "--reload-exclude", "logs/*", "--reload-exclude", "frontend/dist/*", "--port", "$apiPort" -PassThru
Start-Sleep -Seconds 3
$frontend = Start-Process "npm.cmd" -WorkingDirectory $frontendRoot -ArgumentList "run", "dev", "--", "--host", "127.0.0.1", "--port", "$frontendPort" -PassThru

Write-Host ("Backend PID:  {0}" -f $backend.Id) -ForegroundColor Yellow
Write-Host ("Frontend PID: {0}" -f $frontend.Id) -ForegroundColor Yellow
Write-Host "Backend API:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend:     http://localhost:4173" -ForegroundColor Yellow
Write-Host "API docs:     http://localhost:8000/docs" -ForegroundColor Yellow
