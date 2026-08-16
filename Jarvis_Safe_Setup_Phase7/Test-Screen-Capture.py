"""Capture locally, verify dimensions, discard bytes, and never upload or save."""

from screen_capture import capture_for_request


image, details = capture_for_request("look at my screen")
if not image.startswith(b"\x89PNG\r\n\x1a\n"):
    raise RuntimeError("Captured image is not a valid PNG stream.")
if len(image) < 1000:
    raise RuntimeError("Captured PNG is unexpectedly small.")
print(details)
print(f"In-memory PNG size: {len(image)} bytes")
del image
print("LOCAL SCREEN CAPTURE SELF-TEST PASSED; IMAGE DISCARDED")
