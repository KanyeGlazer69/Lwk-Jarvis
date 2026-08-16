"""Strictly allowlisted local Windows actions for Jarvis."""

from __future__ import annotations

import dataclasses
import re
import subprocess


@dataclasses.dataclass(frozen=True)
class ActionResult:
    matched: bool
    success: bool = False
    message: str = ""
    action: str = ""


APP_ALIASES = {
    "notepad": ("Notepad", ["notepad.exe"]),
    "calculator": ("Calculator", ["calc.exe"]),
    "calc": ("Calculator", ["calc.exe"]),
    "file explorer": ("File Explorer", ["explorer.exe"]),
    "explorer": ("File Explorer", ["explorer.exe"]),
    "settings": ("Settings", ["explorer.exe", "ms-settings:"]),
    "windows settings": ("Settings", ["explorer.exe", "ms-settings:"]),
    "task manager": ("Task Manager", ["taskmgr.exe"]),
}

OPEN_PATTERN = re.compile(
    r"^\s*(?:please\s+)?(?:open|launch|start)\s+(?:the\s+)?"
    r"(?P<app>notepad|calculator|calc|file explorer|explorer|settings|windows settings|task manager)"
    r"(?:\s+for\s+me)?[.!?]*\s*$",
    re.IGNORECASE,
)


def parse_action(text: str) -> tuple[str, str, list[str]] | None:
    match = OPEN_PATTERN.match(text)
    if not match:
        return None
    alias = match.group("app").lower()
    display_name, command = APP_ALIASES[alias]
    return f"open_{display_name.lower().replace(' ', '_')}", display_name, command


def handle_action(text: str, dry_run: bool = False) -> ActionResult:
    parsed = parse_action(text)
    if parsed is None:
        return ActionResult(matched=False)
    action, display_name, command = parsed
    if dry_run:
        return ActionResult(True, True, f"I would open {display_name}.", action)
    try:
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except OSError as exc:
        return ActionResult(True, False, f"I couldn't open {display_name}: {exc}", action)
    return ActionResult(True, True, f"Opening {display_name}.", action)
