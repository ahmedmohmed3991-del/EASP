using System.Text.Json;
using EASP.API.Data;
using EASP.API.Models;
using Microsoft.EntityFrameworkCore;

namespace EASP.API.Services
{
    public class PolicyEngine
    {
        private readonly AppDbContext _db;
        private readonly AuditService _audit;

        public PolicyEngine(AppDbContext db, AuditService audit)
        {
            _db = db;
            _audit = audit;
        }

        /// <summary>Evaluate applicable policies and enforce action, creating incidents as needed</summary>
        public async Task<PolicyDecision> EvaluatePolicyAsync(
            int userId,
            string username,
            string userRole,
            string ipAddress,
            double riskScore,
            string riskLevel,
            object? dlpFindings,
            Dictionary<string, double> contributingFactors,
            string source)
        {
            // Load active policies ordered by priority (lower = higher)
            var policies = await _db.Policies
                .Where(p => p.IsActive &&
                            p.MinRiskScore <= riskScore &&
                            p.MaxRiskScore >= riskScore &&
                            (p.TargetRole == "All" || p.TargetRole == userRole))
                .OrderBy(p => p.Priority)
                .ToListAsync();

            // Default to ALLOW
            var matchedPolicy = policies.FirstOrDefault();
            var action = matchedPolicy?.Action ?? "ALLOW";
            var policyName = matchedPolicy?.Name ?? "DEFAULT_ALLOW";
            var requireDlpRedaction = matchedPolicy?.RequireDlpRedaction ?? false;

            // Build details
            var details = new
            {
                policyName,
                action,
                riskScore,
                riskLevel,
                source,
                contributingFactors,
                dlpFindings
            };
            var detailsJson = JsonSerializer.Serialize(details);

            // Log to audit chain
            var auditLog = await _audit.LogEventAsync(
                "POLICY_DECISION",
                action,
                userId,
                username,
                userRole,
                ipAddress,
                riskScore,
                riskLevel,
                detailsJson
            );

            // Create incident for escalate/block or medium+ risk
            int? incidentId = null;
            if (action is "ESCALATE" or "BLOCK" || riskLevel is "MEDIUM" or "HIGH")
            {
                var severity = riskLevel switch
                {
                    "HIGH" when action == "BLOCK" => "CRITICAL",
                    "HIGH" => "HIGH",
                    "MEDIUM" => "MEDIUM",
                    _ => "LOW"
                };

                var incident = new Incident
                {
                    Title = $"[{source}] {action} — Risk: {riskLevel} ({riskScore:F2})",
                    Severity = severity,
                    Status = "OPEN",
                    Source = source,
                    UserId = userId,
                    Username = username,
                    RiskScore = riskScore,
                    RiskLevel = riskLevel,
                    VoiceRisk = contributingFactors.GetValueOrDefault("voiceRisk"),
                    SocialRisk = contributingFactors.GetValueOrDefault("socialRisk"),
                    DlpSensitivity = contributingFactors.GetValueOrDefault("dlpSensitivity"),
                    ActionTaken = action,
                    AuditLogId = auditLog.Id
                };
                _db.Incidents.Add(incident);
                await _db.SaveChangesAsync();
                incidentId = incident.Id;
            }

            return new PolicyDecision
            {
                Action = action,
                PolicyName = policyName,
                RequireDlpRedaction = requireDlpRedaction,
                AuditLogId = auditLog.Id,
                IncidentId = incidentId
            };
        }
    }

    public class PolicyDecision
    {
        public string Action { get; set; } = "ALLOW";
        public string PolicyName { get; set; } = string.Empty;
        public bool RequireDlpRedaction { get; set; }
        public int AuditLogId { get; set; }
        public int? IncidentId { get; set; }
    }
}
