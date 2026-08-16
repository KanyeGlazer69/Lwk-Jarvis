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
$phase8 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase8'

Write-Host 'Jarvis Safe Setup - Phase 8 Windows Actions' -ForegroundColor Green
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Phase 8 is intentionally non-admin.' }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Phase 1 is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $phase4 'jarvis_brain.py') -PathType Leaf)) { throw 'Phase 4 is missing.' }
    if (-not (Test-Path -LiteralPath $phase8)) { New-Item -ItemType Directory -Path $phase8 -Force | Out-Null }
    foreach ($name in @('windows_actions.py', 'Test-Windows-Actions.py', 'Start-Jarvis-With-Actions.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase8 $name) -Force
    }
    $brainSource = Join-Path (Split-Path $PSScriptRoot -Parent) 'Jarvis_Safe_Setup_Phase4\jarvis_brain.py'
    Copy-Item -LiteralPath $brainSource -Destination (Join-Path $phase4 'jarvis_brain.py') -Force
    Invoke-Checked 'Testing safe actions without launching apps' $python @((Join-Path $phase8 'Test-Windows-Actions.py'))
    Write-Host 'PHASE 8 ACTION ALLOWLIST SELF-TEST PASSED' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "PHASE 8 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
