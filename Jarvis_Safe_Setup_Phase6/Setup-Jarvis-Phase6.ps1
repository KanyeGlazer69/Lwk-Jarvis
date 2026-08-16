[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$phase4 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase4'
$phase6 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase6'

Write-Host 'Jarvis Safe Setup - Phase 6 Speech' -ForegroundColor Green
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Phase 6 is intentionally non-admin.' }
    if (-not (Test-Path -LiteralPath (Join-Path $phase4 'jarvis_brain.py') -PathType Leaf)) { throw 'Phase 4 is missing.' }
    if (-not (Test-Path -LiteralPath $phase6)) { New-Item -ItemType Directory -Path $phase6 -Force | Out-Null }
    foreach ($name in @('config.json', 'Speak-Jarvis.ps1', 'Start-Jarvis-Talking.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase6 $name) -Force
    }
    $brainSource = Join-Path (Split-Path $PSScriptRoot -Parent) 'Jarvis_Safe_Setup_Phase4\jarvis_brain.py'
    Copy-Item -LiteralPath $brainSource -Destination (Join-Path $phase4 'jarvis_brain.py') -Force
    & (Join-Path $phase6 'Speak-Jarvis.ps1') -Text 'Jarvis voice online.'
    if (-not $?) { throw 'Windows speech test failed.' }
    Write-Host 'PHASE 6 OFFLINE SPEECH TEST PASSED' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "PHASE 6 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
