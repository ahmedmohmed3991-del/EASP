"""
EASP FastAPI API Routers (AI 4 Component)
Defines REST API endpoints for text/voice security analysis, DLP restoration, and health checks.
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status, Depends
from typing import Optional
from src.api.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    VoiceAnalysisResponse,
    DLPDetokenizeRequest,
    DLPDetokenizeResponse,
    HealthResponse
)
from src.api.pipeline import EASPUnifiedAIPipeline

router = APIRouter(prefix="/api/v1", tags=["AI Security Services"])

def get_pipeline() -> EASPUnifiedAIPipeline:
    return EASPUnifiedAIPipeline.get_instance()

@router.get("/health", response_model=HealthResponse, summary="AI Subsystem Health & Status")
async def health_check(pipeline: EASPUnifiedAIPipeline = Depends(get_pipeline)):
    """
    Returns current health status, active execution device, and loaded AI model states.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service_name="EASP AI Integration & Security Microservice",
        owner="AI 4 (kareem)",
        models_loaded={
            "dlp_engine": pipeline.dlp_engine is not None,
            "text_threat_classifier": pipeline.text_classifier is not None,
            "audio_deepfake_cnn": pipeline.audio_deepfake_model is not None,
            "speech_transcriber": pipeline.transcriber is not None,
            "policy_risk_engine": pipeline.policy_engine is not None,
            "shap_explainer": pipeline.explainer is not None,
        },
        device=pipeline.device
    )

@router.post(
    "/ai/analyze-text",
    response_model=TextAnalysisResponse,
    summary="Analyze Text Prompt for DLP and Injection Threats",
    status_code=status.HTTP_200_OK
)
async def analyze_text(
    payload: TextAnalysisRequest,
    pipeline: EASPUnifiedAIPipeline = Depends(get_pipeline)
):
    """
    Evaluates input text against:
    1. Reversible DLP scanning (PII, Credentials, API keys).
    2. Prompt Injection & Social Engineering classification.
    3. Multi-factor Risk Scoring & Policy enforcement (ALLOW, FLAG, BLOCK).
    4. SHAP feature attribution & explainability telemetry.
    """
    try:
        response = pipeline.analyze_text(
            text=payload.text,
            enable_dlp=payload.enable_dlp,
            enable_explainability=payload.enable_explainability
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing AI text analysis pipeline: {str(e)}"
        )

@router.post(
    "/ai/analyze-voice",
    response_model=VoiceAnalysisResponse,
    summary="Analyze Audio File for Voice Deepfakes, STT, and Downstream Threats",
    status_code=status.HTTP_200_OK
)
async def analyze_voice(
    file: UploadFile = File(..., description="Audio file in WAV, MP3, FLAC, or OGG format"),
    enable_dlp: bool = Form(True, description="Enable Reversible DLP on transcribed speech"),
    enable_explainability: bool = Form(True, description="Enable explainability attributions"),
    pipeline: EASPUnifiedAIPipeline = Depends(get_pipeline)
):
    """
    Full Multi-Modal Voice Analysis:
    1. Runs Deepfake Detection (RawNet2 / CNN + Spectral Profiling).
    2. Runs Faster-Whisper Speech-to-Text transcription.
    3. Applies Reversible DLP Redaction on transcribed text.
    4. Evaluates Prompt Injection & Malicious intent on transcribed content.
    5. Calculates Fused Multi-Modal Risk Score and produces Policy Decision.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No audio file uploaded.")
    
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
        
        response = pipeline.analyze_voice(
            audio_bytes=audio_bytes,
            filename=file.filename,
            enable_dlp=enable_dlp,
            enable_explainability=enable_explainability
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing AI voice analysis pipeline: {str(e)}"
        )

@router.post(
    "/ai/dlp-restore",
    response_model=DLPDetokenizeResponse,
    summary="Restore and Decrypt DLP Redacted Tokens",
    status_code=status.HTTP_200_OK
)
async def restore_dlp(
    payload: DLPDetokenizeRequest,
    pipeline: EASPUnifiedAIPipeline = Depends(get_pipeline)
):
    """
    Restores redacted tokens (<REDACTED_TYPE_HASH>) into their original values
    via AES-256 in-memory cryptographic vault.
    """
    try:
        response = pipeline.restore_dlp(
            masked_text=payload.masked_text,
            custom_token_map=payload.token_map
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restoring DLP masked text: {str(e)}"
        )
