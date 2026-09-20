using System.ComponentModel.DataAnnotations;

namespace EASP.Api.DTOs;

/// <summary>
/// T-P06-035: Incoming multi-modal threat telemetry for risk evaluation.
/// Interoperable with FastAPI AI service and client applications.
/// </summary>
public class RiskEvaluationRequest
{
    [Range(0.0, 1.0, ErrorMessage = "PromptInjectionProbability must be between 0.0 and 1.0")]
    public double PromptInjectionProbability { get; set; } = 0.0;

    [Range(0.0, 1.0, ErrorMessage = "DeepfakeProbability must be between 0.0 and 1.0")]
    public double DeepfakeProbability { get; set; } = 0.0;

    [Range(0.0, 1.0, ErrorMessage = "SocialEngineeringProbability must be between 0.0 and 1.0")]
    public double SocialEngineeringProbability { get; set; } = 0.0;

    [Range(0, 1000, ErrorMessage = "PiiEntitiesCount must be non-negative")]
    public int PiiEntitiesCount { get; set; } = 0;

    [Range(0.0, 1.0, ErrorMessage = "PiiSeverityScore must be between 0.0 and 1.0")]
    public double PiiSeverityScore { get; set; } = 0.0;

    /// <summary>
    /// Optional metadata: e.g. userId, sessionId, sourceIp, channel ("voice", "chat", "email")
    /// </summary>
    public Dictionary<string, object>? Metadata { get; set; }
}

/// <summary>
/// Normalized 0-100 threat component contribution scores.
/// </summary>
public class RiskComponentBreakdown
{
    public double PromptInjection { get; set; }
    public double VoiceDeepfake { get; set; }
    public double SocialEngineering { get; set; }
    public double PiiLeakage { get; set; }
}

/// <summary>
/// T-P06-035: Result of the weighted risk fusion and policy enforcement evaluation.
/// </summary>
public class RiskEvaluationResponse
{
    public string Status { get; set; } = "success";

    /// <summary>
    /// Composite risk score normalized between 0.0 and 100.0
    /// </summary>
    public double CompositeRiskScore { get; set; }

    /// <summary>
    /// Enforced policy action: ALLOW, FLAG, ESCALATE, or BLOCK
    /// </summary>
    public string Action { get; set; } = "ALLOW";

    /// <summary>
    /// Specific risk triggers and explainability statements explaining the evaluation
    /// </summary>
    public List<string> Reasons { get; set; } = new();

    /// <summary>
    /// Component breakdowns on 0-100 scale
    /// </summary>
    public RiskComponentBreakdown Breakdown { get; set; } = new();

    /// <summary>
    /// Flag indicating whether a compound threat pattern was triggered
    /// </summary>
    public bool CompoundThreatDetected { get; set; }

    /// <summary>
    /// Multiplier factor applied (e.g. 1.0, 1.25)
    /// </summary>
    public double CompoundThreatMultiplier { get; set; } = 1.0;

    /// <summary>
    /// ID of the security policy applied if matched from Phase 5 Policy table
    /// </summary>
    public Guid? PolicyAppliedId { get; set; }

    /// <summary>
    /// Name of the matched policy
    /// </summary>
    public string? PolicyName { get; set; }

    public DateTime EvaluatedAt { get; set; } = DateTime.UtcNow;

    public long ExecutionLatencyMs { get; set; }
}

/// <summary>
/// Diagnostic info about active risk engine weights and thresholds.
/// </summary>
public class RiskEngineHealthDto
{
    public string Status { get; set; } = "Healthy";
    public double AllowThreshold { get; set; }
    public double BlockThreshold { get; set; }
    public Dictionary<string, double> Weights { get; set; } = new();
    public int ActivePoliciesCount { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}
