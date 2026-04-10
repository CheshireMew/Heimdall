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
$serviceReadyTimeoutSeconds = 45
$pollIntervalMilliseconds = 200

function Stop-LauncherProcess {
    param(
        [Parameter(Mandatory = $false)]
        $Process
    )

    if ($null -ne $Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force
    }
}

function Wait-HttpReady {
    param(
        [Parameter(Mandatory = $true)]
        $Process,
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [Parameter(Mandatory = $true)]
        [datetime]$Deadline
    )

    while ((Get-Date) -lt $Deadline) {
        if ($Process.HasExited) {
            throw "$Name exited before startup completed. PID=$($Process.Id)"
        }

        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return
            }
        }
        catch {
        }

        Start-Sleep -Milliseconds $pollIntervalMilliseconds
    }

    throw "$Name did not become ready within $serviceReadyTimeoutSeconds seconds. Probe=$Url"
}

Write-Host "Launching Heimdall development environment..." -ForegroundColor Cyan

$backend = $null
$frontend = $null

try {
    $backend = Start-Process $pythonExe -WorkingDirectory $projectRoot -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--reload-dir", "app", "--reload-dir", "config", "--reload-dir", "utils", "--reload-exclude=data/*", "--reload-exclude=logs/*", "--reload-exclude=frontend/dist/*", "--port", "$apiPort" -PassThru
    $frontend = Start-Process "npm.cmd" -WorkingDirectory $frontendRoot -ArgumentList "run", "dev", "--", "--host", "127.0.0.1", "--port", "$frontendPort" -PassThru

    $deadline = (Get-Date).AddSeconds($serviceReadyTimeoutSeconds)
    Wait-HttpReady -Process $backend -Name "Backend" -Url "http://127.0.0.1:$apiPort/health" -Deadline $deadline
    Wait-HttpReady -Process $frontend -Name "Frontend" -Url "http://127.0.0.1:$frontendPort/" -Deadline $deadline

    Write-Host ("Backend PID:  {0}" -f $backend.Id) -ForegroundColor Yellow
    Write-Host ("Frontend PID: {0}" -f $frontend.Id) -ForegroundColor Yellow
    Write-Host "Backend API:  http://localhost:8000" -ForegroundColor Yellow
    Write-Host "Frontend:     http://localhost:4173" -ForegroundColor Yellow
    Write-Host "API docs:     http://localhost:8000/docs" -ForegroundColor Yellow
}
catch {
    Stop-LauncherProcess -Process $frontend
    Stop-LauncherProcess -Process $backend
    throw
}
