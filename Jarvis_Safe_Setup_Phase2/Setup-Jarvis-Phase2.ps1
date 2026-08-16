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
$initialFree = Get-FreeSpaceGB

Write-Host 'Jarvis Safe Setup - Phase 2' -ForegroundColor Green
Write-Host "Free storage before setup: $initialFree GB"

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Phase 2 is intentionally non-admin. Run it from a normal PowerShell window.'
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw 'The verified Phase 1 environment is missing.'
    }
    if ($initialFree -lt 1.5) {
        throw "At least 1.5 GB free is required for safe Windows breathing room. Available: $initialFree GB."
    }

    Write-Host "`n==> Validating Phase 1"
    Invoke-Checked 'Checking Python 3.12' $python @('-c', 'import sys; assert sys.version_info[:2] == (3, 12); print(sys.version)')
    Invoke-Checked 'Checking Phase 1 packages' $python @('-m', 'pip', 'check')

    Write-Host "`n==> Downloading and validating the official Hey Jarvis model"
    Invoke-Checked 'Preparing openWakeWord models' $python @((Join-Path $PSScriptRoot 'Prepare-Models.py'))

    Write-Host "`n==> Installing the Phase 2 listener"
    if (-not (Test-Path -LiteralPath $phase2)) { New-Item -ItemType Directory -Path $phase2 -Force | Out-Null }
    foreach ($name in @('jarvis_listener.py', 'config.json', 'Start-Hey-Jarvis.cmd', 'Test-Hey-Jarvis.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase2 $name) -Force
    }

    Write-Host "`n==> Running unattended microphone and false-trigger baseline"
    Invoke-Checked 'Running 20-second baseline' $python @((Join-Path $phase2 'jarvis_listener.py'), '--baseline-seconds', '20')

    $finalFree = Get-FreeSpaceGB
    Write-Host "`nFree storage after setup: $finalFree GB"
    Write-Host 'PHASE 2 SOFTWARE + BASELINE PASSED' -ForegroundColor Green
    Write-Host "Tomorrow, run: $phase2\Test-Hey-Jarvis.cmd"
    exit 0
}
catch {
    Write-Host "`nPHASE 2 SETUP STOPPED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Free storage now: $(Get-FreeSpaceGB) GB"
    Write-Host 'No startup, firewall, registry, security-policy, or permanent ExecutionPolicy changes were made.'
    exit 1
}
