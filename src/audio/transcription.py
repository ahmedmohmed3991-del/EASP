"""
EASP Speech-to-Text (STT) Transcription Engine
-----------------------------------------------
- Powered by Faster-Whisper (int8 / CPU).
- Multilingual STT with clean Arabic & English speech recognition.
- Zero-hallucination configuration (no forced prompts).
- Passes transcribed text to downstream NLP / DLP security models.
"""
import os
import re
import numpy as np
import librosa
from typing import Tuple, List, Dict

class SpeechTranscriber:
    def __init__(self, model_size: str = "base"):
        self.model = None
        self.model_size = model_size
        self.device_type = "cpu"
        self.compute_type = "int8"
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(
                model_size,
                device=self.device_type,
                compute_type=self.compute_type,
                cpu_threads=min(8, os.cpu_count() or 4)
            )
        except Exception as e:
            try:
                from faster_whisper import WhisperModel
                self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
            except Exception:
                self.model = None

    def transcribe(self, audio_input, orig_sr: int = 16000) -> Tuple[str, str, List[dict]]:
        """Transcribes audio file path or numpy array and returns (text, language, segments)."""
        if self.model is None:
            return ("[Speech-to-Text engine unavailable]", "unknown", [])

        try:
            if isinstance(audio_input, str):
                if not os.path.exists(audio_input):
                    return ("[Audio file not found]", "unknown", [])
                audio_16k, sr = librosa.load(audio_input, sr=16000)
            else:
                audio_16k = np.asarray(audio_input, dtype=np.float32)
                if audio_16k.ndim > 1:
                    audio_16k = audio_16k.mean(axis=-1)
                if orig_sr != 16000:
                    audio_16k = librosa.resample(audio_16k, orig_sr=orig_sr, target_sr=16000)

            # 1. DC-Offset Removal & Peak Normalization
            audio_16k = audio_16k - np.mean(audio_16k)
            peak = np.max(np.abs(audio_16k)) + 1e-9
            if peak > 1e-4:
                audio_16k = audio_16k / peak

            # 2. Silence / Energy check
            rms = np.sqrt(np.mean(audio_16k**2))
            if rms < 0.005 or len(audio_16k) < 3200:
                return ("[No active speech detected in audio]", "none", [])

            # 3. Clean Transcription (No misleading initial prompts)
            segments, info = self.model.transcribe(
                audio_16k,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400),
                condition_on_previous_text=False,
                temperature=0.0,
                no_speech_threshold=0.6
            )

            seg_list = list(segments)
            full_text = " ".join(s.text.strip() for s in seg_list if s.text.strip()).strip()

            if not full_text:
                return ("[No speech detected]", "none", [])

            raw_lang = info.language if info else "unknown"
            
            # Detect Arabic / English code-switching
            has_ar = bool(re.search(r'[\u0600-\u06FF]', full_text))
            has_en = bool(re.search(r'[a-zA-Z]', full_text))
            if has_ar and has_en:
                lang_desc = "Bilingual (Arabic + English)"
            elif has_ar:
                lang_desc = "Arabic (ar)"
            elif has_en:
                lang_desc = "English (en)"
            else:
                lang_desc = f"{raw_lang.upper()} ({raw_lang})"

            seg_details = [
                {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
                for s in seg_list if s.text.strip()
            ]

            return (full_text, lang_desc, seg_details)

        except Exception as e:
            return (f"[Transcription note: {e}]", "unknown", [])
