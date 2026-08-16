[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-StrictMode -Version 2.0

function Invoke-Checked {
    param([string]$Description, [string]$FilePath, [string[]]$ArgumentList = @())
    Write-Host "  $Description"
    & $FilePath @ArgumentList
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    if ($code -ne 0) { throw "$Description failed with exit code $code." }
}

function Get-FreeSpaceGB {
    return [math]::Round(([System.IO.DriveInfo]::new($env:SystemDrive)).AvailableFreeSpace / 1GB, 2)
}

$python = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase1\.venv\Scripts\python.exe'
$phase2 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase2'
$phase3 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase3'
$initialFree = Get-FreeSpaceGB

Write-Host 'Jarvis Safe Setup - Phase 3' -ForegroundColor Green
Write-Host "Free storage before setup: $initialFree GB"

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Phase 3 is intentionally non-admin.'
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Phase 1 is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $phase2 'jarvis_listener.py'))) { throw 'Phase 2 is missing.' }
    if ($initialFree -lt 2.0) { throw "At least 2.0 GB free is required. Available: $initialFree GB." }

    Write-Host "`n==> Validating earlier phases"
    Invoke-Checked 'Checking Python 3.12' $python @('-c', 'import sys; assert sys.version_info[:2] == (3, 12); print(sys.version)')
    Invoke-Checked 'Checking current dependencies' $python @('-m', 'pip', 'check')

    Write-Host "`n==> Installing lean local speech recognition"
    Invoke-Checked 'Installing faster-whisper without a pip cache' $python @('-m', 'pip', 'install', '--no-cache-dir', 'faster-whisper')
    Invoke-Checked 'Checking all dependencies' $python @('-m', 'pip', 'check')

    Write-Host "`n==> Installing Phase 3 files"
    if (-not (Test-Path -LiteralPath $phase3)) { New-Item -ItemType Directory -Path $phase3 -Force | Out-Null }
    foreach ($name in @('Prepare-Speech-Model.py', 'jarvis_hear.py', 'config.json', 'Test-Phase3.cmd', 'Start-Jarvis-Hearing.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase3 $name) -Force
    }

    Write-Host "`n==> Downloading and loading the high-accuracy distil-large-v3 model"
    Invoke-Checked 'Preparing local speech model' $python @((Join-Path $phase3 'Prepare-Speech-Model.py'))

    $finalFree = Get-FreeSpaceGB
    Write-Host "`nFree storage after setup: $finalFree GB"
    Write-Host 'PHASE 3 SOFTWARE SELF-TEST PASSED' -ForegroundColor Green
    Write-Host "Live test: $phase3\Test-Phase3.cmd"
    exit 0
}
catch {
    Write-Host "`nPHASE 3 SETUP STOPPED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Free storage now: $(Get-FreeSpaceGB) GB"
    Write-Host 'No startup, firewall, registry, security-policy, or permanent ExecutionPolicy changes were made.'
    exit 1
}
