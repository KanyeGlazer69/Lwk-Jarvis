[CmdletBinding()]
param()
$shortcut = Join-Path ([Environment]::GetFolderPath('Startup')) 'Jarvis.lnk'
if (Test-Path -LiteralPath $shortcut) {
    Remove-Item -LiteralPath $shortcut -Force
}
Write-Host 'Jarvis startup disabled. Jarvis itself was not removed.'
