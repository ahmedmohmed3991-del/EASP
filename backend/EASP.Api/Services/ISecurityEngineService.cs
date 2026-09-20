using EASP.Api.DTOs;

namespace EASP.Api.Services;

/// <summary>
/// T-P10-050: Security Engine Layer — typed HttpClient interface for the Python FastAPI AI microservice.
/// Exposes text analysis, voice deepfake analysis, DLP restore, and health check operations.
/// </summary>
public interface ISecurityEngineService
{
    /// <summary>
    /// Sends text to the FastAPI AI microservice for DLP scanning, prompt-injection classification,
    /// multi-modal risk scoring, and explainability attribution.
    /// </summary>
    Task<AiAnalyzeTextResponse> AnalyzeTextAsync(
        string text,
        string? userId = null,
        bool enableDlp = true,
        bool enableExplainability = true,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends an audio file to the FastAPI AI microservice for voice deepfake detection,
    /// Faster-Whisper STT transcription, DLP redaction on transcript, and fused risk decision.
    /// </summary>
    Task<AiAnalyzeVoiceResponse> AnalyzeVoiceAsync(
        Stream audioStream,
        string filename,
        bool enableDlp = true,
        bool enableExplainability = true,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Restores DLP-redacted tokens back to their original plaintext via the FastAPI AES-256 vault.
    /// </summary>
    Task<AiDlpDetokenizeResponse> RestoreDlpAsync(
        string maskedText,
        Dictionary<string, string>? tokenMap = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Performs a health check against the FastAPI AI microservice.
    /// Returns model load status, device, and connectivity.
    /// </summary>
    Task<AiEngineHealthResponse> GetHealthAsync(CancellationToken cancellationToken = default);
}
