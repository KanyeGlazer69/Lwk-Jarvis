"""Short, non-recording-retained microphone test for Jarvis Phase 1."""

import sys

import numpy as np
import sounddevice as sd


def main() -> None:
    devices = sd.query_devices()
    inputs = [d for d in devices if int(d["max_input_channels"]) > 0]
    if not inputs:
        raise RuntimeError("Windows reported no microphone input devices.")

    default_input = sd.default.device[0]
    if default_input is None or int(default_input) < 0:
        raise RuntimeError("No default microphone is selected in Windows sound settings.")

    info = sd.query_devices(int(default_input), "input")
    sample_rate = int(info["default_samplerate"] or 16000)
    print(f"Default microphone: {info['name']}")
    print("Capturing one second for a local level check (audio is not saved)...")
    audio = sd.rec(sample_rate, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    print(f"Microphone capture: OK (peak level {peak:.4f})")
    if peak < 0.00001:
        print("Note: the capture was silent; check mute/privacy settings if this was unexpected.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Microphone diagnostic failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
