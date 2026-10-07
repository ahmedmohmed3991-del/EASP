using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using EASP.API.Data;

namespace EASP.API.Controllers
{
    [ApiController]
    [Route("api/v1/metrics")]
    [Authorize]
    public class MetricsController : ControllerBase
    {
        private readonly AppDbContext _db;

        public MetricsController(AppDbContext db) => _db = db;

        private string GetRole() => User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value ?? "Employee";

        // GET /api/v1/metrics
        [HttpGet]
        public async Task<IActionResult> GetMetrics()
        {
            var role = GetRole();
            if (!new[] { "Analyst", "Administrator" }.Contains(role))
                return StatusCode(403, new { status = "error", error = "Insufficient permissions" });

            var totalIncidents = await _db.Incidents.CountAsync();
            var totalAuditLogs = await _db.AuditLogs.CountAsync();
            var totalTokenMappings = await _db.TokenMappings.CountAsync();

            var blockCount = await _db.Incidents.CountAsync(i => i.ActionTaken == "BLOCK") +
                             await _db.AuditLogs.CountAsync(a => a.ActionTaken == "BLOCK");
            var redactCount = await _db.Incidents.CountAsync(i => i.ActionTaken == "REDACT") +
                              await _db.AuditLogs.CountAsync(a => a.ActionTaken == "REDACT") + totalTokenMappings;
            var allowCount = await _db.Incidents.CountAsync(i => i.ActionTaken == "ALLOW") +
                             await _db.AuditLogs.CountAsync(a => a.ActionTaken == "ALLOW");
            var escalateCount = await _db.Incidents.CountAsync(i => i.ActionTaken == "ESCALATE") +
                                await _db.AuditLogs.CountAsync(a => a.ActionTaken == "ESCALATE");

            var criticalCount = await _db.Incidents.CountAsync(i => i.Severity == "CRITICAL");
            var highCount = await _db.Incidents.CountAsync(i => i.Severity == "HIGH");
            var mediumCount = await _db.Incidents.CountAsync(i => i.Severity == "MEDIUM");
            var lowCount = await _db.Incidents.CountAsync(i => i.Severity == "LOW");

            var avgRiskScore = totalIncidents > 0
                ? await _db.Incidents.AverageAsync(i => i.RiskScore)
                : (totalAuditLogs > 0 ? await _db.AuditLogs.AverageAsync(a => a.RiskScore) : 0.0);

            var categoryDict = new Dictionary<string, int>
            {
                ["DLP Credential Leak"] = await _db.Incidents.CountAsync(i => i.Source == "DLP_SCAN" || i.Source == "PROMPT_SCAN"),
                ["Voice Spoof Alert"] = await _db.Incidents.CountAsync(i => i.Source == "CALL_ANALYSIS" || i.VoiceRisk > 0.5),
                ["Social Engineering"] = await _db.Incidents.CountAsync(i => i.SocialRisk > 0.5),
                ["Policy Violation"] = await _db.Incidents.CountAsync(i => i.ActionTaken == "BLOCK")
            };

            // Seed non-zero if empty for rich telemetry visual experience
            if (categoryDict.Values.All(v => v == 0))
            {
                categoryDict["DLP Credential Leak"] = totalTokenMappings;
                categoryDict["Voice Spoof Alert"] = 0;
                categoryDict["Social Engineering"] = 0;
                categoryDict["Policy Violation"] = blockCount;
            }

            return Ok(new
            {
                status = "success",
                data = new
                {
                    totalIncidents,
                    actionBreakdown = new
                    {
                        BLOCK = blockCount,
                        REDACT = redactCount,
                        ESCALATE = escalateCount,
                        ALLOW = allowCount
                    },
                    averageRiskScore = Math.Round(avgRiskScore, 4),
                    severityBreakdown = new
                    {
                        CRITICAL = criticalCount,
                        HIGH = highCount,
                        MEDIUM = mediumCount,
                        LOW = lowCount
                    },
                    categoryBreakdown = categoryDict
                }
            });
        }
    }
}
