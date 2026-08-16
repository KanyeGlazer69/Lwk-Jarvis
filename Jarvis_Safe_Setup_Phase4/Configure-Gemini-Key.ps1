[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
$phase4 = Join-Path $env:LOCALAPPDATA 'Jarvis\Phase4'
$keyFile = Join-Path $phase4 'gemini-key.dpapi'

try {
    Write-Host 'Jarvis Phase 4 - Private Gemini Key Setup' -ForegroundColor Cyan
    Write-Host 'Your key will not appear while you type or paste it.'
    Write-Host 'It will be encrypted for your Windows account using DPAPI.'
    $secureKey = Read-Host 'Paste your Gemini API key, then press Enter' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    $plainBytes = $null
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        if ([string]::IsNullOrWhiteSpace($plain)) { throw 'No key was entered.' }
        $plainBytes = [Text.Encoding]::UTF8.GetBytes($plain)
        $protectedBytes = [Security.Cryptography.ProtectedData]::Protect(
            $plainBytes,
            $null,
            [Security.Cryptography.DataProtectionScope]::CurrentUser
        )
        $encrypted = 'JARVIS-DPAPI-V1:' + [Convert]::ToBase64String($protectedBytes)
        [System.IO.File]::WriteAllText($keyFile, $encrypted, [System.Text.UTF8Encoding]::new($false))
    }
    finally {
        if ($plainBytes) { [Array]::Clear($plainBytes, 0, $plainBytes.Length) }
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    Write-Host "`nEncrypted key saved for Windows user $env:USERNAME." -ForegroundColor Green
    Write-Host 'The plaintext key was not written to disk.'
}
catch {
    Write-Host "`nKEY SETUP FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Read-Host 'Press Enter to close'
