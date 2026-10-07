"""
EASP Audio Preprocessor - Phase 7 (T-P07-036)
Standardizes input audio to 16,000 Hz mono PCM, applies silence trimming,
and normalizes waveforms for RawNet2 and Whisper pipelines.
"""

import io
import wave
import numpy as np


class AudioProcessor:
    def __init__(self, target_sr: int = 16000):
        self.target_sr = target_sr

    def load_wav_bytes(self, audio_bytes: bytes) -> np.ndarray:
        """Loads an audio byte stream (MP3, WAV, FLAC, M4A, OGG) into a normalized 16kHz float32 numpy array."""
        # 1. Try PyAV / faster_whisper decode_audio (handles MP3, WAV, FLAC, M4A, etc.)
        try:
            from faster_whisper.audio import decode_audio
            data = decode_audio(io.BytesIO(audio_bytes), sampling_rate=self.target_sr)
            if data is not None and len(data) > 0:
                return data.astype(np.float32)
        except Exception:
            pass

        # 2. Try scipy.io.wavfile (handles various WAV bit-depths: 16, 24, 32-bit, float)
        try:
            import scipy.io.wavfile as wavfile
            sr, raw = wavfile.read(io.BytesIO(audio_bytes))
            if raw.dtype == np.int16:
                data = raw.astype(np.float32) / 32768.0
            elif raw.dtype == np.int32:
                data = raw.astype(np.float32) / 2147483648.0
            elif raw.dtype == np.uint8:
                data = (raw.astype(np.float32) - 128.0) / 128.0
            else:
                data = raw.astype(np.float32)

            if data.ndim > 1:
                data = data.mean(axis=1)

            if sr != self.target_sr and len(data) > 0:
                import math
                import scipy.signal as signal
                g = math.gcd(sr, self.target_sr)
                up = self.target_sr // g
                down = sr // g
                data = signal.resample_poly(data, up, down).astype(np.float32)

            return data
        except Exception:
            pass

        # 3. Fallback to standard wave module
        try:
            with io.BytesIO(audio_bytes) as bio:
                with wave.open(bio, 'rb') as wf:
                    n_channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    framerate = wf.getframerate()
                    n_frames = wf.getnframes()
                    raw_data = wf.readframes(n_frames)

            if sampwidth == 1:
                data = (np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) - 128) / 128.0
            elif sampwidth == 2:
                data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif sampwidth == 4:
                data = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                data = np.frombuffer(raw_data, dtype=np.float32)

            if n_channels > 1:
                data = data.reshape(-1, n_channels).mean(axis=1)

            if framerate != self.target_sr and len(data) > 0:
                duration = len(data) / framerate
                target_len = int(duration * self.target_sr)
                indices = np.linspace(0, len(data) - 1, target_len)
                data = np.interp(indices, np.arange(len(data)), data).astype(np.float32)

            return data
        except Exception:
            try:
                return np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            except Exception:
                return np.zeros(self.target_sr * 2, dtype=np.float32)

    def trim_silence(self, audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Removes leading and trailing silence below amplitude threshold."""
        if len(audio) == 0:
            return audio
        non_silent = np.where(np.abs(audio) > threshold)[0]
        if len(non_silent) == 0:
            return audio
        return audio[non_silent[0]:non_silent[-1] + 1]

    def create_wav_bytes(self, audio: np.ndarray) -> bytes:
        """Encodes float32 audio back into 16-bit PCM WAV bytes."""
        scaled = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        bio = io.BytesIO()
        with wave.open(bio, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.target_sr)
            wf.writeframes(scaled.tobytes())
        return bio.getvalue()
