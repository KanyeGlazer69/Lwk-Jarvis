[CmdletBinding()]
param([switch]$Once, [switch]$Probe, [switch]$MemoryProbe)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
$phase4 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase4'
$keyFile = Join-Path $phase4 'gemini-key.dpapi'
$python = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase1\.venv\Scripts\python.exe'
$brain = Join-Path $phase4 'jarvis_brain.py'

if (-not (Test-Path -LiteralPath $keyFile -PathType Leaf)) {
    throw 'No encrypted Gemini key found. Run Configure-Gemini-Key.ps1 first.'
}
$encrypted = [System.IO.File]::ReadAllText($keyFile).Trim()
if (-not $encrypted.StartsWith('JARVIS-DPAPI-V1:')) { throw 'The encrypted key file has an unsupported format.' }
$protectedBytes = [Convert]::FromBase64String($encrypted.Substring(16))
$plainBytes = [Security.Cryptography.ProtectedData]::Unprotect(
    $protectedBytes,
    $null,
    [Security.Cryptography.DataProtectionScope]::CurrentUser
)
try {
    $env:GEMINI_API_KEY = [Text.Encoding]::UTF8.GetString($plainBytes)
    $arguments = @('-u', $brain)
    if ($Once) { $arguments += '--once' }
    if ($Probe) { $arguments += '--probe' }
    if ($MemoryProbe) { $arguments += '--memory-probe' }
    & $python @arguments
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    exit $code
}
finally {
    Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
    [Array]::Clear($plainBytes, 0, $plainBytes.Length)
}
