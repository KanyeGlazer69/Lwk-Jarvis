[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$pythonw = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase1\.venv\Scripts\pythonw.exe'
$phase9 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase9'
$app = Join-Path $phase9 'jarvis_app.py'
$packageRoot = Split-Path -Parent $PSScriptRoot
$appSource = Join-Path $packageRoot 'Jarvis_Safe_Setup_Phase9\jarvis_app.py'
$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'Jarvis.lnk'

Write-Host 'Jarvis Safe Setup - Phase 11 Startup' -ForegroundColor Cyan
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Phase 11 is intentionally non-admin.'
    }
    if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) { throw 'Jarvis Python is missing.' }
    if (-not (Test-Path -LiteralPath $appSource -PathType Leaf)) { throw 'The Phase 9 app source is missing from this package.' }
    New-Item -ItemType Directory -Path $phase9 -Force | Out-Null
    Copy-Item -LiteralPath $appSource -Destination $app -Force
    if (-not (Test-Path -LiteralPath $app -PathType Leaf)) { throw 'Jarvis Phase 9 could not be updated.' }

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $pythonw
    $shortcut.Arguments = '"' + $app + '" --startup'
    $shortcut.WorkingDirectory = $phase9
    $shortcut.WindowStyle = 7
    $shortcut.Description = 'Start Jarvis silently after Windows sign-in'
    $shortcut.Save()

    $check = $shell.CreateShortcut($shortcutPath)
    if ($check.TargetPath -ne $pythonw -or $check.Arguments -notmatch '--startup') {
        throw 'The startup shortcut did not validate.'
    }
    Write-Host "Startup shortcut: $shortcutPath"
    Write-Host 'JARVIS STARTUP ENABLED' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "PHASE 11 SETUP STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
