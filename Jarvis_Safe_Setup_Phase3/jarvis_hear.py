"""Wake, record until natural silence, and transcribe locally for Jarvis Phase 3."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import queue
import re
import sys
import time
import winsound

import numpy as np
import openwakeword
import sounddevice as sd
from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeModel


ROOT = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
MODEL_ROOT = ROOT / "models"
LAST_TEXT = ROOT / "last-transcript.txt"
LAST_REPORT = ROOT / "last-transcription.json"
SAMPLE_RATE = 16_000
CHUNK = 1_280  # 80 ms; the native openWakeWord frame size.
SPEECH_MODEL_NAME = "small.en"


def load_config() -> dict:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["wake_threshold"] = float(config["wake_threshold"])
    config["wake_consecutive_hits"] = max(1, int(config["wake_consecutive_hits"]))
    config["speech_start_timeout_seconds"] = max(2.0, float(config["speech_start_timeout_seconds"]))
    config["silence_to_finish_seconds"] = max(0.6, float(config["silence_to_finish_seconds"]))
    config["maximum_utterance_seconds"] = max(5.0, float(config["maximum_utterance_seconds"]))
    return config


def rms(frame: np.ndarray) -> float:
    values = frame.astype(np.float32)
    return float(np.sqrt(np.mean(values * values))) if values.size else 0.0


def drain_audio_queue(audio_queue: queue.Queue) -> None:
    while True:
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            return


def create_wake_model() -> WakeModel:
    path = pathlib.Path(openwakeword.MODELS["hey_jarvis"]["model_path"]).with_suffix(".onnx")
    if not path.is_file():
        raise FileNotFoundError("Phase 2's official Hey Jarvis model is missing.")
    return WakeModel(wakeword_models=[str(path)], inference_framework="onnx")


def create_speech_model() -> WhisperModel:
    return WhisperModel(
        SPEECH_MODEL_NAME,
        device="cpu",
        compute_type="int8",
        download_root=str(MODEL_ROOT),
        local_files_only=True,
        cpu_threads=4,
    )


def capture_utterance(audio_queue: queue.Queue, config: dict, noise_floor: float) -> tuple[np.ndarray, dict]:
    threshold = max(float(config["minimum_energy"]), noise_floor * float(config["noise_multiplier"]))
    start_deadline = time.monotonic() + config["speech_start_timeout_seconds"]
    max_frames = int(config["maximum_utterance_seconds"] * SAMPLE_RATE / CHUNK)
    silence_frames_needed = int(config["silence_to_finish_seconds"] * SAMPLE_RATE / CHUNK)
    frames: list[np.ndarray] = []
    speech_started = False
    silent_frames = 0
    speech_frames = 0

    print(f"Speak now. Recording stops after {config['silence_to_finish_seconds']:.1f}s of silence.")
    while len(frames) < max_frames:
        try:
            frame = audio_queue.get(timeout=1.0)
        except queue.Empty as exc:
            raise RuntimeError("Microphone audio stopped during recording.") from exc
        energy = rms(frame)
        is_speech = energy >= threshold

        if not speech_started:
            if is_speech:
                speech_started = True
            elif time.monotonic() >= start_deadline:
                raise RuntimeError("No speech was heard after the wake word.")

        if speech_started:
            frames.append(frame)
            if is_speech:
                speech_frames += 1
                silent_frames = 0
            else:
                silent_frames += 1
                if silent_frames >= silence_frames_needed:
                    if silent_frames:
                        frames = frames[:-silent_frames]
                    break

    if not frames or speech_frames < 2:
        raise RuntimeError("The captured utterance was too short to transcribe.")
    audio = np.concatenate(frames).astype(np.float32) / 32768.0
    details = {
        "noise_floor_rms": round(noise_floor, 2),
        "speech_threshold_rms": round(threshold, 2),
        "captured_seconds": round(audio.size / SAMPLE_RATE, 2),
        "speech_frames": speech_frames,
    }
    return audio, details


def clean_transcript(text: str) -> str:
    text = re.sub(r"^\s*(?:hey\s+)?jarvis[,.!?;:\s-]*", "", text, flags=re.IGNORECASE)
    return text.strip()


def transcribe(model: WhisperModel, audio: np.ndarray) -> tuple[str, float]:
    started = time.monotonic()
    segments, _ = model.transcribe(
        audio,
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
        without_timestamps=True,
        initial_prompt=(
            "Jarvis voice commands. Examples: Play Can't Tell Me Nothing by Kanye West. "
            "Play a song in Apple Music. Play music. Pause music. Next song. "
            "Search Google in Opera GX."
        ),
    )
    text = clean_transcript(" ".join(segment.text.strip() for segment in segments).strip())
    return text, time.monotonic() - started


def run(once: bool) -> int:
    config = load_config()
    wake_model = create_wake_model()
    print(f"Loading the local {SPEECH_MODEL_NAME} high-accuracy speech model...")
    speech_model = create_speech_model()
    audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=64)
    recent_energy: collections.deque[float] = collections.deque(maxlen=125)
    overflows = 0

    def callback(indata, frames, time_info, status):
        nonlocal overflows
        if status:
            overflows += 1
        try:
            audio_queue.put_nowait(indata[:, 0].copy())
        except queue.Full:
            overflows += 1

    info = sd.query_devices(config["input_device"], "input")
    print(f"Microphone: {info['name']}")
    print('Ready. Say "Hey Jarvis", wait for the beep, then speak naturally.')
    hits = 0
    last_wake = -1e9
    interactions = 0

    try:
        with sd.InputStream(
            device=config["input_device"],
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK,
            callback=callback,
        ):
            while True:
                try:
                    frame = audio_queue.get(timeout=1.0)
                except queue.Empty as exc:
                    raise RuntimeError("No microphone audio arrived for one second.") from exc
                recent_energy.append(rms(frame))
                score = max(float(value) for value in wake_model.predict(frame).values())
                hits = hits + 1 if score >= config["wake_threshold"] else 0
                now = time.monotonic()
                if hits < config["wake_consecutive_hits"] or now - last_wake < config["wake_cooldown_seconds"]:
                    continue

                last_wake = now
                hits = 0
                interactions += 1
                print(f"HEY JARVIS DETECTED (score {score:.3f})")
                winsound.MessageBeep(winsound.MB_OK)
                noise_floor = float(np.median(recent_energy)) if recent_energy else 0.0
                drain_audio_queue(audio_queue)
                try:
                    audio, capture = capture_utterance(audio_queue, config, noise_floor)
                    text, elapsed = transcribe(speech_model, audio)
                    if not text:
                        raise RuntimeError("Speech was recorded, but no words could be transcribed.")
                    report = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "microphone": info["name"],
                        "transcript": text,
                        "transcription_seconds": round(elapsed, 2),
                        "audio_status_events": overflows,
                        **capture,
                    }
                    LAST_TEXT.write_text(text + "\n", encoding="utf-8")
                    LAST_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
                    print(f"TRANSCRIPT: {text}")
                    print(f"Local transcription time: {elapsed:.2f}s")
                    print("PHASE 3 LIVE TEST PASSED")
                    if once:
                        return 0
                    drain_audio_queue(audio_queue)
                    wake_model.reset()
                    recent_energy.clear()
                    hits = 0
                    last_wake = time.monotonic()
                    print('Ready again. Say "Hey Jarvis".')
                except RuntimeError as exc:
                    print(f"Interaction failed: {exc}", file=sys.stderr)
                    if once:
                        return 2
                    drain_audio_queue(audio_queue)
                    wake_model.reset()
                    recent_energy.clear()
                    hits = 0
                    last_wake = time.monotonic()
                    print('Ready again. Say "Hey Jarvis".')
    except KeyboardInterrupt:
        print("Jarvis hearing stopped.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Exit after one wake-and-transcribe interaction")
    args = parser.parse_args()
    return run(args.once)


if __name__ == "__main__":
    raise SystemExit(main())
