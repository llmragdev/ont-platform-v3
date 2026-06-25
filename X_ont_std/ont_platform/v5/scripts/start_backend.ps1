param(
    [int]$Port = 8001,
    [switch]$NoReload,
    [switch]$KeepExisting
)

$ErrorActionPreference = "Stop"

if ($env:CONDA_DEFAULT_ENV -ne "claud_be") {
    Write-Error "Backend must run inside conda env 'claud_be'. Run: conda activate claud_be"
}

$BackendDir = Resolve-Path "$PSScriptRoot\..\backend"
Set-Location $BackendDir

$env:PYTHONPATH = $BackendDir.Path

if (-not $KeepExisting) {
    # 1. Kill process holding the port (Worker)
    $owners = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        if ($owner -and (Get-Process -Id $owner -ErrorAction SilentlyContinue)) {
            Write-Host "Stopping existing process on port ${Port}: PID $owner" -ForegroundColor Yellow
            Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
        }
    }
    
    # 2. Kill parent/zombie reloader process (Master)
    $EscapedBackendDir = [regex]::Escape($BackendDir.Path)
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | 
        Where-Object {
            $_.CommandLine -match "uvicorn app\.main:app" -and
            $_.CommandLine -match "--port $Port" -and
            $_.CommandLine -match $EscapedBackendDir
        } |
        ForEach-Object {
            Write-Host "Stopping zombie uvicorn process: PID $($_.ProcessId)" -ForegroundColor Yellow
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
        
    Start-Sleep -Seconds 1
}

$LogDir = Join-Path $BackendDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "backend-$Timestamp.log"
$LatestLogFile = Join-Path $LogDir "backend-latest.log"

Write-Host "Backend log file: $LogFile" -ForegroundColor Cyan
Write-Host "Latest log file : $LatestLogFile" -ForegroundColor Cyan

if ($NoReload) {
    cmd /c "python -m uvicorn app.main:app --port $Port --env-file .env 2>&1" |
        Tee-Object -FilePath $LogFile |
        Tee-Object -FilePath $LatestLogFile
    exit $LASTEXITCODE
}

cmd /c "python -m uvicorn app.main:app --reload --reload-dir=app --port $Port --env-file .env 2>&1" |
    Tee-Object -FilePath $LogFile |
    Tee-Object -FilePath $LatestLogFile
