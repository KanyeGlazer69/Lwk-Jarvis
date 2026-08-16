"""Dry-run the allowlist without launching any applications."""

from windows_actions import handle_action


safe_cases = {
    "open notepad": "open_notepad",
    "Please launch the calculator for me.": "open_calculator",
    "start file explorer": "open_file_explorer",
    "open settings": "open_settings",
    "open task manager": "open_task_manager",
    "can you open up the calculator app for me": "open_calculator",
}
for phrase, expected in safe_cases.items():
    result = handle_action(phrase, dry_run=True)
    assert result.matched and result.success and result.action == expected, (phrase, result)

blocked_cases = (
    "open powershell",
    "delete all my files",
    "shut down the computer",
    "restart windows",
    "run this command",
    "close task manager",
)
for phrase in blocked_cases:
    assert not handle_action(phrase, dry_run=True).matched, phrase

print("SAFE ACTION ALLOWLIST TEST PASSED")
print("DANGEROUS / UNLISTED ACTION REJECTION TEST PASSED")
