[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$source = Join-Path $PSScriptRoot 'YouTube-Auto-Skip'
$destination = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase12\YouTube-Auto-Skip'
Write-Host 'Jarvis Safe Setup - Phase 12 YouTube Auto Skip' -ForegroundColor Cyan
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Phase 12 is intentionally non-admin.' }
    foreach ($name in @('manifest.json', 'background.js', 'youtube.js')) {
        if (-not (Test-Path -LiteralPath (Join-Path $source $name) -PathType Leaf)) { throw "Extension file is missing: $name" }
    }
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    foreach ($name in @('manifest.json', 'background.js', 'youtube.js')) {
        Copy-Item -LiteralPath (Join-Path $source $name) -Destination (Join-Path $destination $name) -Force
    }
    Get-Content -LiteralPath (Join-Path $destination 'manifest.json') -Raw | ConvertFrom-Json | Out-Null
    Write-Host "Extension folder: $destination"
    Write-Host 'PHASE 12 FILES INSTALLED' -ForegroundColor Green
    exit 0
} catch { Write-Host "PHASE 12 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }
