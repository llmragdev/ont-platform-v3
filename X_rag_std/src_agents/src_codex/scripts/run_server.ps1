param(
    [int]$Port = 8010
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".\.conda")) {
    Write-Host "Creating folder-based conda environment at .conda ..."
    conda env create --prefix .\.conda --file environment.yml
}

.\.conda\python.exe -m uvicorn main:app --reload --port $Port
