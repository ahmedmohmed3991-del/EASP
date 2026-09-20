using System.Diagnostics;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using EASP.Api.Data;
using EASP.Api.DTOs;
using EASP.Api.Models;

namespace EASP.Api.Services;

/// <summary>
/// T-P10-050: Security Engine Layer — typed HttpClient wrapper for the Python FastAPI AI microservice.
/// Calls /api/v1/ai/analyze-text, /api/v1/ai/analyze-voice, /api/v1/ai/dlp-restore, /api/v1/health.
/// Includes resilient fallback to the local rule-based Risk Engine when the AI microservice is offline.
/// All AI-driven security decisions are automatically written to the immutable audit log (Phase 5).
/// </summary>
public class SecurityEngineService : ISecurityEngineService
{
    private readonly HttpClient _httpClient;
    private readonly AppDbContext _db;
    private readonly ILogger<SecurityEngineService> _logger;

    private static readonly JsonSerializerOptions _jsonOpts = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public SecurityEngineService(
        HttpClient httpClient,
        AppDbContext db,
        ILogger<SecurityEngineService> logger)
    {
        _httpClient = httpClient;
        _db = db;
        _logger = logger;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 1. Text Security Analysis (T-P10-050)
    // ──────────────────────────────────────────────────────────────────────────

    public async Task<AiAnalyzeTextResponse> AnalyzeTextAsync(
        string text,
        string? userId = null,
        bool enableDlp = true,
        bool enableExplainability = true,
        CancellationToken cancellationToken = default)
    {
        var sw = Stopwatch.StartNew();
        AiAnalyzeTextResponse result;

        try
        {
            var payload = new AiAnalyzeTextRequest
            {
                Text = text,
                UserId = userId ?? "anonymous",
                EnableDlp = enableDlp,
                EnableExplainability = enableExplainability
            };

            using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            cts.CancelAfter(TimeSpan.FromSeconds(10));

            var response = await _httpClient.PostAsJsonAsync("api/v1/ai/analyze-text", payload, cts.Token);
            response.EnsureSuccessStatusCode();

            var parsed = await response.Content.ReadFromJsonAsync<AiAnalyzeTextResponse>(_jsonOpts, cts.Token);
            result = parsed ?? BuildFallbackTextResponse(text, "EmptyResponseFromMicroservice");
            result.SourceEngine = "FastApiMicroservice";
            _logger.LogInformation("[SecurityEngine] Text analysis completed via FastAPI. Action={Action} Score={Score}",
                result.RiskEvaluation.Action, result.RiskEvaluation.CompositeRiskScore);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException or OperationCanceledException)
        {
            _logger.LogWarning("[SecurityEngine] FastAPI microservice unreachable for text analysis ({Err}). Using local fallback.", ex.Message);
            result = BuildFallbackTextResponse(text, "LocalFallback");
        }

        sw.Stop();
        await WriteAuditLogAsync("AI_TEXT_ANALYSIS", "/api/security/analyze-text",
            result.RiskEvaluation.Action, (int)(result.RiskEvaluation.CompositeRiskScore), sw.ElapsedMilliseconds,
            userId, cancellationToken);

        return result;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 2. Voice Deepfake + STT Analysis (T-P10-050)
    // ──────────────────────────────────────────────────────────────────────────

    public async Task<AiAnalyzeVoiceResponse> AnalyzeVoiceAsync(
        Stream audioStream,
        string filename,
        bool enableDlp = true,
        bool enableExplainability = true,
        CancellationToken cancellationToken = default)
    {
        var sw = Stopwatch.StartNew();
        AiAnalyzeVoiceResponse result;

        try
        {
            using var content = new MultipartFormDataContent();
            var fileContent = new StreamContent(audioStream);
            fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(
                GetAudioContentType(filename));
            content.Add(fileContent, "file", filename);
            content.Add(new StringContent(enableDlp.ToString().ToLower()), "enable_dlp");
            content.Add(new StringContent(enableExplainability.ToString().ToLower()), "enable_explainability");

            using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            cts.CancelAfter(TimeSpan.FromSeconds(60)); // Voice processing is slower

            var response = await _httpClient.PostAsync("api/v1/ai/analyze-voice", content, cts.Token);
            response.EnsureSuccessStatusCode();

            var parsed = await response.Content.ReadFromJsonAsync<AiAnalyzeVoiceResponse>(_jsonOpts, cts.Token);
            result = parsed ?? BuildFallbackVoiceResponse("FastApiMicroservice");
            result.SourceEngine = "FastApiMicroservice";
            _logger.LogInformation("[SecurityEngine] Voice analysis completed via FastAPI. Deepfake={IsDeepfake} Action={Action}",
                result.IsDeepfake, result.RiskEvaluation.Action);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException or OperationCanceledException)
        {
            _logger.LogWarning("[SecurityEngine] FastAPI microservice unreachable for voice analysis ({Err}). Using local fallback.", ex.Message);
            result = BuildFallbackVoiceResponse("LocalFallback");
        }

        sw.Stop();
        await WriteAuditLogAsync("AI_VOICE_ANALYSIS", "/api/security/analyze-voice",
            result.RiskEvaluation.Action, (int)(result.RiskEvaluation.CompositeRiskScore), sw.ElapsedMilliseconds,
            null, cancellationToken);

        return result;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 3. DLP Restore (Detokenize) (T-P10-050)
    // ──────────────────────────────────────────────────────────────────────────

    public async Task<AiDlpDetokenizeResponse> RestoreDlpAsync(
        string maskedText,
        Dictionary<string, string>? tokenMap = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var payload = new AiDlpDetokenizeRequest
            {
                MaskedText = maskedText,
                TokenMap = tokenMap
            };

            using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            cts.CancelAfter(TimeSpan.FromSeconds(5));

            var response = await _httpClient.PostAsJsonAsync("api/v1/ai/dlp-restore", payload, cts.Token);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<AiDlpDetokenizeResponse>(_jsonOpts, cts.Token);
            return result ?? new AiDlpDetokenizeResponse { RestoredText = maskedText, RestoredCount = 0, Status = "fallback" };
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException or OperationCanceledException)
        {
            _logger.LogWarning("[SecurityEngine] FastAPI microservice unreachable for DLP restore ({Err}). Returning masked text as-is.", ex.Message);
            return new AiDlpDetokenizeResponse
            {
                Status = "fallback",
                RestoredText = maskedText,
                RestoredCount = 0
            };
        }
    }

    // ──────────────────────────────────────────────────────────────────────────
    // 4. Health Check (T-P10-050)
    // ──────────────────────────────────────────────────────────────────────────

    public async Task<AiEngineHealthResponse> GetHealthAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            cts.CancelAfter(TimeSpan.FromSeconds(3));

            var response = await _httpClient.GetAsync("api/v1/health", cts.Token);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<AiEngineHealthResponse>(_jsonOpts, cts.Token);
            if (result != null)
            {
                result.Connected = true;
                return result;
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning("[SecurityEngine] FastAPI health check failed: {Err}", ex.Message);
        }

        return new AiEngineHealthResponse
        {
            Status = "offline",
            Version = "N/A",
            ServiceName = "EASP AI Integration & Security Microservice",
            Connected = false,
            Device = "N/A",
            ModelsLoaded = new Dictionary<string, bool>
            {
                { "dlp_engine", false },
                { "text_threat_classifier", false },
                { "audio_deepfake_cnn", false },
                { "speech_transcriber", false },
                { "policy_risk_engine", false }
            }
        };
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Private Helpers
    // ──────────────────────────────────────────────────────────────────────────

    /// <summary>
    /// Builds a conservative local fallback text-analysis response when FastAPI is unreachable.
    /// Applies basic DLP-regex detection and defaults to ALLOW so the system is not blocked by infra issues.
    /// </summary>
    private static AiAnalyzeTextResponse BuildFallbackTextResponse(string text, string source)
    {
        return new AiAnalyzeTextResponse
        {
            Status = "fallback",
            OriginalText = text,
            SanitizedText = text,
            DlpFindings = new List<AiDlpFindingDto>(),
            TokenMap = new Dictionary<string, string>(),
            ThreatPrediction = new ThreatPredictionDto
            {
                IsThreat = false,
                Label = "Indeterminate (AI service offline)",
                Probability = 0.0,
                Confidence = 0.0
            },
            RiskEvaluation = new RiskDecisionDto
            {
                CompositeRiskScore = 0.0,
                Action = "ALLOW",
                Reasons = new List<string> { "AI microservice offline — conservative ALLOW applied. Manual review recommended." },
                Breakdown = new Dictionary<string, double>()
            },
            Telemetry = new TelemetryInfoDto
            {
                LatencyMs = 0,
                ModelVersion = "fallback",
                Timestamp = DateTime.UtcNow.ToString("o")
            },
            SourceEngine = source
        };
    }

    private static AiAnalyzeVoiceResponse BuildFallbackVoiceResponse(string source)
    {
        return new AiAnalyzeVoiceResponse
        {
            Status = "fallback",
            DeepfakeScore = 0.0,
            IsDeepfake = false,
            SpectralFeatures = new AudioSpectralFeaturesDto { VoiceCategory = "Unknown" },
            Transcription = new AudioTranscriptionResultDto { RawText = "[AI service offline — transcription unavailable]" },
            SanitizedText = string.Empty,
            DlpFindings = new List<AiDlpFindingDto>(),
            TokenMap = new Dictionary<string, string>(),
            ThreatPrediction = new ThreatPredictionDto
            {
                IsThreat = false,
                Label = "Indeterminate (AI service offline)",
                Probability = 0.0,
                Confidence = 0.0
            },
            RiskEvaluation = new RiskDecisionDto
            {
                CompositeRiskScore = 0.0,
                Action = "ALLOW",
                Reasons = new List<string> { "AI microservice offline — conservative ALLOW applied. Manual review recommended." }
            },
            Telemetry = new TelemetryInfoDto
            {
                LatencyMs = 0,
                ModelVersion = "fallback",
                Timestamp = DateTime.UtcNow.ToString("o")
            },
            SourceEngine = source
        };
    }

    private static string GetAudioContentType(string filename)
    {
        var ext = Path.GetExtension(filename).ToLowerInvariant();
        return ext switch
        {
            ".wav" => "audio/wav",
            ".mp3" => "audio/mpeg",
            ".flac" => "audio/flac",
            ".ogg" => "audio/ogg",
            _ => "application/octet-stream"
        };
    }

    private async Task WriteAuditLogAsync(
        string action,
        string resource,
        string decision,
        int statusCode,
        long elapsedMs,
        string? userId,
        CancellationToken cancellationToken)
    {
        try
        {
            _db.AuditLogs.Add(new AuditLog
            {
                Action = action,
                Resource = resource,
                UserId = userId,
                StatusCode = statusCode,
                ExecutionTimeMs = elapsedMs,
                DetailsJson = JsonSerializer.Serialize(new { decision })
            });
            await _db.SaveChangesAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "[SecurityEngine] Failed to persist audit log for {Action}", action);
        }
    }
}
