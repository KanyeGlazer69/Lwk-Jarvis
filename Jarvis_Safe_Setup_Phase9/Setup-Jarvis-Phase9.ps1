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
$phase9 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase9'

Write-Host 'Jarvis Safe Setup - Phase 9 Desktop App' -ForegroundColor Cyan
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Phase 9 is intentionally non-admin.' }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Phase 1 is missing.' }
    if (-not (Test-Path -LiteralPath $phase9)) { New-Item -ItemType Directory -Path $phase9 -Force | Out-Null }
    Invoke-Checked 'Installing the lightweight tray interface' $python @('-m','pip','install','--no-cache-dir','Pillow','pystray')
    foreach ($name in @('jarvis_app.py', 'Start-Jarvis-App.cmd')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase9 $name) -Force
    }
    $assetSource = Join-Path $PSScriptRoot 'assets\black-gold-marble.png'
    $assetTarget = Join-Path $phase9 'assets\black-gold-marble.png'
    if (-not (Test-Path -LiteralPath $assetSource -PathType Leaf)) { throw 'The marble interface asset is missing.' }
    New-Item -ItemType Directory -Path (Split-Path -Parent $assetTarget) -Force | Out-Null
    Copy-Item -LiteralPath $assetSource -Destination $assetTarget -Force
    Invoke-Checked 'Checking the desktop app' $python @('-m','py_compile',(Join-Path $phase9 'jarvis_app.py'))
    Invoke-Checked 'Checking required interface components' $python @('-c','import tkinter,PIL,pystray')
    Write-Host 'PHASE 9 DESKTOP APP INSTALLED' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "PHASE 9 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
