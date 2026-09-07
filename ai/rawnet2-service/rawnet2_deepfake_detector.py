"""
RawNet2 Voice Deepfake Detection Module
=========================================
Author: Abrar (AI Team 1)
Project: Graduation Project - Voice Deepfake / Social Engineering Detection

This module wraps a RawNet2 model (trained on ASVspoof 2019 - Logical Access)
into a single, easy-to-use function: `predict(audio_path)`.

It classifies a given audio file as either:
    - "real"  -> genuine human speech (bona fide)
    - "fake"  -> AI-generated / spoofed speech (deepfake)

------------------------------------------------------------------------------
MODEL DETAILS
------------------------------------------------------------------------------
- Architecture : RawNet2 (end-to-end, raw-waveform based anti-spoofing model)
- Training data: ASVspoof 2019 LA (Logical Access) partition
- Epochs       : 20
- Batch size   : 24
- Learning rate: 0.0001
- Result       : EER (Equal Error Rate) = 6.08% on the ASVspoof 2019 LA
                 evaluation set (71,237 trials)

------------------------------------------------------------------------------
HOW TO USE (for integration, e.g. by the FastAPI/backend team)
------------------------------------------------------------------------------
    from rawnet2_deepfake_detector import predict

    result = predict("some_audio_file.wav")
    print(result)
    # -> {"label": "real", "confidence": 0.97}

The function accepts any common audio format supported by librosa
(.wav, .flac, .mp3, .m4a, etc.). It automatically resamples to 16kHz
and pads/trims the audio to match the model's expected input length.

------------------------------------------------------------------------------
REQUIRED FILES / PATHS (must be adjusted to your environment)
------------------------------------------------------------------------------
1. RawNet2 source code (model.py + model_config_RawNet.yaml) from:
   https://github.com/asvspoof-challenge/2021  (LA/Baseline-RawNet2 folder)

2. Trained model weights file: epoch_19.pth
   (produced by training the RawNet2 baseline on ASVspoof 2019 LA for 20 epochs)

Update the two path variables below (RAWNET_CODE_DIR, MODEL_WEIGHTS_PATH)
to point to wherever these files live in the deployment environment.
"""

import importlib.util
import numpy as np
import torch
import yaml
import librosa

# ==============================================================================
# CONFIGURATION - update these two paths for your environment
# ==============================================================================
RAWNET_CODE_DIR = "/content/2021/LA/Baseline-RawNet2"          # folder with model.py
MODEL_WEIGHTS_PATH = (
    "/content/drive/MyDrive/graduation_project_rawnet2/models/"
    "model_LA_weighted_CCE_20_24_0.0001_rawnet2_graduation_project/epoch_19.pth"
)

SEGMENT_LENGTH = 64600   # 4 seconds at 16kHz sample rate (matches training setup)
SAMPLE_RATE = 16000

# ==============================================================================
# MODEL LOADING (runs once when this module is imported)
# ==============================================================================

def _load_rawnet_class(code_dir: str):
    """Dynamically import the RawNet class from model.py without relying on sys.path."""
    spec = importlib.util.spec_from_file_location("model", f"{code_dir}/model.py")
    model_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_module)
    return model_module.RawNet


def _load_model(code_dir: str, weights_path: str):
    """Build the RawNet2 architecture and load the trained weights."""
    RawNet = _load_rawnet_class(code_dir)

    with open(f"{code_dir}/model_config_RawNet.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = RawNet(config["model"], device).to(device)
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()

    return model, device


# Load once at import time and keep in memory (avoids reloading on every call)
_model, _device = _load_model(RAWNET_CODE_DIR, MODEL_WEIGHTS_PATH)
print(f"[rawnet2_deepfake_detector] Model loaded successfully on device: {_device}")


# ==============================================================================
# AUDIO PREPROCESSING
# ==============================================================================

def _load_and_pad_audio(audio_path: str) -> np.ndarray:
    """Load an audio file, resample to 16kHz, and pad/trim to a fixed length."""
    waveform, _ = librosa.load(audio_path, sr=SAMPLE_RATE)

    length = waveform.shape[0]
    if length >= SEGMENT_LENGTH:
        waveform = waveform[:SEGMENT_LENGTH]
    else:
        num_repeats = int(SEGMENT_LENGTH / length) + 1
        waveform = np.tile(waveform, num_repeats)[:SEGMENT_LENGTH]

    return waveform


# ==============================================================================
# PUBLIC API
# ==============================================================================

def predict(audio_path: str) -> dict:
    """
    Classify an audio file as real (genuine human voice) or fake (AI-generated).

    Parameters
    ----------
    audio_path : str
        Path to the audio file to classify (.wav, .flac, .mp3, etc.)

    Returns
    -------
    dict
        {
            "label": "real" | "fake",
            "confidence": float   # value between 0 and 1
        }
    """
    waveform = _load_and_pad_audio(audio_path)
    input_tensor = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0).to(_device)

    with torch.no_grad():
        output = _model(input_tensor)
        probabilities = torch.softmax(output, dim=1)[0]
        fake_prob = probabilities[0].item()
        real_prob = probabilities[1].item()

    if real_prob > fake_prob:
        return {"label": "real", "confidence": round(real_prob, 4)}
    else:
        return {"label": "fake", "confidence": round(fake_prob, 4)}


# ==============================================================================
# QUICK TEST (only runs if this file is executed directly, not on import)
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python rawnet2_deepfake_detector.py <path_to_audio_file>")
    else:
        test_path = sys.argv[1]
        result = predict(test_path)
        print(f"File: {test_path}")
        print(f"Prediction: {result['label'].upper()}  (confidence: {result['confidence']*100:.2f}%)")
