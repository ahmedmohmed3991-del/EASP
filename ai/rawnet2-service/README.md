# Voice Deepfake Detection - RawNet2

**Component owner:** Abrar (AI 1)
**Task:** RawNet2, Voice Deepfake Detection

## Overview

This module detects whether a given audio clip is a genuine human voice
(`real`) or an AI-generated / spoofed voice (`fake`), using an end-to-end
RawNet2 model trained directly on the raw audio waveform.

## Model Details

- **Architecture:** RawNet2 (raw-waveform anti-spoofing model)
- **Training data:** ASVspoof 2019 - Logical Access (LA) partition
- **Training setup:** 20 epochs, batch size 24, learning rate 0.0001
- **Trained weights file:** `epoch_19.pth`

## Evaluation Results

Evaluated on the full ASVspoof 2019 LA evaluation set (71,237 trials):

| Metric | Value |
|---|---|
| EER (Equal Error Rate) | 6.08% |
| Accuracy (5,000-sample benchmark) | 91.22% |
| ROC-AUC (5,000-sample benchmark) | 0.9838 |

## Files

| File | Description |
|---|---|
| `rawnet2_deepfake_detector.py` | Main module - exposes `predict(audio_path)` |
| `model.py` | RawNet2 model architecture |
| `model_config_RawNet.yaml` | Model architecture configuration |
| `epoch_19.pth` | Trained model weights |
| `requirements.txt` | Python dependencies |

## Usage

```python
from rawnet2_deepfake_detector import predict

result = predict("path/to/audio.wav")
print(result)
# -> {"label": "real", "confidence": 0.97}
```

Before running, update the two path variables at the top of
`rawnet2_deepfake_detector.py`:

```python
RAWNET_CODE_DIR = "path/to/this/folder"       # folder containing model.py
MODEL_WEIGHTS_PATH = "path/to/epoch_19.pth"   # trained weights file
```

## Known Limitation

The model is trained on studio-quality (uncompressed) audio. Accuracy drops
on heavily compressed real-world audio (e.g. WhatsApp/Telegram voice notes
using the Opus/OGG codec) due to a channel/codec mismatch, a known
limitation documented in anti-spoofing literature. Potential future
improvement: fine-tuning with RawBoost data augmentation
(https://github.com/TakHemlata/RawBoost-antispoofing) to improve robustness
to compressed/real-world audio channels.
