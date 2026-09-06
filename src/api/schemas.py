"""
EASP FastAPI Pydantic Data Contracts & Schemas
Defines request and response interfaces for AI Services & CS 1 (Express Backend) integration.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# ----------------- Base & Nested Schemas -----------------

class DLPFinding(BaseModel):
    entity_type: str = Field(..., description="Type of detected sensitive entity (e.g. EMAIL_ADDRESS, API_KEY, CREDIT_CARD)")
    original: str = Field(..., description="Original extracted sensitive text")
    token: str = Field(..., description="Reversible token inserted into redacted prompt")
    encrypted_vault_id: str = Field(..., description="AES-256 encrypted token representation in vault")

class ThreatPrediction(BaseModel):
    is_threat: bool = Field(..., description="Whether the prompt is classified as a security threat / prompt injection")
    label: str = Field(..., description="Human readable prediction label (e.g. Malicious Prompt Injection vs Benign)")
    probability: float = Field(..., description="Threat probability between 0.0 and 1.0")
    confidence: float = Field(..., description="Confidence percentage [0-100%]")

class RiskDecision(BaseModel):
    composite_risk_score: float = Field(..., description="Overall calculated risk score from 0.0 to 100.0")
    action: str = Field(..., description="Policy action: ALLOW, FLAG, or BLOCK")
    reasons: List[str] = Field(default_factory=list, description="List of rule triggers and security violation explanations")
    breakdown: Dict[str, float] = Field(default_factory=dict, description="Component score contributions (0-100 scale)")

class ExplainabilityInsight(BaseModel):
    feature_attributions: Dict[str, float] = Field(default_factory=dict, description="Top tokens/features contributing positively or negatively to the risk score")
    summary: str = Field(..., description="Summary of explainability findings")

class TelemetryInfo(BaseModel):
    latency_ms: float = Field(..., description="Processing time in milliseconds")
    model_version: str = Field(default="1.0.0", description="Version of the AI model pipeline")
    timestamp: str = Field(..., description="ISO timestamp of evaluation")

# ----------------- Request Schemas -----------------

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Input user prompt or text payload to analyze")
    user_id: Optional[str] = Field(default="anonymous", description="Identifier of the querying user")
    session_id: Optional[str] = Field(default=None, description="Optional session or chat thread ID")
    enable_dlp: bool = Field(default=True, description="Whether to run reversible DLP redaction")
    enable_explainability: bool = Field(default=True, description="Whether to compute explainability attributions")

class DLPDetokenizeRequest(BaseModel):
    masked_text: str = Field(..., description="Redacted text containing <REDACTED_TYPE_HASH> tokens")
    token_map: Optional[Dict[str, str]] = Field(default=None, description="Optional client-provided mapping of tokens to ciphertext")

# ----------------- Response Schemas -----------------

class TextAnalysisResponse(BaseModel):
    status: str = "success"
    original_text: str
    sanitized_text: str
    dlp_findings: List[DLPFinding] = Field(default_factory=list)
    token_map: Dict[str, str] = Field(default_factory=dict)
    threat_prediction: ThreatPrediction
    risk_evaluation: RiskDecision
    explainability: Optional[ExplainabilityInsight] = None
    telemetry: TelemetryInfo

class AudioSpectralFeatures(BaseModel):
    spectral_centroid_hz: float
    spectral_bandwidth_hz: float
    f0_mean_hz: float
    pitch_stability_score: float
    speech_duration_sec: float
    voice_category: str

class AudioTranscriptionResult(BaseModel):
    raw_text: str
    detected_language: str
    segments_count: int
    duration_seconds: float

class VoiceAnalysisResponse(BaseModel):
    status: str = "success"
    deepfake_score: float = Field(..., description="Voice deepfake probability [0.0 - 1.0]")
    is_deepfake: bool = Field(..., description="True if voice deepfake probability exceeds security threshold")
    spectral_features: AudioSpectralFeatures
    transcription: AudioTranscriptionResult
    sanitized_text: str
    dlp_findings: List[DLPFinding] = Field(default_factory=list)
    token_map: Dict[str, str] = Field(default_factory=dict)
    threat_prediction: ThreatPrediction
    risk_evaluation: RiskDecision
    explainability: Optional[ExplainabilityInsight] = None
    telemetry: TelemetryInfo

class DLPDetokenizeResponse(BaseModel):
    status: str = "success"
    restored_text: str
    restored_count: int

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    service_name: str = "EASP AI Integration & Security Microservice"
    owner: str = "AI 4 (kareem)"
    models_loaded: Dict[str, bool]
    device: str
