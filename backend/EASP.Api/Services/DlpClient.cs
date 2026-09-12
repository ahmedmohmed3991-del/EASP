using System.Diagnostics;
using System.Net.Http.Json;
using System.Text.RegularExpressions;
using EASP.Api.DTOs;

namespace EASP.Api.Services;

/// <summary>
/// T-P03-023: Implementation of DLP Microservice Client using HttpClientFactory.
/// Includes intelligent resilience and local regex fallback when the Python microservice is offline.
/// </summary>
public class DlpClient : IDlpClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<DlpClient> _logger;

    // High-performance compiled regex patterns for fallback PII detection
    private static readonly (string EntityType, Regex Pattern, double Confidence)[] FallbackPatterns =
    {
        ("EMAIL_ADDRESS", new Regex(@"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", RegexOptions.Compiled | RegexOptions.IgnoreCase), 0.98),
        ("CREDIT_CARD", new Regex(@"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b", RegexOptions.Compiled), 0.95),
        ("PHONE_NUMBER", new Regex(@"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", RegexOptions.Compiled), 0.85),
        ("IPV4_ADDRESS", new Regex(@"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", RegexOptions.Compiled), 0.90)
    };

    public DlpClient(HttpClient httpClient, ILogger<DlpClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<DlpAnalyzeResponse> AnalyzeAsync(DlpAnalyzeRequest request, CancellationToken cancellationToken = default)
    {
        var stopwatch = Stopwatch.StartNew();

        try
        {
            // Attempt communicating with the upstream DLP FastAPI microservice
            using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            cts.CancelAfter(TimeSpan.FromSeconds(3)); // Fast timeout to trigger resilient fallback

            var response = await _httpClient.PostAsJsonAsync("api/v1/dlp/analyze", request, cts.Token);
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<DlpAnalyzeResponse>(cancellationToken: cancellationToken);
                if (result != null)
                {
                    result.ProcessingTimeMs = stopwatch.ElapsedMilliseconds;
                    result.SourceEngine = "DlpMicroservice";
                    return result;
                }
            }

            _logger.LogWarning("DLP microservice returned status {StatusCode}. Falling back to internal scanner.", response.StatusCode);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException or OperationCanceledException)
        {
            _logger.LogWarning("DLP microservice unreachable ({Error}). Engaging internal resilient fallback scanner.", ex.Message);
        }

        // Resilient Fallback: Internal Regex Scanner
        return PerformInternalAnalysis(request.Text, stopwatch);
    }

    public async Task<DlpAnonymizeResponse> AnonymizeAsync(DlpAnonymizeRequest request, CancellationToken cancellationToken = default)
    {
        var analyzeResult = await AnalyzeAsync(new DlpAnalyzeRequest { Text = request.Text }, cancellationToken);

        return new DlpAnonymizeResponse
        {
            OriginalText = request.Text,
            AnonymizedText = analyzeResult.MaskedText,
            EntitiesRedactedCount = analyzeResult.DetectedEntities.Count
        };
    }

    private static DlpAnalyzeResponse PerformInternalAnalysis(string text, Stopwatch stopwatch)
    {
        var matches = new List<DlpEntityMatch>();
        var maskedText = text;

        foreach (var (entityType, regex, confidence) in FallbackPatterns)
        {
            var matchCollection = regex.Matches(text);
            foreach (Match match in matchCollection)
            {
                matches.Add(new DlpEntityMatch
                {
                    EntityType = entityType,
                    Value = match.Value,
                    StartIndex = match.Index,
                    EndIndex = match.Index + match.Length,
                    Confidence = confidence
                });
            }
        }

        // Filter out overlapping matches (higher confidence / larger match wins)
        var nonOverlappingMatches = new List<DlpEntityMatch>();
        foreach (var match in matches.OrderByDescending(m => m.Confidence).ThenBy(m => m.StartIndex))
        {
            var overlaps = nonOverlappingMatches.Any(existing =>
                Math.Max(existing.StartIndex, match.StartIndex) < Math.Min(existing.EndIndex, match.EndIndex));

            if (!overlaps)
            {
                nonOverlappingMatches.Add(match);
            }
        }

        // Sort descending by position so masking doesn't offset subsequent indices
        foreach (var entity in nonOverlappingMatches.OrderByDescending(m => m.StartIndex))
        {
            var replacement = $"[REDACTED_{entity.EntityType}]";
            maskedText = maskedText.Remove(entity.StartIndex, entity.EndIndex - entity.StartIndex).Insert(entity.StartIndex, replacement);
        }

        stopwatch.Stop();

        return new DlpAnalyzeResponse
        {
            HasSensitiveData = nonOverlappingMatches.Count > 0,
            DetectedEntities = nonOverlappingMatches.OrderBy(m => m.StartIndex).ToList(),
            MaskedText = maskedText,
            ProcessingTimeMs = stopwatch.ElapsedMilliseconds,
            SourceEngine = "InternalFallbackScanner"
        };
    }
}
