param(
    [int]$Port = 3002
)

$ErrorActionPreference = "Stop"

if ($env:CONDA_DEFAULT_ENV -ne "claud_fe") {
    Write-Error "Frontend must run inside conda env 'claud_fe'. Run: conda activate claud_fe"
}

$FrontendDir = Resolve-Path "$PSScriptRoot\..\frontend"
Set-Location $FrontendDir

npx next dev -p $Port
