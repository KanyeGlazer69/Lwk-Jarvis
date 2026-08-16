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

$python = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase1\.venv\Scripts\python.exe'
$phase4 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase4'
$phase7 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase7'

Write-Host 'Jarvis Safe Setup - Phase 7 Explicit Screen Vision' -ForegroundColor Green
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Phase 7 is intentionally non-admin.' }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Phase 1 is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $phase4 'jarvis_brain.py') -PathType Leaf)) { throw 'Phase 4 is missing.' }

    Invoke-Checked 'Installing lightweight screen capture without a pip cache' $python @('-m', 'pip', 'install', '--no-cache-dir', 'mss')
    Invoke-Checked 'Checking dependencies' $python @('-m', 'pip', 'check')
    if (-not (Test-Path -LiteralPath $phase7)) { New-Item -ItemType Directory -Path $phase7 -Force | Out-Null }
    foreach ($name in @('screen_capture.py', 'Test-Screen-Capture.py', 'Start-Jarvis-With-Vision.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase7 $name) -Force
    }
    $brainSource = Join-Path (Split-Path $PSScriptRoot -Parent) 'Jarvis_Safe_Setup_Phase4\jarvis_brain.py'
    Copy-Item -LiteralPath $brainSource -Destination (Join-Path $phase4 'jarvis_brain.py') -Force
    Invoke-Checked 'Testing local capture (not uploaded or saved)' $python @((Join-Path $phase7 'Test-Screen-Capture.py'))
    Write-Host 'PHASE 7 LOCAL SCREEN CAPTURE SELF-TEST PASSED' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "PHASE 7 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
