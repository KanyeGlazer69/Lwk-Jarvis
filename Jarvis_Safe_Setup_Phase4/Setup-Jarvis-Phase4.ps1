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
$phase3 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase3\jarvis_hear.py'
$phase4 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase4'
$initialFree = Get-FreeSpaceGB

Write-Host 'Jarvis Safe Setup - Phase 4' -ForegroundColor Green
Write-Host "Free storage before setup: $initialFree GB"

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Phase 4 is intentionally non-admin.'
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Phase 1 is missing.' }
    if (-not (Test-Path -LiteralPath $phase3 -PathType Leaf)) { throw 'Phase 3 is missing.' }
    if ($initialFree -lt 2.0) { throw "At least 2.0 GB free is required. Available: $initialFree GB." }

    Write-Host "`n==> Installing the official Gemini SDK"
    Invoke-Checked 'Installing google-genai without a pip cache' $python @('-m', 'pip', 'install', '--no-cache-dir', 'google-genai')
    Invoke-Checked 'Checking dependencies' $python @('-m', 'pip', 'check')

    Write-Host "`n==> Installing Phase 4 files"
    if (-not (Test-Path -LiteralPath $phase4)) { New-Item -ItemType Directory -Path $phase4 -Force | Out-Null }
    foreach ($name in @('jarvis_brain.py', 'Configure-Gemini-Key.ps1', 'Run-Jarvis-Phase4.ps1', 'Test-Phase4.cmd', 'Start-Jarvis-Thinking.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase4 $name) -Force
    }
    Invoke-Checked 'Checking Gemini SDK import' $python @('-c', 'from google import genai; print(genai.__name__)')

    $finalFree = Get-FreeSpaceGB
    Write-Host "`nFree storage after setup: $finalFree GB"
    Write-Host 'PHASE 4 SOFTWARE SELF-TEST PASSED' -ForegroundColor Green
    Write-Host 'Next: create a free Gemini API key, then run Configure-Gemini-Key.ps1.'
    exit 0
}
catch {
    Write-Host "`nPHASE 4 SETUP STOPPED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Free storage now: $(Get-FreeSpaceGB) GB"
    Write-Host 'No startup, firewall, registry, security-policy, or permanent ExecutionPolicy changes were made.'
    exit 1
}
