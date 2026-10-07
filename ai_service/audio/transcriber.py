"""
Faster-Whisper Speech-to-Text Transcriber - Phase 7 (T-P07-037 / T-P07-038)
Wraps Faster-Whisper for low-latency speech transcription with CPU fallback.
Produces transcript text feeding into the downstream mBERT classifier.
"""

import os
from typing import Dict, Any, Optional
import numpy as np
from .processor import AudioProcessor


class SpeechTranscriber:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.processor = AudioProcessor(target_sr=16000)
        self.model = None
        self.model_loaded = False
        self.init_error = None

        self._init_whisper()

    def _init_whisper(self):
        try:
            from faster_whisper import WhisperModel
            device = "cpu"
            compute_type = "int8"
            self.model = WhisperModel(self.model_size, device=device, compute_type=compute_type, local_files_only=True, download_root=os.getenv("WHISPER_DOWNLOAD_ROOT"))
            self.model_loaded = True
        except Exception as e:
            self.model_loaded = False
            self.init_error = f"Faster-Whisper not initialized: {str(e)}"

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes normalized 16kHz float32 audio array into text.
        Supports multi-lingual auto-detection (Arabic, English, etc.).
        """
        if audio_data is None or len(audio_data) == 0:
            return {
                "success": False,
                "error": "Empty audio data provided",
                "transcript": "",
                "segments": []
            }

        if self.model_loaded and self.model is not None:
            try:
                # If language is None, Whisper automatically identifies the spoken language
                transcribe_kwargs = {"beam_size": 2}
                if language:
                    transcribe_kwargs["language"] = language

                segments, info = self.model.transcribe(audio_data, **transcribe_kwargs)
                transcript_text = " ".join([seg.text.strip() for seg in segments])
                return {
                    "success": True,
                    "model_loaded": True,
                    "transcript": transcript_text,
                    "language": getattr(info, "language", "en"),
                    "language_probability": round(getattr(info, "language_probability", 1.0), 4),
                    "duration_seconds": round(getattr(info, "duration", len(audio_data) / 16000.0), 2),
                    "engine": "Faster-Whisper-Int8"
                }
            except Exception as e:
                return {
                    "success": False,
                    "model_loaded": True,
                    "error": f"Transcription error: {str(e)}",
                    "transcript": ""
                }

        # Real status report when Whisper model is offline
        return {
            "success": False,
            "model_loaded": False,
            "notice": "Faster-Whisper model unpopulated or offline; please run using Miniconda Python environment",
            "init_error": self.init_error,
            "transcript": "",
            "language": "none",
            "duration_seconds": round(len(audio_data) / 16000.0, 2),
            "engine": "Unavailable"
        }
