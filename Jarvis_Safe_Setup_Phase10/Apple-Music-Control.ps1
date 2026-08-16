[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Query,
    [switch]$Play
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms

$process = Get-Process | Where-Object { $_.MainWindowTitle -match 'Apple Music' } | Select-Object -First 1
if (-not $process) { throw 'Apple Music window not found.' }
$root = [System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
$trueCondition = [System.Windows.Automation.Condition]::TrueCondition

function Get-AllElements {
    $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $trueCondition)
}

$elements = Get-AllElements
$search = $null
for ($i = 0; $i -lt $elements.Count; $i++) {
    $element = $elements.Item($i)
    if ($element.Current.ControlType -eq [System.Windows.Automation.ControlType]::Edit -and
        $element.Current.Name -eq 'Search') {
        $search = $element
        break
    }
}
if (-not $search) { throw 'Apple Music search field not found.' }
$valuePattern = $null
if (-not $search.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$valuePattern)) {
    throw 'Apple Music search field is not writable.'
}
$search.SetFocus()
$valuePattern.SetValue($Query)
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Seconds 2

if (-not $Play) {
    Write-Output 'APPLE_MUSIC_SEARCH_COMPLETE'
    exit 0
}

$elements = Get-AllElements
$result = $null
for ($i = 0; $i -lt $elements.Count; $i++) {
    $element = $elements.Item($i)
    if ($element.Current.ControlType -eq [System.Windows.Automation.ControlType]::ListItem -and
        $element.Current.Name -match ' Song\s*[·.]' -and
        $element.Current.Name -notmatch 'Music Video|Mixed|Live|Remix') {
        $invoke = $null
        if ($element.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$invoke)) {
            $result = $element
            break
        }
    }
}
if (-not $result) { throw 'No playable Apple Music song result was found.' }

$resultName = $result.Current.Name
$trackTitle = ($resultName -split '\s+Song\s*[·.]', 2)[0].Trim()
$resultInvoke = $null
$result.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$resultInvoke) | Out-Null
$resultInvoke.Invoke()
Start-Sleep -Seconds 2

$elements = Get-AllElements
$track = $null
for ($i = 0; $i -lt $elements.Count; $i++) {
    $element = $elements.Item($i)
    if ($element.Current.ControlType -eq [System.Windows.Automation.ControlType]::ListItem -and
        $element.Current.Name -match '^Track \d+ ' -and
        $element.Current.Name.IndexOf($trackTitle, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
        $invoke = $null
        if ($element.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$invoke)) {
            $track = $element
            break
        }
    }
}
if (-not $track) { throw "The exact album track '$trackTitle' was not found." }
$trackInvoke = $null
$track.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$trackInvoke) | Out-Null
$trackInvoke.Invoke()
Write-Output "APPLE_MUSIC_PLAY_COMPLETE: $trackTitle"
