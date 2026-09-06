"""
Downloads real voice samples and deepfake audio files from HuggingFace
and saves them as genuine WAV files in data/audio_deepfake/in_the_wild/.
Uses raw audio byte stream to decode cleanly with soundfile.
"""
import io
import os
import soundfile as sf
import pandas as pd
from pathlib import Path
from datasets import load_dataset, Audio

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUT_DIR = BASE_DIR / "data" / "audio_deepfake" / "in_the_wild"
REAL_AUDIO_DIR = OUT_DIR / "release_in_the_wild"
REAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def fetch_and_save_real_audio_dataset():
    print("--- Fetching Real Audio Deepfake Benchmark (HuggingFace) ---")
    try:
        ds = load_dataset("garystafford/deepfake-audio-detection", split="train")
        ds = ds.cast_column("audio", Audio(decode=False))
        print(f"Loaded dataset with {len(ds)} audio recordings!")
        
        meta_rows = []
        for i, item in enumerate(ds):
            audio_info = item["audio"]
            audio_bytes = audio_info["bytes"]
            
            # Decode audio using soundfile from bytes
            data, sr = sf.read(io.BytesIO(audio_bytes))
            
            label_name = str(item.get("label", "unknown")).lower()
            is_deepfake = 1 if ("fake" in label_name or item.get("is_fake", False) or item.get("label") == 1) else 0
            speaker_id = str(item.get("speaker_id") or f"speaker_{i % 50:03d}")
            
            filename = f"audio_{i:04d}_{'deepfake' if is_deepfake else 'bonafide'}.wav"
            file_path = REAL_AUDIO_DIR / filename
            
            sf.write(str(file_path), data, sr)
            
            meta_rows.append({
                "speaker_id": speaker_id,
                "filename": str(file_path.relative_to(BASE_DIR)),
                "label": is_deepfake,
                "type": "deepfake" if is_deepfake else "bona_fide",
                "sample_rate": sr
            })
            
            if (i + 1) % 100 == 0 or (i + 1) == len(ds):
                print(f"  Extracted & saved {i + 1}/{len(ds)} real audio WAV files...", flush=True)

        meta_df = pd.DataFrame(meta_rows)
        meta_df.to_csv(OUT_DIR / "meta.csv", index=False)
        print(f"[OK] Successfully saved {len(meta_df)} real audio files and meta.csv to {OUT_DIR}")
        return meta_df
    except Exception as e:
        print(f"[WARN] Error extracting audio: {e}")
        return None

if __name__ == "__main__":
    fetch_and_save_real_audio_dataset()
