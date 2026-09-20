using System.Text.Json.Serialization;

namespace EASP.Api.DTOs;

// ==========================================
// Phase 10: AI Security Engine DTO Contracts (T-P10-050)
// ==========================================

public class AiAnalyzeTextRequest
{
    [JsonPropertyName("text")]
    public string Text { get; set; } = string.Empty;

    [JsonPropertyName("user_id")]
    public string? UserId { get; set; } = "anonymous";

    [JsonPropertyName("session_id")]
    public string? SessionId { get; set; }

    [JsonPropertyName("enable_dlp")]
    public bool EnableDlp { get; set; } = true;

    [JsonPropertyName("enable_explainability")]
    public bool EnableExplainability { get; set; } = true;
}

public class AiDlpFindingDto
{
    [JsonPropertyName("entity_type")]
    public string EntityType { get; set; } = string.Empty;

    [JsonPropertyName("original")]
    public string Original { get; set; } = string.Empty;

    [JsonPropertyName("token")]
    public string Token { get; set; } = string.Empty;

    [JsonPropertyName("encrypted_vault_id")]
    public string EncryptedVaultId { get; set; } = string.Empty;
}

public class ThreatPredictionDto
{
    [JsonPropertyName("is_threat")]
    public bool IsThreat { get; set; }

    [JsonPropertyName("label")]
    public string Label { get; set; } = string.Empty;

    [JsonPropertyName("probability")]
    public double Probability { get; set; }

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }
}

public class RiskDecisionDto
{
    [JsonPropertyName("composite_risk_score")]
    public double CompositeRiskScore { get; set; }

    [JsonPropertyName("action")]
    public string Action { get; set; } = "ALLOW";

    [JsonPropertyName("reasons")]
    public List<string> Reasons { get; set; } = new();

    [JsonPropertyName("breakdown")]
    public Dictionary<string, double> Breakdown { get; set; } = new();
}

public class ExplainabilityInsightDto
{
    [JsonPropertyName("feature_attributions")]
    public Dictionary<string, double> FeatureAttributions { get; set; } = new();

    [JsonPropertyName("summary")]
    public string Summary { get; set; } = string.Empty;
}

public class TelemetryInfoDto
{
    [JsonPropertyName("latency_ms")]
    public double LatencyMs { get; set; }

    [JsonPropertyName("model_version")]
    public string ModelVersion { get; set; } = "1.0.0";

    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;
}

public class AiAnalyzeTextResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "success";

    [JsonPropertyName("original_text")]
    public string OriginalText { get; set; } = string.Empty;

    [JsonPropertyName("sanitized_text")]
    public string SanitizedText { get; set; } = string.Empty;

    [JsonPropertyName("dlp_findings")]
    public List<AiDlpFindingDto> DlpFindings { get; set; } = new();

    [JsonPropertyName("token_map")]
    public Dictionary<string, string> TokenMap { get; set; } = new();

    [JsonPropertyName("threat_prediction")]
    public ThreatPredictionDto ThreatPrediction { get; set; } = new();

    [JsonPropertyName("risk_evaluation")]
    public RiskDecisionDto RiskEvaluation { get; set; } = new();

    [JsonPropertyName("explainability")]
    public ExplainabilityInsightDto? Explainability { get; set; }

    [JsonPropertyName("telemetry")]
    public TelemetryInfoDto Telemetry { get; set; } = new();

    [JsonPropertyName("source_engine")]
    public string SourceEngine { get; set; } = "FastApiMicroservice";
}

public class AudioSpectralFeaturesDto
{
    [JsonPropertyName("spectral_centroid_hz")]
    public double SpectralCentroidHz { get; set; }

    [JsonPropertyName("spectral_bandwidth_hz")]
    public double SpectralBandwidthHz { get; set; }

    [JsonPropertyName("f0_mean_hz")]
    public double F0MeanHz { get; set; }

    [JsonPropertyName("pitch_stability_score")]
    public double PitchStabilityScore { get; set; }

    [JsonPropertyName("speech_duration_sec")]
    public double SpeechDurationSec { get; set; }

    [JsonPropertyName("voice_category")]
    public string VoiceCategory { get; set; } = string.Empty;
}

public class AudioTranscriptionResultDto
{
    [JsonPropertyName("raw_text")]
    public string RawText { get; set; } = string.Empty;

    [JsonPropertyName("detected_language")]
    public string DetectedLanguage { get; set; } = "en";

    [JsonPropertyName("segments_count")]
    public int SegmentsCount { get; set; }

    [JsonPropertyName("duration_seconds")]
    public double DurationSeconds { get; set; }
}

public class AiAnalyzeVoiceResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "success";

    [JsonPropertyName("deepfake_score")]
    public double DeepfakeScore { get; set; }

    [JsonPropertyName("is_deepfake")]
    public bool IsDeepfake { get; set; }

    [JsonPropertyName("spectral_features")]
    public AudioSpectralFeaturesDto SpectralFeatures { get; set; } = new();

    [JsonPropertyName("transcription")]
    public AudioTranscriptionResultDto Transcription { get; set; } = new();

    [JsonPropertyName("sanitized_text")]
    public string SanitizedText { get; set; } = string.Empty;

    [JsonPropertyName("dlp_findings")]
    public List<AiDlpFindingDto> DlpFindings { get; set; } = new();

    [JsonPropertyName("token_map")]
    public Dictionary<string, string> TokenMap { get; set; } = new();

    [JsonPropertyName("threat_prediction")]
    public ThreatPredictionDto ThreatPrediction { get; set; } = new();

    [JsonPropertyName("risk_evaluation")]
    public RiskDecisionDto RiskEvaluation { get; set; } = new();

    [JsonPropertyName("explainability")]
    public ExplainabilityInsightDto? Explainability { get; set; }

    [JsonPropertyName("telemetry")]
    public TelemetryInfoDto Telemetry { get; set; } = new();

    [JsonPropertyName("source_engine")]
    public string SourceEngine { get; set; } = "FastApiMicroservice";
}

public class AiDlpDetokenizeRequest
{
    [JsonPropertyName("masked_text")]
    public string MaskedText { get; set; } = string.Empty;

    [JsonPropertyName("token_map")]
    public Dictionary<string, string>? TokenMap { get; set; }
}

public class AiDlpDetokenizeResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "success";

    [JsonPropertyName("restored_text")]
    public string RestoredText { get; set; } = string.Empty;

    [JsonPropertyName("restored_count")]
    public int RestoredCount { get; set; }
}

public class AiEngineHealthResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "healthy";

    [JsonPropertyName("version")]
    public string Version { get; set; } = "1.0.0";

    [JsonPropertyName("service_name")]
    public string ServiceName { get; set; } = "EASP AI Integration & Security Microservice";

    [JsonPropertyName("owner")]
    public string Owner { get; set; } = "AI 4 (kareem)";

    [JsonPropertyName("models_loaded")]
    public Dictionary<string, bool> ModelsLoaded { get; set; } = new();

    [JsonPropertyName("device")]
    public string Device { get; set; } = "cpu";

    [JsonPropertyName("connected")]
    public bool Connected { get; set; } = true;
}
