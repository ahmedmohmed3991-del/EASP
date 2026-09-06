"""
Generates synthetic & simulated bona-fide audio samples for quick local pipeline verification
and end-to-end testing of the spectrogram CNN and EER evaluation.
"""
import numpy as np
import soundfile as sf
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLE_DIR = BASE_DIR / "data" / "audio_deepfake" / "in_the_wild" / "samples"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def generate_sample_audio_benchmark():
    sr = 16000
    duration = 4.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    metadata = []
    
    # 1. Generate 10 Bona Fide (Human Voice Simulation: natural harmonic formant frequencies)
    print("Generating simulated bona-fide speech samples...")
    for i in range(1, 11):
        f0 = 120 + (i * 12) # Pitch variation
        harmonic = (
            0.6 * np.sin(2 * np.pi * f0 * t) +
            0.3 * np.sin(2 * np.pi * 2 * f0 * t) +
            0.15 * np.sin(2 * np.pi * 3 * f0 * t) +
            0.08 * np.sin(2 * np.pi * 4 * f0 * t)
        )
        # Add slight natural envelope
        envelope = np.exp(-0.5 * (t - duration/2)**2)
        audio = (harmonic * envelope + np.random.normal(0, 0.005, len(t))).astype(np.float32)
        
        filename = f"bonafide_{i:02d}.wav"
        file_path = SAMPLE_DIR / filename
        sf.write(str(file_path), audio, sr)
        
        metadata.append({
            "speaker_id": f"speaker_{i:02d}",
            "filename": str(file_path.relative_to(BASE_DIR)),
            "label": 0, # Bona fide
            "type": "bona_fide"
        })

    # 2. Generate 10 Deepfake (Synthetic Voice Simulation: high-frequency phase discontinuities / vocoder artifacts)
    print("Generating simulated synthetic vocoder deepfake samples...")
    for i in range(1, 11):
        f0 = 130 + (i * 10)
        # Vocoder robotic phase artifacts
        harmonic = (
            0.5 * np.sin(2 * np.pi * f0 * t) +
            0.4 * np.sin(2 * np.pi * 2 * f0 * t + np.pi/4) +
            0.2 * np.sin(2 * np.pi * 3.5 * f0 * t) # Non-integer harmonic artifact
        )
        # Add high-frequency buzz
        buzz = 0.05 * np.sin(2 * np.pi * 4000 * t)
        audio = (harmonic + buzz + np.random.normal(0, 0.015, len(t))).astype(np.float32)
        
        filename = f"deepfake_{i:02d}.wav"
        file_path = SAMPLE_DIR / filename
        sf.write(str(file_path), audio, sr)
        
        metadata.append({
            "speaker_id": f"synth_model_{i:02d}",
            "filename": str(file_path.relative_to(BASE_DIR)),
            "label": 1, # Spoof / Deepfake
            "type": "synthetic_deepfake"
        })

    meta_df = pd.DataFrame(metadata)
    meta_df.to_csv(BASE_DIR / "data" / "audio_deepfake" / "in_the_wild" / "meta.csv", index=False)
    print(f"[OK] Saved {len(metadata)} audio samples and metadata to {SAMPLE_DIR}")
    return meta_df

if __name__ == "__main__":
    generate_sample_audio_benchmark()
