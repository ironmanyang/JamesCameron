$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "code\backEnd"
$frontendDir = Join-Path $root "code\frontEnd"
$backendLog = Join-Path $root "backend.dev.log"
$backendErrLog = Join-Path $root "backend.dev.err.log"
$frontendLog = Join-Path $root "frontend.dev.log"
$frontendErrLog = Join-Path $root "frontend.dev.err.log"
$frontendUrl = "http://127.0.0.1:8080"
$backendUrl = "http://127.0.0.1:8000/api/health"

function Stop-ListeningPort {
    param([int]$Port)

    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
        foreach ($connection in $connections) {
            Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    } catch {
    }
}

function Wait-HttpReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null
            return $true
        } catch {
            Start-Sleep -Milliseconds 800
        }
    }

    return $false
}

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found: $backendDir"
}

if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found: $frontendDir"
}

Stop-ListeningPort -Port 8000
Stop-ListeningPort -Port 8080
Start-Sleep -Seconds 1

$backendCommand = 'title AI-Video-Backend && cd /d "{0}" && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload 1>>"{1}" 2>>"{2}"' -f $backendDir, $backendLog, $backendErrLog
$frontendCommand = 'title AI-Video-Frontend && cd /d "{0}" && npm.cmd run dev 1>>"{1}" 2>>"{2}"' -f $frontendDir, $frontendLog, $frontendErrLog

Start-Process -FilePath "cmd.exe" -ArgumentList "/c $backendCommand" -WindowStyle Hidden
if (-not (Wait-HttpReady -Url $backendUrl -TimeoutSeconds 45)) {
    throw "Backend failed to start within 45 seconds. Check backend.dev.err.log"
}

Start-Process -FilePath "cmd.exe" -ArgumentList "/c $frontendCommand" -WindowStyle Hidden
if (-not (Wait-HttpReady -Url $frontendUrl -TimeoutSeconds 60)) {
    throw "Frontend failed to start within 60 seconds. Check frontend.dev.err.log"
}

Start-Process $frontendUrl
