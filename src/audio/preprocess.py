"""
Preprocessing Pipeline for Voice Deepfake Audio.
Includes:
- Sample rate standardization (16 kHz)
- Clip length standardization (padding / truncation)
- Log-Mel Spectrogram & MFCC feature extraction
- Speaker-independent Train/Val/Test splitting
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
from sklearn.model_selection import GroupShuffleSplit

class AudioPreprocessor:
    """Standard audio processor for deepfake detection models."""
    def __init__(
        self,
        target_sr: int = 16000,
        duration: float = 4.0, # 4 seconds standardized
        n_mels: int = 128,
        n_mfcc: int = 40,
        n_fft: int = 1024,
        hop_length: int = 512
    ):
        self.target_sr = target_sr
        self.duration = duration
        self.target_length = int(target_sr * duration)
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.n_fft = n_fft
        self.hop_length = hop_length

    def load_and_standardize(self, audio_input) -> np.ndarray:
        """Loads audio (from path or numpy array), resamples, peak-normalizes, and tiles/crops to fixed duration."""
        import librosa
        if isinstance(audio_input, str):
            try:
                waveform, sr = librosa.load(audio_input, sr=self.target_sr, mono=True)
            except Exception:
                import soundfile as sf
                data, sr = sf.read(audio_input)
                if len(data.shape) > 1:
                    data = np.mean(data, axis=1)
                if sr != self.target_sr:
                    waveform = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=self.target_sr)
                else:
                    waveform = data.astype(np.float32)
        else:
            waveform = np.asarray(audio_input, dtype=np.float32)
            if len(waveform.shape) > 1:
                waveform = np.mean(waveform, axis=1)

        # 1. Peak Normalization
        peak = np.max(np.abs(waveform)) + 1e-9
        if peak > 1e-4:
            waveform = waveform / peak * 0.90

        # 2. Trim Silence
        try:
            trimmed, _ = librosa.effects.trim(waveform, top_db=25)
            if len(trimmed) >= int(self.target_sr * 0.5):
                waveform = trimmed
        except Exception:
            pass

        # 3. Robust Tiling (No dead zero-padding discontinuities)
        if len(waveform) < self.target_length:
            reps = int(np.ceil(self.target_length / max(1, len(waveform))))
            waveform = np.tile(waveform, reps)[:self.target_length]
        else:
            waveform = waveform[:self.target_length]
            
        return waveform.astype(np.float32)

    def extract_mel_spectrogram(self, waveform: np.ndarray) -> np.ndarray:
        """Computes Log-Mel Spectrogram (dB). Output shape: (n_mels, time_steps)."""
        import librosa
        mel_spec = librosa.feature.melspectrogram(
            y=waveform,
            sr=self.target_sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
            fmin=20,
            fmax=self.target_sr // 2
        )
        log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
        # Normalize to [-1, 1] range for neural networks
        log_mel_spec = (log_mel_spec - log_mel_spec.min()) / (log_mel_spec.max() - log_mel_spec.min() + 1e-8)
        log_mel_spec = log_mel_spec * 2.0 - 1.0
        return log_mel_spec.astype(np.float32)

    def extract_mfcc(self, waveform: np.ndarray) -> np.ndarray:
        """Computes MFCC features. Output shape: (n_mfcc, time_steps)."""
        import librosa
        mfccs = librosa.feature.mfcc(
            y=waveform,
            sr=self.target_sr,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        # Standardize MFCCs
        mfccs = (mfccs - np.mean(mfccs)) / (np.std(mfccs) + 1e-8)
        return mfccs.astype(np.float32)

def create_speaker_independent_splits(
    meta_df: pd.DataFrame,
    speaker_col: str = "speaker_id",
    train_size: float = 0.70,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42
) -> Dict[str, pd.DataFrame]:
    """
    Performs speaker-independent splitting (no overlapping speakers across train, val, test)
    to prevent acoustic identity leakage.
    """
    assert speaker_col in meta_df.columns, f"Column '{speaker_col}' missing from metadata."
    
    unique_speakers = meta_df[speaker_col].unique()
    np.random.seed(random_state)
    shuffled_speakers = np.random.permutation(unique_speakers)
    
    n_total = len(shuffled_speakers)
    n_train = int(n_total * train_size)
    n_val = int(n_total * val_size)
    
    train_speakers = set(shuffled_speakers[:n_train])
    val_speakers = set(shuffled_speakers[n_train:n_train + n_val])
    test_speakers = set(shuffled_speakers[n_train + n_val:])
    
    train_df = meta_df[meta_df[speaker_col].isin(train_speakers)].copy().reset_index(drop=True)
    val_df = meta_df[meta_df[speaker_col].isin(val_speakers)].copy().reset_index(drop=True)
    test_df = meta_df[meta_df[speaker_col].isin(test_speakers)].copy().reset_index(drop=True)
    
    return {"train": train_df, "val": val_df, "test": test_df}
