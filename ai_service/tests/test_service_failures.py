import asyncio
import importlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import HTTPException, UploadFile


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # No downloads or heavyweight model construction in boundary tests.
        real_import = importlib.import_module
        engines = {
            'audio.processor': 'AudioProcessor', 'voice_deepfake.detector': 'RawNet2VoiceDetector',
            'voice_deepfake.speaker_profiler': 'SpeakerFrequencyProfiler', 'audio.transcriber': 'SpeechTranscriber',
            'risk_engine': 'XGBoostRiskEngine'
        }
        def load(name, *args, **kwargs):
            if name in engines:
                return SimpleNamespace(**{engines[name]: lambda **kw: None})
            return real_import(name, *args, **kwargs)
        with patch('importlib.import_module', side_effect=load):
            cls.service = real_import('app')

    async def test_model_failure_is_unavailable_not_success(self):
        s = self.service
        processor = SimpleNamespace(load_wav_bytes=lambda _: [0.1], trim_silence=lambda x: x)
        with patch.object(s, 'audio_processor', processor):
            for voice in [None, SimpleNamespace(model_loaded=False),
                          SimpleNamespace(model_loaded=True, analyze_audio=lambda *a, **kw: {'success': False})]:
                with patch.object(s, 'voice_detector', voice):
                    with self.assertRaises(HTTPException) as error:
                        await s.audio_analyze_pipeline(UploadFile(io.BytesIO(b'audio')), None)
                    self.assertEqual(error.exception.status_code, 503)

    async def test_transcription_failure_is_not_an_empty_successful_scan(self):
        s = self.service
        with patch.object(s, 'audio_processor', SimpleNamespace(load_wav_bytes=lambda _: [0.1], trim_silence=lambda x: x)), \
             patch.object(s, 'transcriber', SimpleNamespace(model_loaded=True, transcribe=lambda _: {'success': False})):
            with self.assertRaises(HTTPException) as error:
                await s.audio_transcribe(UploadFile(io.BytesIO(b'audio')))
            self.assertEqual(error.exception.status_code, 503)

    def test_health_reports_unavailable_models(self):
        self.assertEqual(self.service.health().status, 'degraded')
        self.assertEqual(self.service.health().components['whisper']['status'], 'unavailable')

    def test_text_request_limit(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError): self.service.ScanRequest(text='x' * 20001)


if __name__ == '__main__': unittest.main()
