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
$backendTag = "HEIMDALL_BACKEND_$apiHost`:$apiPort"
$backgroundTag = "HEIMDALL_BACKGROUND"
$frontendTag = "HEIMDALL_FRONTEND_$frontendHost`:$frontendPort"

function Get-ProcessLineage {
    param([int]$ProcessId)

    $lineage = @()
    $seen = @{}
    $currentPid = $ProcessId
    for ($depth = 0; $depth -lt 8 -and $currentPid -and -not $seen.ContainsKey($currentPid); $depth++) {
        $seen[$currentPid] = $true
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $currentPid" -ErrorAction SilentlyContinue
        if (-not $process) {
            break
        }
        $lineage += $process
        $currentPid = [int]$process.ParentProcessId
    }
    return $lineage
}

function Format-ProcessLineage {
    param($Lineage)

    return ($Lineage | ForEach-Object {
        $command = if ($_.CommandLine) { $_.CommandLine } else { $_.Name }
        "PID $($_.ProcessId): $command"
    }) -join "`n"
}

function Test-HeimdallProcess {
    param(
        $Lineage,
        [string]$Role,
        [int]$Port,
        [string]$Tag
    )

    $commands = @($Lineage | ForEach-Object { [string]$_.CommandLine })
    $joined = ($commands -join "`n").ToLowerInvariant()
    $ownerCommand = if ($Lineage.Count -gt 0) { ([string]$Lineage[0].CommandLine).ToLowerInvariant() } else { "" }
    $root = $projectRoot.ToLowerInvariant()
    $frontend = $frontendRoot.ToLowerInvariant()
    $tagLower = $Tag.ToLowerInvariant()

    if ($joined.Contains($tagLower)) {
        return $true
    }

    if ($Role -eq "backend") {
        return $ownerCommand.Contains("uvicorn") `
            -and $ownerCommand.Contains("app.main:app") `
            -and $ownerCommand.Contains("--port $Port")
    }

    return ($ownerCommand.Contains($frontend) -or $ownerCommand.Contains($root)) `
        -and $ownerCommand.Contains("vite") `
        -and $ownerCommand.Contains("$Port")
}

function Stop-HeimdallPortListeners {
    param(
        [string]$Name,
        [string]$Role,
        [int]$Port,
        [string]$Tag
    )

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        return
    }

    $ownerPids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($ownerPid in $ownerPids) {
        $lineage = @(Get-ProcessLineage -ProcessId ([int]$ownerPid))
        if (-not $lineage) {
            continue
        }

        if (Test-HeimdallProcess -Lineage $lineage -Role $Role -Port $Port -Tag $Tag) {
            Write-Host "Stopping stale $Name listener on port $Port (PID $ownerPid)..." -ForegroundColor DarkYellow
            $tagLower = $Tag.ToLowerInvariant()
            $stopPids = @()
            foreach ($process in $lineage) {
                $command = ([string]$process.CommandLine).ToLowerInvariant()
                $processName = ([string]$process.Name).ToLowerInvariant()
                $isBackend = $Role -eq "backend" `
                    -and $processName.Contains("python") `
                    -and $command.Contains("uvicorn") `
                    -and $command.Contains("app.main:app")
                $isFrontend = $Role -eq "frontend" `
                    -and ($processName.Contains("node") -or $processName.Contains("npm") -or $processName -eq "cmd.exe") `
                    -and $command.Contains("vite")
                if (
                    $command.Contains($tagLower) `
                    -or $isBackend `
                    -or $isFrontend
                ) {
                    $stopPids += [int]$process.ProcessId
                }
            }
            if ($stopPids -notcontains [int]$ownerPid) {
                $stopPids += [int]$ownerPid
            }
            $stopPids | Select-Object -Unique | ForEach-Object {
                Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
            }
            Start-Sleep -Milliseconds 500
            continue
        }

        Write-Host "$Name port $Port is already used by a non-Heimdall process:" -ForegroundColor Red
        Write-Host (Format-ProcessLineage -Lineage $lineage) -ForegroundColor DarkGray
        throw "$Name port $Port is occupied by another process. Stop it manually or change the port."
    }
}

function Stop-HeimdallTaggedProcesses {
    param(
        [string]$Name,
        [string]$Tag
    )

    $tagLower = $Tag.ToLowerInvariant()
    $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        ([string]$_.CommandLine).ToLowerInvariant().Contains($tagLower)
    }
    foreach ($process in $processes) {
        Write-Host "Stopping stale $Name process (PID $($process.ProcessId))..." -ForegroundColor DarkYellow
        Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
    }
}

function Wait-HeimdallBackendReady {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSeconds = 120
    )

    $healthUrl = "http://${HostName}:$Port/health"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null

    Write-Host "Waiting for backend readiness at $healthUrl ..." -ForegroundColor DarkGray
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "Backend is ready." -ForegroundColor Green
                return
            }
            $lastError = "HTTP $($response.StatusCode)"
        }
        catch {
            $lastError = $_.Exception.Message
        }

        Start-Sleep -Seconds 1
    }

    throw "Backend did not become ready within ${TimeoutSeconds}s. Last check: $lastError"
}

Stop-HeimdallPortListeners -Name "Backend" -Role "backend" -Port $apiPort -Tag $backendTag
Stop-HeimdallPortListeners -Name "Frontend" -Role "frontend" -Port $frontendPort -Tag $frontendTag
Stop-HeimdallTaggedProcesses -Name "Background runtime" -Tag $backgroundTag

$backendCommand = @(
    "Set-Location -LiteralPath '$projectRoot'"
    "`$env:HEIMDALL_PROCESS_TAG='$backendTag'"
    "`$env:APP_RUNTIME_ROLE='api'"
    "`$env:HEIMDALL_API_HOST='$apiHost'"
    "`$env:HEIMDALL_API_PORT='$apiPort'"
    "& '$pythonExe' scripts\\prepare_db.py"
    "if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }"
    "& '$pythonExe' -m uvicorn app.main:app --host $apiHost --reload --reload-dir app --reload-dir config --reload-dir utils --port $apiPort"
) -join "; "

$backgroundCommand = @(
    "Set-Location -LiteralPath '$projectRoot'"
    "`$env:HEIMDALL_PROCESS_TAG='$backgroundTag'"
    "`$env:APP_RUNTIME_ROLE='background'"
    "& '$pythonExe' scripts\\run_background_runtime.py"
) -join "; "

$frontendCommand = @(
    "Set-Location -LiteralPath '$frontendRoot'"
    "`$env:HEIMDALL_PROCESS_TAG='$frontendTag'"
    "`$env:HEIMDALL_API_HOST='$apiHost'"
    "`$env:HEIMDALL_API_PORT='$apiPort'"
    "`$env:HEIMDALL_FRONTEND_HOST='$frontendHost'"
    "`$env:HEIMDALL_FRONTEND_PORT='$frontendPort'"
    "& '$npmCmd' run dev -- --host $frontendHost --port $frontendPort --strictPort"
) -join "; "

Write-Host "Starting backend..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $projectRoot -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand

Wait-HeimdallBackendReady -HostName $apiHost -Port $apiPort

Write-Host "Starting background runtime..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $projectRoot -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backgroundCommand

Write-Host "Starting frontend..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $frontendRoot -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand

Write-Host ""
Write-Host "Backend API:  http://${apiHost}:$apiPort" -ForegroundColor Yellow
Write-Host "Background:   separate worker process" -ForegroundColor Yellow
Write-Host "Frontend:     http://${frontendHost}:$frontendPort" -ForegroundColor Yellow
Write-Host "API docs:     http://${apiHost}:$apiPort/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Close the backend/frontend windows to stop the services." -ForegroundColor DarkGray
