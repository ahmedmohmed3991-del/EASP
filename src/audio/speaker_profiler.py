"""
Speaker Acoustic Frequency Profiler & Voiceprint Biometric Engine
-----------------------------------------------------------------
- Speech-gated fundamental frequency (F0 / pitch range) extraction via pYIN.
- Spectral centroid, spectral bandwidth, and energy analysis.
- Legitimate speaker enrollment and live call verification.
"""
import os
import numpy as np
import librosa
from typing import Dict, Union

class SpeakerFrequencyProfiler:
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate
        self.enrolled_profiles: Dict[str, dict] = {}

    def extract_profile(self, audio_input: Union[str, np.ndarray], orig_sr: int = None) -> dict:
        """Extracts pitch (F0), spectral features, and vocal register from audio."""
        if isinstance(audio_input, str):
            if not os.path.exists(audio_input):
                raise FileNotFoundError(f"Audio file not found: {audio_input}")
            y, sr = librosa.load(audio_input, sr=self.sr)
        else:
            y = np.asarray(audio_input, dtype=np.float32)
            if y.ndim > 1:
                y = y.mean(axis=-1)
            sr = orig_sr or self.sr
            if sr != self.sr:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.sr)

        # 1. DC-Offset Removal & Peak Normalization
        y = y - np.mean(y)
        peak = np.max(np.abs(y))
        y_norm = y / (peak + 1e-6) if peak > 1e-4 else y

        # 2. RMS Energy
        hop_length = 512
        rms = librosa.feature.rms(y=y_norm, hop_length=hop_length)[0]
        rms_thresh = max(0.008, 0.05 * np.max(rms)) if len(rms) > 0 else 0.008

        # 3. Fundamental Frequency (F0 / Pitch) via pYIN
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y_norm,
            fmin=librosa.note_to_hz('C2'),  # ~65.4 Hz
            fmax=librosa.note_to_hz('C7'),  # ~2093 Hz
            sr=self.sr,
            hop_length=hop_length
        )

        min_len = min(len(rms), len(f0), len(voiced_probs))
        rms = rms[:min_len]
        f0 = f0[:min_len]
        voiced_probs = voiced_probs[:min_len]

        # 4. Voice Activity Detection (VAD) Speech Mask
        speech_mask = (voiced_probs >= 0.25) & (~np.isnan(f0)) & (rms >= rms_thresh)
        f0_speech = f0[speech_mask]

        if len(f0_speech) >= 3:
            f0_min = float(np.percentile(f0_speech, 5))
            f0_max = float(np.percentile(f0_speech, 95))
            f0_mean = float(np.mean(f0_speech))
            f0_median = float(np.median(f0_speech))
            f0_std = float(np.std(f0_speech))
            pitch_stability = max(0.0, float(1.0 - (f0_std / (f0_mean + 1e-6))))
            speech_dur = float(len(f0_speech) * hop_length / self.sr)
        else:
            f0_min, f0_max, f0_mean, f0_median, f0_std, pitch_stability, speech_dur = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        # 5. Spectral Centroid & Bandwidth
        spec_cent = librosa.feature.spectral_centroid(y=y_norm, sr=self.sr, hop_length=hop_length)[0][:min_len]
        spec_bw = librosa.feature.spectral_bandwidth(y=y_norm, sr=self.sr, hop_length=hop_length)[0][:min_len]

        active_mask = (rms >= rms_thresh) if np.any(rms >= rms_thresh) else np.ones(min_len, dtype=bool)
        cent_mean = float(np.mean(spec_cent[active_mask])) if len(spec_cent[active_mask]) > 0 else 0.0
        bw_mean = float(np.mean(spec_bw[active_mask])) if len(spec_bw[active_mask]) > 0 else 0.0

        # 6. Vocal Register Classification
        if f0_mean == 0.0:
            voice_category = "Unvoiced / Ambient Audio"
        elif f0_mean < 85.0:
            voice_category = "Low Bass (Deep Male Register)"
        elif f0_mean < 155.0:
            voice_category = "Male Register (Low Pitch)"
        elif f0_mean < 185.0:
            voice_category = "Neutral / Contralto (Mid Pitch)"
        elif f0_mean < 250.0:
            voice_category = "Female Register (Medium-High Pitch)"
        else:
            voice_category = "High Register (High Pitch)"

        return {
            "f0_range_hz": (round(f0_min, 1), round(f0_max, 1)),
            "f0_mean_hz": round(f0_mean, 1),
            "f0_median_hz": round(f0_median, 1),
            "f0_std_hz": round(f0_std, 1),
            "pitch_stability_score": round(pitch_stability, 3),
            "spectral_centroid_hz": round(cent_mean, 1),
            "spectral_bandwidth_hz": round(bw_mean, 1),
            "speech_duration_sec": round(speech_dur, 2),
            "voice_category": voice_category
        }

    def enroll_speaker(self, speaker_id: str, audio_input: Union[str, np.ndarray]) -> dict:
        """Enrolls an authorized speaker profile into memory."""
        profile = self.extract_profile(audio_input)
        self.enrolled_profiles[speaker_id] = profile
        return profile

    def verify_speaker(self, speaker_id: str, test_audio_input: Union[str, np.ndarray], tolerance: float = 0.25) -> dict:
        """Verifies if test audio matches the enrolled speaker's biometric voiceprint."""
        if speaker_id not in self.enrolled_profiles:
            return {
                "target_speaker": speaker_id,
                "is_authentic_speaker": False,
                "match_confidence": 0.0,
                "verdict": "NOT_ENROLLED"
            }

        enrolled = self.enrolled_profiles[speaker_id]
        current = self.extract_profile(test_audio_input)

        if current["f0_mean_hz"] == 0.0:
            return {
                "target_speaker": speaker_id,
                "is_authentic_speaker": False,
                "match_confidence": 0.0,
                "verdict": "UNVOICED_SAMPLE"
            }

        f0_diff = abs(current["f0_mean_hz"] - enrolled["f0_mean_hz"]) / (enrolled["f0_mean_hz"] + 1e-6)
        cent_diff = abs(current["spectral_centroid_hz"] - enrolled["spectral_centroid_hz"]) / (enrolled["spectral_centroid_hz"] + 1e-6)
        bw_diff = abs(current["spectral_bandwidth_hz"] - enrolled["spectral_bandwidth_hz"]) / (enrolled["spectral_bandwidth_hz"] + 1e-6)

        distance = (0.50 * f0_diff) + (0.30 * cent_diff) + (0.20 * bw_diff)
        match_score = max(0.0, min(1.0, 1.0 - distance))
        is_verified = match_score >= (1.0 - tolerance)

        return {
            "target_speaker": speaker_id,
            "is_authentic_speaker": is_verified,
            "match_confidence": round(match_score * 100, 1),
            "enrolled_f0_mean": enrolled["f0_mean_hz"],
            "test_f0_mean": current["f0_mean_hz"],
            "enrolled_category": enrolled["voice_category"],
            "test_category": current["voice_category"],
            "verdict": "AUTHENTIC_SPEAKER" if is_verified else "ACOUSTIC_MISMATCH"
        }
