[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
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
$phase5 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase5'

Write-Host 'Jarvis Safe Setup - Phase 5 Memory' -ForegroundColor Green
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Phase 5 is intentionally non-admin.' }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Phase 1 is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $phase4 'jarvis_brain.py') -PathType Leaf)) { throw 'Phase 4 is missing.' }

    if (-not (Test-Path -LiteralPath $phase5)) { New-Item -ItemType Directory -Path $phase5 -Force | Out-Null }
    foreach ($name in @('jarvis_memory.py', 'manage_memory.py', 'Test-Memory.py', 'Manage-Jarvis-Memory.cmd', 'Start-Jarvis-With-Memory.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase5 $name) -Force
    }
    $brainSource = Join-Path (Split-Path $PSScriptRoot -Parent) 'Jarvis_Safe_Setup_Phase4\jarvis_brain.py'
    if (-not (Test-Path -LiteralPath $brainSource -PathType Leaf)) { throw 'The validated memory-enabled brain source is missing.' }
    Copy-Item -LiteralPath $brainSource -Destination (Join-Path $phase4 'jarvis_brain.py') -Force
    Invoke-Checked 'Testing memory create, recall, and forget' $python @((Join-Path $phase5 'Test-Memory.py'))
    Invoke-Checked 'Checking dependencies' $python @('-m', 'pip', 'check')
    Write-Host 'PHASE 5 SOFTWARE SELF-TEST PASSED' -ForegroundColor Green
    Write-Host "Memory manager: $phase5\Manage-Jarvis-Memory.cmd"
    exit 0
}
catch {
    Write-Host "PHASE 5 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
