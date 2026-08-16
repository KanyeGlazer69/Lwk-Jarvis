"""Strictly allowlisted Opera GX and Apple Music voice controls."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import os
import pathlib
import re
import subprocess
import time
import urllib.parse


OPERA = pathlib.Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Opera GX" / "opera.exe"
KEYEVENTF_KEYUP = 0x0002
VK = {"ctrl": 0x11, "shift": 0x10, "enter": 0x0D, "l": 0x4C, "t": 0x54,
      "w": 0x57, "a": 0x41, "f": 0x46, "space": 0x20}
MEDIA = {"play pause": 0xB3, "pause": 0xB3, "play": 0xB3, "next": 0xB0,
         "previous": 0xB1, "volume up": 0xAF, "volume down": 0xAE}


@dataclass(frozen=True)
class Result:
    matched: bool
    success: bool = False
    action: str = ""
    message: str = ""


def _tap(code: int) -> None:
    ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(code, 0, KEYEVENTF_KEYUP, 0)


def _hotkey(*names: str) -> None:
    codes = [VK[name] for name in names]
    for code in codes:
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    for code in reversed(codes):
        ctypes.windll.user32.keybd_event(code, 0, KEYEVENTF_KEYUP, 0)


def _type(text: str) -> None:
    # SendKeys is used only with sanitized user text and a fixed target workflow.
    escaped = "".join("{" + c + "}" if c in "+^%~()[]{}" else c for c in text)
    safe = escaped.replace("'", "''")
    command = "Add-Type -AssemblyName System.Windows.Forms; [Windows.Forms.SendKeys]::SendWait('{}')".format(safe)
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                   check=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)


def _activate(title: str) -> bool:
    command = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f"[Microsoft.VisualBasic.Interaction]::AppActivate('{title.replace("'", "''")}')"
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                            capture_output=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
    return result.returncode == 0


def _opera_url(query: str) -> str:
    cleaned = query.strip().strip(".?!")
    if re.fullmatch(r"(?:https?://)?[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(?:/[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]*)?", cleaned, re.I):
        return cleaned if cleaned.lower().startswith(("http://", "https://")) else "https://" + cleaned
    return "https://www.google.com/search?q=" + urllib.parse.quote_plus(cleaned)


def _opera(transcript: str, dry_run: bool) -> Result:
    lower = transcript.lower().strip().rstrip(".?!")
    if not ("opera" in lower or "tab" in lower or lower.startswith("search ")):
        return Result(False)
    if re.fullmatch(r"(?:open|start|launch) opera(?: gx)?", lower):
        if not dry_run:
            subprocess.Popen([str(OPERA)])
        return Result(True, True, "opera.open", "Opening Opera GX.")
    if re.fullmatch(r"(?:open|new|create)(?: a)?(?: new)? tab(?: in opera)?", lower):
        if not dry_run:
            if not _activate("Opera"): return Result(True, False, "opera.new_tab", "Opera GX is not open.")
            _hotkey("ctrl", "t")
        return Result(True, True, "opera.new_tab", "Opening a new tab.")
    match = re.fullmatch(r"(?:search(?: for)?|look up) (.+?)(?: (?:in|on|with) opera(?: gx)?)", lower)
    if match:
        query = match.group(1).strip()
        if not query: return Result(True, False, "opera.search", "Tell me what to search for.")
        if not dry_run: subprocess.Popen([str(OPERA), _opera_url(query)])
        return Result(True, True, "opera.search", f"Searching Opera GX for {query}.")
    match = re.fullmatch(r"open (.+?) (?:in|on|with) opera(?: gx)?", lower)
    if match:
        target = match.group(1).strip()
        if not dry_run: subprocess.Popen([str(OPERA), _opera_url(target)])
        return Result(True, True, "opera.open_target", f"Opening {target} in Opera GX.")
    match = re.fullmatch(r"close (?:the )?tab (?:called|named|for) (.+?)(?: in opera)?", lower)
    if match:
        name = match.group(1).strip()
        if not dry_run:
            if not _activate("Opera"): return Result(True, False, "opera.close_named_tab", "Opera GX is not open.")
            _hotkey("ctrl", "shift", "a"); time.sleep(0.4); _type(name); time.sleep(0.4); _tap(VK["enter"]); time.sleep(0.4); _hotkey("ctrl", "w")
        return Result(True, True, "opera.close_named_tab", f"Closing the tab named {name}.")
    if re.fullmatch(r"close (?:this|the current) tab(?: in opera)?", lower):
        if not dry_run:
            if not _activate("Opera"): return Result(True, False, "opera.close_tab", "Opera GX is not open.")
            _hotkey("ctrl", "w")
        return Result(True, True, "opera.close_tab", "Closing the current Opera tab.")
    return Result(False)


def _apple_music(transcript: str, dry_run: bool) -> Result:
    lower = transcript.lower().strip().rstrip(".?!")
    if "apple music" not in lower and not re.fullmatch(r"(?:play|pause|next|previous)(?: song| track| music)?", lower):
        return Result(False)
    if re.fullmatch(r"(?:open|start|launch) apple music", lower):
        if not dry_run:
            _tap(0x5B); time.sleep(0.5); _type("Apple Music"); time.sleep(0.7); _tap(VK["enter"])
        return Result(True, True, "music.open", "Opening Apple Music.")
    match = re.fullmatch(r"search apple music for (.+)", lower)
    if not match:
        match = re.fullmatch(r"(?:search for|find|play) (.+?) (?:on|in) apple music", lower)
    if match:
        song = match.group(1).strip()
        if not dry_run:
            if not _activate("Apple Music"): return Result(True, False, "music.search", "Open Apple Music first, then ask me again.")
            _hotkey("ctrl", "f"); time.sleep(0.3); _type(song); time.sleep(0.3); _tap(VK["enter"])
        return Result(True, True, "music.search", f"Searching Apple Music for {song}.")
    action_match = re.fullmatch(r"(play pause|play|pause|next|previous|volume up|volume down)(?: (?:song|track|music))?(?: (?:on|in) apple music)?", lower)
    if action_match:
        action = action_match.group(1)
        if not dry_run: _tap(MEDIA[action])
        spoken = {"next": "Skipping to the next song.", "previous": "Going to the previous song.",
                  "volume up": "Turning the volume up.", "volume down": "Turning the volume down."}.get(action, "Toggling playback.")
        return Result(True, True, f"music.{action.replace(' ', '_')}", spoken)
    return Result(False)


def handle_action(transcript: str, dry_run: bool = False) -> Result:
    return _opera(transcript, dry_run) if _opera(transcript, True).matched else _apple_music(transcript, dry_run)
