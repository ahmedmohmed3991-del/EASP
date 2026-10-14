"""
EASP AI Microservice - Phase 10 (T-P10-048 / T-P10-049)
Exposes production REST endpoints for:
- /dlp/scan: Sensitive data detection & AES-256 tokenization
- /audio/transcribe: Faster-Whisper speech-to-text
- /audio/analyze-deepfake: RawNet2 voice spoofing detection
- /nlp/classify: mBERT multi-label social engineering detection
- /audio/analyze: Consolidated audio pipeline (audio -> deepfake + transcript + social engineering)
- /risk/evaluate: Rule-based risk fusion calculation
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import base64

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dlp.engine import DLPEngine
from voice_deepfake.detector import RawNet2VoiceDetector
from voice_deepfake.speaker_profiler import SpeakerFrequencyProfiler
from audio.processor import AudioProcessor
from audio.transcriber import SpeechTranscriber
from social_engineering.detector import SocialEngineeringDetector
from risk_engine import XGBoostRiskEngine

SERVICE_NAME = "easp-ai-service"
PHASE = "phase-10-production"

app = FastAPI(
    title="EASP AI Security Microservice",
    description="Enterprise AI Security Platform - NLP, Audio, and Risk Evaluation Microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
dlp_engine = DLPEngine()
audio_processor = AudioProcessor(target_sr=16000)
voice_detector = RawNet2VoiceDetector()
speaker_profiler = SpeakerFrequencyProfiler()
transcriber = SpeechTranscriber(model_size="base")
social_detector = SocialEngineeringDetector()
xgb_risk_engine = XGBoostRiskEngine()



# ---------------------------------------------------------------------------
# Request / Response Pydantic Models
# ---------------------------------------------------------------------------
class ScanRequest(BaseModel):
    text: str
    user_id: Optional[str] = "anonymous"


class NLPClassifyRequest(BaseModel):
    text: str


class RiskEvaluateRequest(BaseModel):
    voice_score: float = Field(0.0, ge=0.0, le=1.0)
    social_score: float = Field(0.0, ge=0.0, le=1.0)
    dlp_score: float = Field(0.0, ge=0.0, le=1.0)


class MLRiskEvaluateRequest(BaseModel):
    deepfake_score: float = Field(0.0, ge=0.0, le=1.0)
    urgency_score: float = Field(0.0, ge=0.0, le=1.0)
    authority_score: float = Field(0.0, ge=0.0, le=1.0)
    credential_score: float = Field(0.0, ge=0.0, le=1.0)
    payment_score: float = Field(0.0, ge=0.0, le=1.0)
    dlp_entity_count: int = Field(0, ge=0)


class HealthResponse(BaseModel):
    status: str
    service: str
    phase: str
    timestamp: str
    components: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": SERVICE_NAME,
        "phase": PHASE,
        "status": "operational",
        "endpoints": [
            "/health",
            "/dlp/scan",
            "/audio/transcribe",
            "/audio/analyze-deepfake",
            "/nlp/classify",
            "/audio/analyze",
            "/risk/evaluate"
        ]
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        phase=PHASE,
        timestamp=datetime.now(timezone.utc).isoformat(),
        components={
            "dlp": {"status": "ready", "recognizers_loaded": True},
            "voice_deepfake": {
                "status": "ready",
                "model_loaded": voice_detector.model_loaded,
                "weights_path": voice_detector.weights_path
            },
            "whisper": {
                "status": "ready",
                "model_loaded": transcriber.model_loaded,
                "model_size": transcriber.model_size
            },
            "social_engineering": {
                "status": "ready",
                "categories": ["urgency", "authority_impersonation", "credential_request", "payment_request"]
            }
        }
    )


@app.post("/dlp/scan")
def dlp_scan(request: ScanRequest):
    """Scans text for credentials and PII, returns redacted text and token mappings."""
    try:
        result = dlp_engine.scan_and_redact(request.text)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DLP scan error: {str(e)}")


@app.post("/nlp/classify")
def nlp_classify(request: NLPClassifyRequest):
    """Classifies text for social engineering, coercion, and phishing indicators."""
    try:
        result = social_detector.analyze_text(request.text)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP classification error: {str(e)}")


@app.post("/audio/transcribe")
async def audio_transcribe(file: UploadFile = File(...)):
    """Transcribes uploaded audio file (WAV/PCM) to text."""
    try:
        contents = await file.read()
        audio_data = audio_processor.load_wav_bytes(contents)
        trimmed = audio_processor.trim_silence(audio_data)
        result = transcriber.transcribe(trimmed)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")


@app.post("/audio/analyze-deepfake")
async def audio_analyze_deepfake(file: UploadFile = File(...)):
    """Analyzes uploaded audio file for voice deepfake spoof probability."""
    try:
        contents = await file.read()
        audio_data = audio_processor.load_wav_bytes(contents)
        result = voice_detector.analyze_audio(audio_data, sample_rate=16000)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deepfake analysis error: {str(e)}")


@app.get("/audio/speaker-profiles")
def get_speaker_profiles():
    """Returns list of enrolled executive acoustic baseline frequency profiles."""
    return {
        "status": "success",
        "data": speaker_profiler.list_profiles()
    }


@app.post("/audio/enroll-speaker")
async def enroll_speaker_profile(
    profile_id: str = Form(...),
    name: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...)
):
    """Enrolls a new VIP speaker acoustic baseline from an audio recording."""
    try:
        contents = await file.read()
        audio_data = audio_processor.load_wav_bytes(contents)
        trimmed = audio_processor.trim_silence(audio_data)
        res = speaker_profiler.enroll_profile(profile_id, name, title, trimmed, sample_rate=16000)
        return {"status": "success" if res.get("success") else "error", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrollment error: {str(e)}")


@app.post("/audio/sync-voices")
def sync_voices():
    """Scans the voices/ folder and synchronizes all audio recordings as enrolled speaker profiles."""
    try:
        enrolled = speaker_profiler.sync_voices_folder()
        return {
            "status": "success",
            "enrolled_count": len(enrolled),
            "profiles": speaker_profiler.list_profiles()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync voices error: {str(e)}")


@app.post("/audio/identify-speaker")
async def identify_speaker_endpoint(file: UploadFile = File(...)):
    """Performs 1-to-N biometric speaker identification against enrolled voice database."""
    try:
        contents = await file.read()
        audio_data = audio_processor.load_wav_bytes(contents)
        trimmed = audio_processor.trim_silence(audio_data)
        res = speaker_profiler.identify_speaker(trimmed, sample_rate=16000)
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification error: {str(e)}")


@app.post("/audio/analyze")
async def audio_analyze_pipeline(
    file: UploadFile = File(...),
    speaker_profile_id: Optional[str] = Form(None)
):
    """
    Consolidated Audio Security Pipeline with Dual-Perspective Biometrics:
    1. Loads and preprocesses audio waveform to 16 kHz mono.
    2. Model 1 (RawNet2): Voice deepfake spoof probability & vocoder artifacts.
    3. Model 2 (SpeakerFrequencyProfiler): Acoustic frequency bounds verification (F0 pitch, spectral envelope).
    4. Speech transcription (Faster-Whisper).
    5. Social engineering detection (mBERT).
    6. DLP entity scanning & tokenization.
    """
    try:
        contents = await file.read()
        audio_data = audio_processor.load_wav_bytes(contents)
        trimmed = audio_processor.trim_silence(audio_data)

        # 1. General Voice deepfake analysis (Tri-Engine SOTA)
        voice_result = voice_detector.analyze_audio(audio_data, sample_rate=16000)

        # 2. Speaker Acoustic Frequency Profiling (Doctor's Frequency Baseline Model)
        frequency_profile_result = speaker_profiler.verify_against_profile(
            audio_data,
            profile_id=speaker_profile_id,
            sample_rate=16000,
            rawnet2_spoof_score=voice_result.get("spoof_score")
        )

        # 3. Transcription
        transcribe_result = transcriber.transcribe(trimmed)
        transcript_text = transcribe_result.get("transcript", "")

        # 4. Social engineering analysis on transcript
        social_result = social_detector.analyze_text(transcript_text)

        # 5. DLP scan on transcript
        dlp_result = dlp_engine.scan_and_redact(transcript_text)

        return {
            "status": "success",
            "data": {
                "voice_deepfake": voice_result,
                "speaker_frequency_profile": frequency_profile_result,
                "transcription": transcribe_result,
                "social_engineering": social_result,
                "dlp": dlp_result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio pipeline error: {str(e)}")


@app.post("/risk/evaluate")
def risk_evaluate(request: RiskEvaluateRequest):
    """
    Computes Phase 1 deterministic rule-based fused risk score:
    Risk = 0.40 * Voice + 0.35 * Social + 0.25 * DLP
    """
    voice = request.voice_score
    social = request.social_score
    dlp = request.dlp_score

    fused = round(0.40 * voice + 0.35 * social + 0.25 * dlp, 4)

    level = "LOW"
    if fused >= 0.70:
        level = "HIGH"
    elif fused >= 0.40:
        level = "MEDIUM"

    return {
        "status": "success",
        "data": {
            "fused_risk": fused,
            "level": level,
            "weights": {
                "voice_deepfake": 0.40,
                "social_engineering": 0.35,
                "dlp_sensitivity": 0.25
            },
            "contributing_factors": {
                "voice_score": voice,
                "social_score": social,
                "dlp_score": dlp
            }
        }
    }


@app.post("/risk/evaluate-ml")
def risk_evaluate_ml(request: MLRiskEvaluateRequest):
    """
    Computes Phase 2 Machine Learning risk decision using XGBoost multi-class classifier
    and generates local SHAP feature attribution vectors for complete explainability.
    """
    try:
        result = xgb_risk_engine.predict_and_explain(request.dict())
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XGBoost risk inference failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
