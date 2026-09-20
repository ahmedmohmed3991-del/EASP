using System.Diagnostics;
using System.Text.Json;
using EASP.Api.Data;
using EASP.Api.DTOs;
using EASP.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace EASP.Api.Services;

/// <summary>
/// Implementation of Phase 6 Risk-Based Security Engine (T-P06-033, T-P06-034, T-P06-035).
/// Combines weighted multi-factor threat fusion, compound threat multipliers,
/// dynamic enterprise policy linkage, and immutable audit logging.
/// </summary>
public class RiskEngineService : IRiskEngineService
{
    private readonly AppDbContext _dbContext;
    private readonly IConfiguration _configuration;
    private readonly ILogger<RiskEngineService> _logger;

    public RiskEngineService(
        AppDbContext dbContext,
        IConfiguration configuration,
        ILogger<RiskEngineService> logger)
    {
        _dbContext = dbContext;
        _configuration = configuration;
        _logger = logger;
    }

    public async Task<RiskEvaluationResponse> EvaluateRiskAsync(
        RiskEvaluationRequest request,
        string? userId = null,
        string? correlationId = null,
        string? ipAddress = null,
        CancellationToken cancellationToken = default)
    {
        var stopwatch = Stopwatch.StartNew();

        // 1. Retrieve configured weights and thresholds
        var wInjection = _configuration.GetValue<double>("RiskEngine:Weights:PromptInjection", 0.35);
        var wDeepfake = _configuration.GetValue<double>("RiskEngine:Weights:Deepfake", 0.35);
        var wSocialEng = _configuration.GetValue<double>("RiskEngine:Weights:SocialEngineering", 0.15);
        var wPii = _configuration.GetValue<double>("RiskEngine:Weights:PiiLeakage", 0.15);

        var allowThreshold = _configuration.GetValue<double>("RiskEngine:AllowThreshold", 35.0);
        var blockThreshold = _configuration.GetValue<double>("RiskEngine:BlockThreshold", 70.0);

        // 2. Component Contributions (0-100 scale)
        var piScore = Math.Round(request.PromptInjectionProbability * 100.0, 2);
        var dfScore = Math.Round(request.DeepfakeProbability * 100.0, 2);
        var seScore = Math.Round(request.SocialEngineeringProbability * 100.0, 2);
        var piiScore = Math.Round(Math.Max(request.PiiSeverityScore * 100.0, Math.Min(request.PiiEntitiesCount * 20.0, 100.0)), 2);

        var breakdown = new RiskComponentBreakdown
        {
            PromptInjection = piScore,
            VoiceDeepfake = dfScore,
            SocialEngineering = seScore,
            PiiLeakage = piiScore
        };

        // 3. Weighted Base Score
        var baseScore = (piScore * wInjection) +
                        (dfScore * wDeepfake) +
                        (seScore * wSocialEng) +
                        (piiScore * wPii);

        // 4. Compound Threat Multipliers (T-P06-033)
        var multiplier = 1.0;
        var reasons = new List<string>();
        var compoundThreatDetected = false;

        // Compound Threat 1: Voice Deepfake + Social Engineering
        if (request.DeepfakeProbability > 0.65 && request.SocialEngineeringProbability > 0.60)
        {
            multiplier += 0.25;
            compoundThreatDetected = true;
            reasons.Add("Coordinated Multi-Modal Threat: Voice Deepfake combined with Social Engineering.");
        }

        // Compound Threat 2: Prompt Injection attempting PII/Secret exfiltration
        if (request.PromptInjectionProbability > 0.70 && request.PiiEntitiesCount > 0)
        {
            multiplier += 0.20;
            compoundThreatDetected = true;
            reasons.Add("Critical Exfiltration Threat: Prompt Injection attempting PII/Secret extraction.");
        }

        var finalScore = Math.Min(100.0, Math.Round(baseScore * multiplier, 2));

        // 5. Individual Threat Reason Tagging
        if (piScore >= 70.0)
        {
            reasons.Add($"High-confidence Prompt Injection detected ({piScore:F1}%).");
        }
        if (dfScore >= 70.0)
        {
            reasons.Add($"Synthetic / Cloned Voice Deepfake detected ({dfScore:F1}%).");
        }
        if (seScore >= 70.0)
        {
            reasons.Add($"Social Engineering / Phishing pattern identified ({seScore:F1}%).");
        }
        if (request.PiiEntitiesCount > 0)
        {
            reasons.Add($"Sensitive Data Exposure: {request.PiiEntitiesCount} PII entity/secret(s) identified.");
        }

        // 6. Dynamic Policy Linkage (T-P06-034)
        // Inspect active policies in database to check for custom threshold overrides or category-specific rules
        Guid? policyAppliedId = null;
        string? policyName = null;
        string action;

        var activePolicies = await _dbContext.Policies
            .Where(p => p.IsEnabled)
            .OrderByDescending(p => p.Severity == "Critical")
            .ThenByDescending(p => p.Severity == "High")
            .ToListAsync(cancellationToken);

        // Check if a custom policy matches
        var matchingPolicy = FindMatchingPolicy(activePolicies, finalScore, piScore, dfScore, request.PiiEntitiesCount);

        if (matchingPolicy != null)
        {
            policyAppliedId = matchingPolicy.Id;
            policyName = matchingPolicy.Name;
            action = NormalizeAction(matchingPolicy.Action);
            reasons.Add($"Enforced by security policy '{matchingPolicy.Name}' (Severity: {matchingPolicy.Severity}, Action: {action}).");
        }
        else
        {
            // Default threshold decisioning
            if (finalScore >= blockThreshold)
            {
                action = "BLOCK";
                if (!reasons.Any())
                {
                    reasons.Add($"Composite risk score ({finalScore:F1}) exceeds BLOCK threshold ({blockThreshold}).");
                }
            }
            else if (finalScore >= allowThreshold)
            {
                action = "FLAG";
                if (!reasons.Any())
                {
                    reasons.Add($"Composite risk score ({finalScore:F1}) requires SOC analyst review or step-up authentication.");
                }
            }
            else
            {
                action = "ALLOW";
                if (!reasons.Any())
                {
                    reasons.Add("Interaction verified safe against enterprise security baseline.");
                }
            }
        }

        stopwatch.Stop();
        var elapsedMs = stopwatch.ElapsedMilliseconds;

        var response = new RiskEvaluationResponse
        {
            Status = "success",
            CompositeRiskScore = finalScore,
            Action = action,
            Reasons = reasons,
            Breakdown = breakdown,
            CompoundThreatDetected = compoundThreatDetected,
            CompoundThreatMultiplier = Math.Round(multiplier, 2),
            PolicyAppliedId = policyAppliedId,
            PolicyName = policyName,
            EvaluatedAt = DateTime.UtcNow,
            ExecutionLatencyMs = elapsedMs
        };

        // 7. Append-only Audit Log (Phase 5 integration)
        try
        {
            var auditLog = new AuditLog
            {
                Timestamp = DateTime.UtcNow,
                CorrelationId = correlationId,
                UserId = userId,
                Action = "RISK_EVALUATION",
                Resource = "/api/risk/evaluate",
                IpAddress = ipAddress,
                StatusCode = 200,
                ExecutionTimeMs = elapsedMs,
                DetailsJson = JsonSerializer.Serialize(new
                {
                    compositeRiskScore = finalScore,
                    action,
                    compoundThreatDetected,
                    multiplier,
                    policyAppliedId,
                    policyName,
                    breakdown = new
                    {
                        promptInjection = piScore,
                        voiceDeepfake = dfScore,
                        socialEngineering = seScore,
                        piiLeakage = piiScore
                    },
                    reasons
                })
            };

            _dbContext.AuditLogs.Add(auditLog);
            await _dbContext.SaveChangesAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to record audit log for risk evaluation.");
            // We do not fail the request if audit persistence fails, but we log the incident
        }

        return response;
    }

    public async Task<RiskEngineHealthDto> GetHealthAsync(CancellationToken cancellationToken = default)
    {
        var activePoliciesCount = await _dbContext.Policies
            .CountAsync(p => p.IsEnabled, cancellationToken);

        return new RiskEngineHealthDto
        {
            Status = "Healthy",
            AllowThreshold = _configuration.GetValue<double>("RiskEngine:AllowThreshold", 35.0),
            BlockThreshold = _configuration.GetValue<double>("RiskEngine:BlockThreshold", 70.0),
            Weights = new Dictionary<string, double>
            {
                ["PromptInjection"] = _configuration.GetValue<double>("RiskEngine:Weights:PromptInjection", 0.35),
                ["Deepfake"] = _configuration.GetValue<double>("RiskEngine:Weights:Deepfake", 0.35),
                ["SocialEngineering"] = _configuration.GetValue<double>("RiskEngine:Weights:SocialEngineering", 0.15),
                ["PiiLeakage"] = _configuration.GetValue<double>("RiskEngine:Weights:PiiLeakage", 0.15)
            },
            ActivePoliciesCount = activePoliciesCount,
            Timestamp = DateTime.UtcNow
        };
    }

    private static Policy? FindMatchingPolicy(
        List<Policy> policies,
        double compositeScore,
        double piScore,
        double dfScore,
        int piiCount)
    {
        foreach (var policy in policies)
        {
            // Category RISK: matches on risk score threshold
            if (string.Equals(policy.Category, "RISK", StringComparison.OrdinalIgnoreCase))
            {
                var threshold = ExtractThreshold(policy.ConfigurationJson, 70.0);
                if (compositeScore >= threshold)
                {
                    return policy;
                }
            }
            // Category PROMPT_INJECTION: matches if prompt injection score exceeds threshold
            else if (string.Equals(policy.Category, "PROMPT_INJECTION", StringComparison.OrdinalIgnoreCase))
            {
                var threshold = ExtractThreshold(policy.ConfigurationJson, 70.0);
                if (piScore >= threshold)
                {
                    return policy;
                }
            }
            // Category DLP: matches if PII entities detected
            else if (string.Equals(policy.Category, "DLP", StringComparison.OrdinalIgnoreCase) && piiCount > 0)
            {
                return policy;
            }
        }

        return null;
    }

    private static double ExtractThreshold(string configJson, double defaultThreshold)
    {
        if (string.IsNullOrWhiteSpace(configJson))
            return defaultThreshold;

        try
        {
            using var doc = JsonDocument.Parse(configJson);
            if (doc.RootElement.TryGetProperty("threshold", out var thresholdElem) &&
                thresholdElem.TryGetDouble(out var val))
            {
                return val;
            }
        }
        catch
        {
            // Fall back to default
        }

        return defaultThreshold;
    }

    private static string NormalizeAction(string action)
    {
        var upper = action.Trim().ToUpperInvariant();
        return upper switch
        {
            "BLOCK" => "BLOCK",
            "REDACT" => "REDACT",
            "FLAG" or "ESCALATE" or "ALERT" => "FLAG",
            "ALLOW" => "ALLOW",
            _ => upper
        };
    }
}
