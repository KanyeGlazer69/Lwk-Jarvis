[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-StrictMode -Version 2.0

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Get-FreeSpaceGB {
    $drive = [System.IO.DriveInfo]::new($env:SystemDrive)
    return [math]::Round($drive.AvailableFreeSpace / 1GB, 2)
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Description,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter()][string[]]$ArgumentList = @()
    )

    Write-Host "  $Description"
    & $FilePath @ArgumentList
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    if ($code -ne 0) {
        throw "$Description failed with exit code $code."
    }
}

function Find-PyLauncher {
    $command = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    $windowsApps = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps'
    $candidates = @(
        (Join-Path $windowsApps 'py.exe'),
        (Join-Path $windowsApps 'PythonSoftwareFoundation.PythonManager_qbz5n2kfra8p0\py.exe'),
        (Join-Path $windowsApps 'PythonSoftwareFoundation.PythonManager_3847v3x7pw1km\py.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}

$initialFreeGB = Get-FreeSpaceGB
$installRoot = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase1'
$venvRoot = Join-Path $installRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
$diagnosticSource = Join-Path $PSScriptRoot 'Microphone-Diagnostic.py'

Write-Host 'Jarvis Safe Setup - Phase 1 v3' -ForegroundColor Green
Write-Host "Free storage before setup: $initialFreeGB GB on $env:SystemDrive"
Write-Host "Install location: $installRoot"

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'This installer is intentionally non-admin. Close this window and run it from a normal PowerShell window.'
    }

    if (-not (Test-Path -LiteralPath $diagnosticSource -PathType Leaf)) {
        throw "Required file is missing: $diagnosticSource"
    }
    if ($initialFreeGB -lt 2.0) {
        throw "At least 2.0 GB of free storage is required. Only $initialFreeGB GB is available."
    }

    Write-Step 'Checking Windows Package Manager'
    $wingetCommand = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $wingetCommand) {
        throw 'WinGet was not found. Install or update App Installer from Microsoft Store, then run this setup again.'
    }
    Invoke-Checked -Description 'Checking WinGet' -FilePath $wingetCommand.Source -ArgumentList @('--version')

    Write-Step 'Checking the official Python Install Manager'
    $pyLauncher = Find-PyLauncher
    if (-not $pyLauncher) {
        Invoke-Checked -Description 'Installing Python Install Manager from Microsoft Store' -FilePath $wingetCommand.Source -ArgumentList @(
            'install', '--id', '9NQ7512CXL7T', '--exact', '--source', 'msstore',
            '--accept-source-agreements', '--accept-package-agreements', '--disable-interactivity'
        )
        $pyLauncher = Find-PyLauncher
        if (-not $pyLauncher) {
            throw 'Python Install Manager installed, but py.exe is not available yet. Close PowerShell, open it again, and rerun this setup.'
        }
    }
    # `py --version` may install the manager's default runtime on first use.
    # `py help` verifies the launcher without provisioning an unwanted runtime.
    Invoke-Checked -Description 'Checking Python Install Manager' -FilePath $pyLauncher -ArgumentList @('help')

    Write-Step 'Installing Python 3.12 for the current user'
    Invoke-Checked -Description 'Installing or confirming Python 3.12' -FilePath $pyLauncher -ArgumentList @('install', '3.12', '--yes')

    if (-not (Test-Path -LiteralPath $installRoot)) {
        New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
    }

    Write-Step 'Creating an isolated Jarvis environment'
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        Invoke-Checked -Description 'Creating the virtual environment' -FilePath $pyLauncher -ArgumentList @('-V:3.12', '-m', 'venv', $venvRoot)
    }
    Invoke-Checked -Description 'Verifying the virtual environment uses Python 3.12' -FilePath $venvPython -ArgumentList @('-c', 'import sys; assert sys.version_info[:2] == (3, 12), sys.version; print(sys.version)')

    Write-Step 'Installing openWakeWord and microphone support without a pip cache'
    Invoke-Checked -Description 'Updating pip' -FilePath $venvPython -ArgumentList @('-m', 'pip', 'install', '--no-cache-dir', '--upgrade', 'pip')
    Invoke-Checked -Description 'Installing openWakeWord and sounddevice' -FilePath $venvPython -ArgumentList @('-m', 'pip', 'install', '--no-cache-dir', 'openwakeword', 'sounddevice')
    Invoke-Checked -Description 'Checking installed packages' -FilePath $venvPython -ArgumentList @('-m', 'pip', 'check')
    Invoke-Checked -Description 'Checking openWakeWord import' -FilePath $venvPython -ArgumentList @('-c', 'import openwakeword; print(1)')

    Write-Step 'Running microphone diagnostic'
    Invoke-Checked -Description 'Testing the default microphone' -FilePath $venvPython -ArgumentList @($diagnosticSource)

    $finalFreeGB = Get-FreeSpaceGB
    $usedGB = [math]::Round($initialFreeGB - $finalFreeGB, 2)
    Write-Host "`nFree storage after setup:  $finalFreeGB GB on $env:SystemDrive"
    Write-Host "Approximate storage change: $usedGB GB"
    Write-Host "`nPHASE 1 COMPLETE - DIAGNOSTIC PASSED" -ForegroundColor Green
    Write-Host 'You may now close this PowerShell window.'
    exit 0
}
catch {
    $finalFreeGB = Get-FreeSpaceGB
    Write-Host "`nSETUP STOPPED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Free storage now: $finalFreeGB GB on $env:SystemDrive"
    Write-Host 'No firewall, registry, security-policy, or permanent ExecutionPolicy changes were made.'
    Write-Host 'Leave this window open and take a screenshot of this message if you need help.'
    exit 1
}
