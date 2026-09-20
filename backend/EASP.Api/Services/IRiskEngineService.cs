using EASP.Api.DTOs;

namespace EASP.Api.Services;

/// <summary>
/// Service interface for Phase 6 Risk-Based Security Engine (T-P06-033, T-P06-034, T-P06-035).
/// </summary>
public interface IRiskEngineService
{
    /// <summary>
    /// Evaluates multi-modal threat telemetry using weighted fusion, compound threat multipliers,
    /// dynamic policy rules, and persists an append-only audit log.
    /// </summary>
    Task<RiskEvaluationResponse> EvaluateRiskAsync(
        RiskEvaluationRequest request,
        string? userId = null,
        string? correlationId = null,
        string? ipAddress = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieves current engine configuration, weights, and active policy count.
    /// </summary>
    Task<RiskEngineHealthDto> GetHealthAsync(CancellationToken cancellationToken = default);
}
