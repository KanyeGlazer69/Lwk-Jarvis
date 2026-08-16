"""Download and validate only the official openWakeWord Hey Jarvis model set."""

import pathlib

import numpy as np
import openwakeword
from openwakeword.model import Model
from openwakeword.utils import download_models


download_models(["hey_jarvis"])
model_path = pathlib.Path(openwakeword.MODELS["hey_jarvis"]["model_path"]).with_suffix(".onnx")
if not model_path.is_file():
    raise RuntimeError(f"Official Hey Jarvis ONNX model was not downloaded: {model_path}")

model = Model(wakeword_models=[str(model_path)], inference_framework="onnx")
prediction = {}
for _ in range(20):
    prediction = model.predict(np.zeros(1280, dtype=np.int16))
if not any("jarvis" in key.lower() for key in prediction):
    raise RuntimeError(f"Unexpected prediction labels: {list(prediction)}")

print(f"Official Hey Jarvis model: {model_path}")
print(f"Model labels: {', '.join(prediction)}")
print("MODEL SELF-TEST PASSED")
