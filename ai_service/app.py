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
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import base64

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from boundary import InternalBoundary, read_upload
from pydantic import BaseModel, Field

import importlib
import logging

SERVICE_NAME = "easp-ai-service"
PHASE = "phase-10-production"

app = FastAPI(
    title="EASP AI Security Microservice",
    description="Enterprise AI Security Platform - NLP, Audio, and Risk Evaluation Microservice",
    version="1.0.0"
)

app.add_middleware(InternalBoundary)

# Each unavailable engine is reported explicitly; unrelated endpoints can still operate.
def initialize(module, name, *args, **kwargs):
    try:
        return getattr(importlib.import_module(module), name)(*args, **kwargs)
    except Exception as error:
        logging.error("Engine %s unavailable (%s)", name, type(error).__name__)
        return None


def require_engine(engine, neural=False):
    if engine is None or (neural and not engine.model_loaded):
        raise HTTPException(503, "Required AI engine is unavailable")
    return engine


def require_success(result):
    if not isinstance(result, dict) or result.get("success") is not True:
        raise HTTPException(503, "AI inference failed")
    return result


dlp_engine = initialize("dlp.engine", "DLPEngine")
audio_processor = initialize("audio.processor", "AudioProcessor", target_sr=16000)
voice_detector = initialize("voice_deepfake.detector", "RawNet2VoiceDetector")
speaker_profiler = initialize("voice_deepfake.speaker_profiler", "SpeakerFrequencyProfiler")
transcriber = initialize("audio.transcriber", "SpeechTranscriber", model_size=os.getenv("WHISPER_MODEL", "base"))
social_detector = initialize("social_engineering.detector", "SocialEngineeringDetector")
xgb_risk_engine = initialize("risk_engine", "XGBoostRiskEngine")


# ---------------------------------------------------------------------------
# Request / Response Pydantic Models
# ---------------------------------------------------------------------------
class ScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    user_id: Optional[str] = "anonymous"


class NLPClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)


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
    components = {
        "dlp": {"status": "ready" if dlp_engine else "unavailable"},
        "voice_deepfake": {"status": "ready" if getattr(voice_detector, "model_loaded", False) else "unavailable",
                           "model_loaded": getattr(voice_detector, "model_loaded", False)},
        "whisper": {"status": "ready" if getattr(transcriber, "model_loaded", False) else "unavailable",
                    "model_loaded": getattr(transcriber, "model_loaded", False)},
        "social_engineering": {"status": "ready" if social_detector else "unavailable", "engine": "regex-heuristic"},
        "risk_ml": {"status": "ready" if xgb_risk_engine else "unavailable", "validation": "unverified"}
    }
    return HealthResponse(status="ok" if all(v["status"] == "ready" for v in components.values()) else "degraded",
                          service=SERVICE_NAME, phase=PHASE, timestamp=datetime.now(timezone.utc).isoformat(), components=components)


@app.post("/dlp/scan")
def dlp_scan(request: ScanRequest):
    """Scans text for credentials and PII, returns redacted text and token mappings."""
    try:
        result = require_engine(dlp_engine).scan_and_redact(request.text)
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="DLP scan error")


@app.post("/nlp/classify")
def nlp_classify(request: NLPClassifyRequest):
    """Classifies text for social engineering, coercion, and phishing indicators."""
    try:
        result = require_engine(social_detector).analyze_text(request.text)
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="NLP classification error")


@app.post("/audio/transcribe")
async def audio_transcribe(file: UploadFile = File(...)):
    """Transcribes uploaded audio file (WAV/PCM) to text."""
    try:
        contents = await read_upload(file)
        audio_data = require_engine(audio_processor).load_wav_bytes(contents)
        trimmed = audio_processor.trim_silence(audio_data)
        result = require_success(require_engine(transcriber, neural=True).transcribe(trimmed))
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Transcription error")


@app.post("/audio/analyze-deepfake")
async def audio_analyze_deepfake(file: UploadFile = File(...)):
    """Analyzes uploaded audio file for voice deepfake spoof probability."""
    try:
        contents = await read_upload(file)
        audio_data = require_engine(audio_processor).load_wav_bytes(contents)
        result = require_success(require_engine(voice_detector, neural=True).analyze_audio(audio_data, sample_rate=16000))
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Deepfake analysis error")


@app.get("/audio/speaker-profiles")
def get_speaker_profiles():
    """Returns list of enrolled executive acoustic baseline frequency profiles."""
    return {
        "status": "success",
        "data": require_engine(speaker_profiler).list_profiles()
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
        contents = await read_upload(file)
        audio_data = require_engine(audio_processor).load_wav_bytes(contents)
        trimmed = audio_processor.trim_silence(audio_data)
        res = speaker_profiler.enroll_profile(profile_id, name, title, trimmed, sample_rate=16000)
        return {"status": "success" if res.get("success") else "error", "data": res}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Enrollment error")


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
        contents = await read_upload(file)
        audio_data = require_engine(audio_processor).load_wav_bytes(contents)
        trimmed = audio_processor.trim_silence(audio_data)

        # 1. General Voice deepfake analysis (RawNet2)
        voice_result = require_success(require_engine(voice_detector, neural=True).analyze_audio(trimmed, sample_rate=16000))

        # 2. Speaker Acoustic Frequency Profiling (Doctor's Frequency Baseline Model)
        frequency_profile_result = require_engine(speaker_profiler).verify_against_profile(
            trimmed,
            profile_id=speaker_profile_id,
            sample_rate=16000,
            rawnet2_spoof_score=voice_result.get("spoof_score")
        )

        # 3. Transcription
        transcribe_result = require_success(require_engine(transcriber, neural=True).transcribe(trimmed))
        transcript_text = transcribe_result.get("transcript", "")

        # 4. Social engineering analysis on transcript
        social_result = require_engine(social_detector).analyze_text(transcript_text)

        # 5. DLP scan on transcript
        dlp_result = require_engine(dlp_engine).scan_and_redact(transcript_text)

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Audio pipeline error")


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
        result = require_engine(xgb_risk_engine).predict_and_explain(request.dict())
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="XGBoost risk inference failed")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host=os.getenv("HOST", "127.0.0.1"), port=port, reload=False)
