[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$Text)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$root = Split-Path $MyInvocation.MyCommand.Path -Parent
$config = Get-Content -Raw -LiteralPath (Join-Path $root 'config.json') | ConvertFrom-Json
if (-not $config.enabled -or [string]::IsNullOrWhiteSpace($Text)) { exit 0 }

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voiceNames = @($synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name })
    if ($voiceNames -contains [string]$config.voice) {
        $synth.SelectVoice([string]$config.voice)
    }
    $synth.Rate = [Math]::Max(-10, [Math]::Min(10, [int]$config.rate))
    $synth.Volume = [Math]::Max(0, [Math]::Min(100, [int]$config.volume))
    $synth.SetOutputToDefaultAudioDevice()
    $synth.Speak($Text)
}
finally {
    $synth.Dispose()
}
