"""Download and load Jarvis's high-accuracy distilled English speech model."""

import pathlib

import numpy as np
from faster_whisper import WhisperModel


root = pathlib.Path(__file__).resolve().parent
model_root = root / "models"
model_root.mkdir(parents=True, exist_ok=True)

model = WhisperModel(
    "distil-large-v3",
    device="cpu",
    compute_type="int8",
    download_root=str(model_root),
    cpu_threads=4,
)
segments, _ = model.transcribe(
    np.zeros(16_000, dtype=np.float32),
    language="en",
    beam_size=5,
    vad_filter=True,
)
list(segments)  # Force inference; faster-whisper returns a lazy generator.
print(f"Speech model directory: {model_root}")
print("LOCAL DISTIL-LARGE-V3 SPEECH MODEL SELF-TEST PASSED")
