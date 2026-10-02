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

    result = predict("some_audio_file.m4a")
    print(result)
    # -> {"label": "real", "confidence": 0.97}

Supported input formats: .wav, .flac, .mp3, .m4a, .ogg, .opus, ...
Any non-wav file is first converted to a 16kHz mono wav using ffmpeg
(this is "Solution 1": convert compressed audio to wav before inference).
The audio is then padded/trimmed to the model's expected input length.

NOTE: ffmpeg must be installed (Linux: sudo apt install ffmpeg,
Windows: download ffmpeg and add it to PATH).

------------------------------------------------------------------------------
REQUIRED FILES / PATHS
------------------------------------------------------------------------------
By default, model.py, model_config_RawNet.yaml and the weights file are
expected in the SAME folder as this script. To use other locations, set the
environment variables RAWNET_CODE_DIR and RAWNET_WEIGHTS_PATH, or edit the
two variables below.
"""
import os
import subprocess
import tempfile
import importlib.util
import numpy as np
import torch
import yaml
import librosa

# ==============================================================================
# CONFIGURATION
# ==============================================================================
_HERE = os.path.dirname(os.path.abspath(__file__))

RAWNET_CODE_DIR = os.environ.get("RAWNET_CODE_DIR", _HERE)   # folder with model.py
MODEL_WEIGHTS_PATH = os.environ.get(
    "RAWNET_WEIGHTS_PATH", os.path.join(_HERE, "epoch_19.pth")
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

def _convert_to_wav(audio_path: str) -> str:
    """Convert any audio format (m4a, ogg, mp3, ...) to a 16kHz mono wav via ffmpeg.

    Returns the path of a temporary wav file (the caller must delete it).
    """
    fd, out_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", audio_path,
             "-ar", str(SAMPLE_RATE), "-ac", "1", out_path],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        os.remove(out_path)
        raise RuntimeError(
            "ffmpeg is not installed. Install it first "
            "(Linux: sudo apt install ffmpeg | Windows: add ffmpeg to PATH)."
        )
    except subprocess.CalledProcessError as e:
        os.remove(out_path)
        raise RuntimeError(
            f"ffmpeg failed to convert '{audio_path}': "
            f"{e.stderr.decode(errors='ignore')}"
        )
    return out_path


def _load_and_pad_audio(audio_path: str) -> np.ndarray:
    """Convert to wav if needed, load at 16kHz, and pad/trim to a fixed length."""
    wav_path = audio_path
    converted = False
    if not audio_path.lower().endswith(".wav"):
        wav_path = _convert_to_wav(audio_path)
        converted = True

    try:
        waveform, _ = librosa.load(wav_path, sr=SAMPLE_RATE)
    finally:
        if converted:
            os.remove(wav_path)

    length = waveform.shape[0]
    if length == 0:
        raise ValueError(f"Audio file is empty: {audio_path}")

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
        Path to the audio file to classify (.wav, .flac, .mp3, .m4a, .ogg, ...)

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
