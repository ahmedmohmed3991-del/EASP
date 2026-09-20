using System.Security.Claims;
using EASP.Api.DTOs;
using EASP.Api.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace EASP.Api.Controllers;

/// <summary>
/// T-P06-035: Internal Risk Evaluation Endpoints.
/// Exposes multi-modal threat telemetry analysis, weighted risk fusion,
/// and automated policy-driven decisioning.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class RiskController : ControllerBase
{
    private readonly IRiskEngineService _riskEngineService;
    private readonly ILogger<RiskController> _logger;

    public RiskController(
        IRiskEngineService riskEngineService,
        ILogger<RiskController> logger)
    {
        _riskEngineService = riskEngineService;
        _logger = logger;
    }

    /// <summary>
    /// T-P06-035: Evaluates multi-modal threat telemetry and returns composite risk score + policy action.
    /// </summary>
    /// <param name="request">Threat telemetry payload</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Evaluated risk score, action (ALLOW/FLAG/BLOCK), breakdown, and reasons</returns>
    [HttpPost("evaluate")]
    [ProducesResponseType(typeof(RiskEvaluationResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> Evaluate(
        [FromBody] RiskEvaluationRequest request,
        CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var userId = User.FindFirstValue(ClaimTypes.NameIdentifier) ?? User.Identity?.Name;
        var correlationId = HttpContext.Request.Headers["X-Correlation-ID"].FirstOrDefault()
                            ?? HttpContext.TraceIdentifier;
        var ipAddress = HttpContext.Connection.RemoteIpAddress?.ToString();

        _logger.LogInformation(
            "[{CorrelationId}] Received risk evaluation request for User {UserId}",
            correlationId, userId ?? "Anonymous");

        var response = await _riskEngineService.EvaluateRiskAsync(
            request, userId, correlationId, ipAddress, cancellationToken);

        return Ok(response);
    }

    /// <summary>
    /// Diagnostic endpoint returning active risk engine weights, thresholds, and policy stats.
    /// </summary>
    [HttpGet("health")]
    [ProducesResponseType(typeof(RiskEngineHealthDto), StatusCodes.Status200OK)]
    public async Task<IActionResult> Health(CancellationToken cancellationToken)
    {
        var health = await _riskEngineService.GetHealthAsync(cancellationToken);
        return Ok(health);
    }
}
