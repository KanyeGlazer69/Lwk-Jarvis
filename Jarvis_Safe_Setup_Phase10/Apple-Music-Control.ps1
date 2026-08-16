[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Query,
    [switch]$Play,
    [switch]$Playlist
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class JarvisAppleMusicMouse {
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X; public int Y; }
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT point);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
}
'@

$process = Get-Process | Where-Object { $_.MainWindowTitle -match 'Apple Music' } | Select-Object -First 1
if (-not $process) { throw 'Apple Music window not found.' }
$root = [System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
$trueCondition = [System.Windows.Automation.Condition]::TrueCondition

function Get-AllElements {
    $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $trueCondition)
}

if ($Playlist) {
    $elements = Get-AllElements
    $libraryPlaylist = $null
    for ($i = 0; $i -lt $elements.Count; $i++) {
        $element = $elements.Item($i)
        $patterns = $element.GetSupportedPatterns()
        if ($element.Current.ControlType -eq [System.Windows.Automation.ControlType]::ListItem -and
            $element.Current.Name -ieq $Query -and
            $patterns -contains [System.Windows.Automation.SelectionItemPattern]::Pattern -and
            $patterns -notcontains [System.Windows.Automation.InvokePattern]::Pattern) {
            $libraryPlaylist = $element
            break
        }
    }
    if (-not $libraryPlaylist) { throw "The Library playlist '$Query' was not found." }
    $selection = $null
    $libraryPlaylist.TryGetCurrentPattern(
        [System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$selection
    ) | Out-Null
    $selection.Select()
    Start-Sleep -Seconds 2
    $elements = Get-AllElements
    $playButton = $null
    for ($i = 0; $i -lt $elements.Count; $i++) {
        $element = $elements.Item($i)
        if ($element.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button -and
            $element.Current.Name -eq 'Play' -and $element.Current.AutomationId -eq 'PlayButton') {
            $playButton = $element
            break
        }
    }
    if (-not $playButton) { throw "The Play button for '$Query' was not found." }
    $invoke = $null
    $playButton.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$invoke) | Out-Null
    $invoke.Invoke()
    Start-Sleep -Seconds 2
    $elements = Get-AllElements
    $pauseVisible = $false
    for ($i = 0; $i -lt [Math]::Min($elements.Count, 75); $i++) {
        if ($elements.Item($i).Current.Name -eq 'Pause') { $pauseVisible = $true; break }
    }
    if (-not $pauseVisible) { throw "Playlist '$Query' was selected but playback was not verified." }
    Write-Output "APPLE_MUSIC_PLAYLIST_VERIFIED: $Query"
    exit 0
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

$scrollPattern = $null
if ($track.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern, [ref]$scrollPattern)) {
    $scrollPattern.ScrollIntoView()
    Start-Sleep -Milliseconds 200
}
$bounds = $track.Current.BoundingRectangle
if ($bounds.IsEmpty) { throw 'The exact track row is not visible.' }
$oldCursor = New-Object JarvisAppleMusicMouse+POINT
[JarvisAppleMusicMouse]::GetCursorPos([ref]$oldCursor) | Out-Null
try {
    $x = [int]($bounds.Left + ($bounds.Width / 2))
    $y = [int]($bounds.Top + ($bounds.Height / 2))
    [JarvisAppleMusicMouse]::SetCursorPos($x, $y) | Out-Null
    [JarvisAppleMusicMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
    [JarvisAppleMusicMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 120
    [JarvisAppleMusicMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
    [JarvisAppleMusicMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
}
finally {
    [JarvisAppleMusicMouse]::SetCursorPos($oldCursor.X, $oldCursor.Y) | Out-Null
}

Start-Sleep -Seconds 2
$elements = Get-AllElements
$pauseVisible = $false
$titleVisible = $false
for ($i = 0; $i -lt $elements.Count; $i++) {
    $name = $elements.Item($i).Current.Name
    if ($name -eq 'Pause') { $pauseVisible = $true }
    if ($name -and $name.IndexOf($trackTitle, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
        $titleVisible = $true
    }
}
if (-not ($pauseVisible -and $titleVisible)) {
    throw "Apple Music selected '$trackTitle' but playback was not verified."
}
Write-Output "APPLE_MUSIC_PLAYBACK_VERIFIED: $trackTitle"
