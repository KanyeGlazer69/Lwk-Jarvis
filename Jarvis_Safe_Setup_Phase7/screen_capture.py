"""Explicit-only, in-memory screen capture for Jarvis visual requests."""

from __future__ import annotations

import re

VISUAL_PHRASES = (
    "look at my screen",
    "look at the screen",
    "look at monitor",
    "look at my monitor",
    "look at this",
    "what do you see",
    "describe my screen",
    "describe the screen",
    "describe my desktop",
    "describe my wallpaper",
    "see my screen",
    "see the screen",
)

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4}


def is_visual_request(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in VISUAL_PHRASES)


def requested_monitor(text: str, monitor_count: int) -> int:
    lowered = text.lower()
    if "all monitors" in lowered or "all screens" in lowered or "entire desktop" in lowered:
        return 0
    match = re.search(r"(?:monitor|screen)\s*(?:number\s*)?(\d+|one|two|three|four)\b", lowered)
    if match:
        token = match.group(1)
        number = int(token) if token.isdigit() else NUMBER_WORDS[token]
        if 1 <= number <= monitor_count:
            return number
        raise ValueError(f"Monitor {number} does not exist; Windows reports {monitor_count} monitor(s).")
    return 1


def capture_for_request(text: str) -> tuple[bytes, str]:
    if not is_visual_request(text):
        raise ValueError("The request did not contain an explicit visual phrase.")
    import mss
    import mss.tools

    with mss.mss() as capture:
        count = len(capture.monitors) - 1
        if count < 1:
            raise RuntimeError("Windows reported no capturable monitors.")
        index = requested_monitor(text, count)
        region = capture.monitors[index]
        shot = capture.grab(region)
        png = mss.tools.to_png(shot.rgb, shot.size)
        label = "all monitors" if index == 0 else f"monitor {index}"
        return png, f"Captured {label} at {shot.width}x{shot.height}; image was not saved to disk."
