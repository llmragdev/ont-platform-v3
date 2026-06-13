param(
    [int]$Port = 8001
)

$ErrorActionPreference = "Stop"

if ($env:CONDA_DEFAULT_ENV -ne "claud_be") {
    Write-Error "Backend must run inside conda env 'claud_be'. Run: conda activate claud_be"
}

$BackendDir = Resolve-Path "$PSScriptRoot\..\backend"
Set-Location $BackendDir

$env:PYTHONPATH = $BackendDir.Path

python -m uvicorn app.main:app --reload --port $Port
