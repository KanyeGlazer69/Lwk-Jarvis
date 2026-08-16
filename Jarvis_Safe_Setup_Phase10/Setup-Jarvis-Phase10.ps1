[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
function Invoke-Checked { param([string]$Description,[string]$FilePath,[string[]]$ArgumentList=@()); Write-Host "  $Description"; & $FilePath @ArgumentList; $code=$LASTEXITCODE; if($null -eq $code){$code=0}; if($code -ne 0){throw "$Description failed with exit code $code."} }
$python=Join-Path $env:LOCALAPPDATA 'Jarvis\Phase1\.venv\Scripts\python.exe'
$phase4=Join-Path $env:LOCALAPPDATA 'Jarvis\Phase4'
$phase10=Join-Path $env:LOCALAPPDATA 'Jarvis\Phase10'
Write-Host 'Jarvis Safe Setup - Phase 10 Opera GX and Apple Music' -ForegroundColor Cyan
try {
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent(); $principal=[Security.Principal.WindowsPrincipal]::new($identity)
    if($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Phase 10 is intentionally non-admin.'}
    if(-not(Test-Path -LiteralPath $python -PathType Leaf)){throw 'Phase 1 is missing.'}
    New-Item -ItemType Directory -Path $phase10 -Force | Out-Null
    foreach($name in @('desktop_apps.py','Apple-Music-Control.ps1','Test-Desktop-Apps.py')){Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $phase10 $name) -Force}
    $brainSource=Join-Path (Split-Path $PSScriptRoot -Parent) 'Jarvis_Safe_Setup_Phase4\jarvis_brain.py'
    Copy-Item -LiteralPath $brainSource -Destination (Join-Path $phase4 'jarvis_brain.py') -Force
    Invoke-Checked 'Testing the command allowlist' $python @((Join-Path $phase10 'Test-Desktop-Apps.py'))
    Write-Host 'PHASE 10 APP CONTROLS INSTALLED' -ForegroundColor Green
    exit 0
} catch { Write-Host "PHASE 10 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }
