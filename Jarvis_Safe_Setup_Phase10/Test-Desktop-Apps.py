from desktop_apps import handle_action

allowed = [
    "open Opera GX", "open a new tab in Opera", "search for weather in Opera",
    "open youtube.com in Opera", "close the tab named YouTube in Opera",
    "close the current tab", "open Apple Music", "play music", "next song",
    "previous track", "volume up on Apple Music", "search Apple Music for Billie Jean",
    "play Kanye West Flashing Lights", "play my mood playlist in Apple Music",
]
for phrase in allowed:
    result = handle_action(phrase, dry_run=True)
    assert result.matched and result.success, (phrase, result)
blocked = ["delete my files", "buy this song", "enter my password", "run PowerShell", "close Opera"]
for phrase in blocked:
    assert not handle_action(phrase, dry_run=True).matched, phrase
print("PHASE 10 COMMAND ALLOWLIST TEST PASSED")
