"""Jarvis Phase 2 wake-word listener using the official openWakeWord model."""

from __future__ import annotations

import argparse
import json
import pathlib
import queue
import sys
import time
import winsound

import numpy as np
import openwakeword
import sounddevice as sd
from openwakeword.model import Model


ROOT = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
REPORT_PATH = ROOT / "last-diagnostic.json"
SAMPLE_RATE = 16_000
CHUNK = 1_280


def load_config() -> dict:
    defaults = {
        "threshold": 0.50,
        "consecutive_hits": 2,
        "cooldown_seconds": 2.5,
        "input_device": None,
    }
    if CONFIG_PATH.is_file():
        defaults.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    threshold = float(defaults["threshold"])
    if not 0.05 <= threshold <= 0.99:
        raise ValueError("threshold must be between 0.05 and 0.99")
    defaults["threshold"] = threshold
    defaults["consecutive_hits"] = max(1, int(defaults["consecutive_hits"]))
    defaults["cooldown_seconds"] = max(0.5, float(defaults["cooldown_seconds"]))
    return defaults


def create_model() -> Model:
    path = pathlib.Path(openwakeword.MODELS["hey_jarvis"]["model_path"]).with_suffix(".onnx")
    if not path.is_file():
        raise FileNotFoundError("The official Hey Jarvis model is missing. Rerun Phase 2 setup.")
    return Model(wakeword_models=[str(path)], inference_framework="onnx")


def listen(mode: str, seconds: float | None) -> int:
    config = load_config()
    model = create_model()
    audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=32)
    overflows = 0

    def callback(indata, frames, time_info, status):
        nonlocal overflows
        if status:
            overflows += 1
        try:
            audio_queue.put_nowait(indata[:, 0].copy())
        except queue.Full:
            overflows += 1

    device = config["input_device"]
    info = sd.query_devices(device, "input")
    threshold = config["threshold"]
    needed_hits = config["consecutive_hits"]
    deadline = None if seconds is None else time.monotonic() + seconds
    highest = 0.0
    frames_processed = 0
    detections = 0
    hits = 0
    last_detection = -1e9

    print(f"Microphone: {info['name']}")
    print(f"Sensitivity threshold: {threshold:.2f}; confirmation frames: {needed_hits}")
    if mode == "listen":
        print('Listening continuously. Say "Hey Jarvis". Press Ctrl+C to stop.')
    elif mode == "test":
        print(f'LIVE TEST: say "Hey Jarvis" several times during the next {seconds:.0f} seconds.')
    else:
        print(f"Running a {seconds:.0f}-second no-speech false-trigger baseline...")

    started = time.monotonic()
    try:
        with sd.InputStream(
            device=device,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK,
            callback=callback,
        ):
            while deadline is None or time.monotonic() < deadline:
                try:
                    audio = audio_queue.get(timeout=1.0)
                except queue.Empty:
                    raise RuntimeError("No microphone audio arrived for one second.")
                scores = model.predict(audio)
                score = max(float(value) for value in scores.values())
                highest = max(highest, score)
                frames_processed += 1
                hits = hits + 1 if score >= threshold else 0
                now = time.monotonic()
                if hits >= needed_hits and now - last_detection >= config["cooldown_seconds"]:
                    detections += 1
                    last_detection = now
                    hits = 0
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] HEY JARVIS DETECTED (score {score:.3f})")
                    winsound.MessageBeep(winsound.MB_OK)
    except KeyboardInterrupt:
        print("Listener stopped.")

    report = {
        "mode": mode,
        "microphone": info["name"],
        "threshold": threshold,
        "duration_seconds": round(time.monotonic() - started, 2),
        "frames_processed": frames_processed,
        "highest_score": round(highest, 6),
        "detections": detections,
        "audio_status_events": overflows,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    if frames_processed < 5:
        print("FAILED: too few microphone frames were processed.", file=sys.stderr)
        return 1
    if mode == "baseline" and detections:
        print("FAILED: false wake detected during baseline.", file=sys.stderr)
        return 1
    if mode == "test" and not detections:
        print("NO WAKE DETECTED: rerun the test while awake, then tune sensitivity if needed.")
        return 2
    print("WAKE LISTENER TEST PASSED" if mode != "listen" else "Listener session complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--listen", action="store_true")
    modes.add_argument("--test-seconds", type=float)
    modes.add_argument("--baseline-seconds", type=float)
    args = parser.parse_args()
    if args.listen:
        return listen("listen", None)
    if args.test_seconds is not None:
        return listen("test", max(5.0, args.test_seconds))
    return listen("baseline", max(5.0, args.baseline_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
