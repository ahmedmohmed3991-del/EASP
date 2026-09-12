using EASP.Api.DTOs;

namespace EASP.Api.Services;

/// <summary>
/// T-P03-023: Typed client for the Data Loss Prevention (DLP) service.
/// Provides detection and redaction of sensitive PII/secrets.
/// </summary>
public interface IDlpClient
{
    Task<DlpAnalyzeResponse> AnalyzeAsync(DlpAnalyzeRequest request, CancellationToken cancellationToken = default);
    Task<DlpAnonymizeResponse> AnonymizeAsync(DlpAnonymizeRequest request, CancellationToken cancellationToken = default);
}
