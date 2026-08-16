"""Strictly allowlisted local Windows actions for Jarvis."""

from __future__ import annotations

import dataclasses
import os
import pathlib
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
    "roblox": ("Roblox", None),
    "roblox player": ("Roblox", None),
}

OPEN_PATTERN = re.compile(
    r"^\s*(?:(?:please|can you|could you|would you)\s+)?(?:open(?:\s+up)?|launch|start)\s+(?:the\s+)?"
    r"(?P<app>notepad|calculator|calc|file explorer|explorer|settings|windows settings|task manager|roblox player|roblox)"
    r"(?:\s+(?:app|application))?(?:\s+for\s+me)?[.!?]*\s*$",
    re.IGNORECASE,
)

FILE_PATTERN = re.compile(
    r"^\s*(?:(?:please|can you|could you|would you)\s+)?open\s+"
    r"(?:my\s+)?(?:the\s+)?(?:file\s+)?(?:named\s+|called\s+)?(?P<name>.+?)[.!?]*\s*$",
    re.IGNORECASE,
)
BLOCKED_FILE_SUFFIXES = {
    ".exe", ".msi", ".msix", ".appx", ".bat", ".cmd", ".ps1", ".psm1",
    ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".scr", ".com", ".dll",
    ".sys", ".drv", ".reg", ".lnk", ".url", ".cpl",
}
BLOCKED_FILE_REQUESTS = {"powershell", "command prompt", "cmd", "terminal", "registry editor", "regedit"}


def personal_roots() -> list[pathlib.Path]:
    profile = pathlib.Path(os.environ["USERPROFILE"])
    candidates = [profile / name for name in
                  ("Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos", "OneDrive")]
    return [path.resolve() for path in candidates if path.is_dir()]


def find_personal_file(requested: str) -> tuple[pathlib.Path | None, str | None]:
    wanted = requested.strip().strip('"').strip("'")
    wanted_lower = wanted.casefold()
    exact: list[pathlib.Path] = []
    partial: list[pathlib.Path] = []
    for root in personal_roots():
        for folder, directories, files in os.walk(root):
            directories[:] = [name for name in directories
                              if not name.startswith(".") and name.lower() not in {"node_modules", "appdata"}]
            for filename in files:
                path = pathlib.Path(folder) / filename
                if path.suffix.lower() in BLOCKED_FILE_SUFFIXES or filename.startswith("."):
                    continue
                if filename.casefold() == wanted_lower or path.stem.casefold() == wanted_lower:
                    exact.append(path)
                elif wanted_lower in filename.casefold():
                    partial.append(path)
    matches = exact or partial
    unique = list(dict.fromkeys(path.resolve() for path in matches))
    if not unique:
        return None, "I couldn't find that personal file."
    if len(unique) > 1:
        return None, f"I found {len(unique)} matching personal files. Please say the full file name."
    return unique[0], None


def parse_action(text: str) -> tuple[str, str, list[str] | None] | None:
    match = OPEN_PATTERN.match(text)
    if not match:
        return None
    alias = match.group("app").lower()
    display_name, command = APP_ALIASES[alias]
    return f"open_{display_name.lower().replace(' ', '_')}", display_name, command


def find_roblox() -> list[str] | None:
    versions = pathlib.Path(os.environ["LOCALAPPDATA"]) / "Roblox" / "Versions"
    try:
        candidates = sorted(versions.glob("version-*/RobloxPlayerBeta.exe"),
                            key=lambda path: path.stat().st_mtime, reverse=True)
    except OSError:
        return None
    return [str(candidates[0])] if candidates else None


def handle_action(text: str, dry_run: bool = False) -> ActionResult:
    parsed = parse_action(text)
    if parsed is None:
        file_match = FILE_PATTERN.match(text)
        if not file_match:
            return ActionResult(matched=False)
        requested = file_match.group("name").strip()
        if requested.casefold() in BLOCKED_FILE_REQUESTS:
            return ActionResult(matched=False)
        if pathlib.Path(requested).suffix.lower() in BLOCKED_FILE_SUFFIXES:
            return ActionResult(True, False, "I won't open executable, script, shortcut, or system file types.",
                                "open_personal_file")
        if dry_run:
            return ActionResult(True, True, f"I would open the personal file {requested}.", "open_personal_file")
        path, error = find_personal_file(requested)
        if error:
            return ActionResult(True, False, error, "open_personal_file")
        subprocess.Popen(["explorer.exe", str(path)], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        return ActionResult(True, True, f"Opening {path.name}.", "open_personal_file")
    action, display_name, command = parsed
    if dry_run:
        return ActionResult(True, True, f"I would open {display_name}.", action)
    if display_name == "Roblox":
        command = find_roblox()
    if not command:
        return ActionResult(True, False, f"I couldn't find the installed {display_name} launcher.", action)
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
