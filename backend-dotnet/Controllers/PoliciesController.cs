using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using EASP.API.Data;
using EASP.API.Models;

namespace EASP.API.Controllers
{
    [ApiController]
    [Route("api/v1/policies")]
    [Authorize]
    public class PoliciesController : ControllerBase
    {
        private readonly AppDbContext _db;

        public PoliciesController(AppDbContext db) => _db = db;

        private string GetRole() => User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value ?? "Employee";

        // GET /api/v1/policies
        [HttpGet]
        public async Task<IActionResult> GetPolicies()
        {
            var role = GetRole();
            if (!new[] { "Analyst", "Administrator" }.Contains(role))
                return StatusCode(403, new { status = "error", error = "Insufficient permissions" });

            var rawPolicies = await _db.Policies.OrderBy(p => p.Priority).ToListAsync();

            var policies = rawPolicies.Select(p => new
            {
                policyId = p.Name,
                name = p.Name.Replace("_", " "),
                description = p.Description,
                action = p.Action,
                priority = p.Priority,
                conditions = new
                {
                    voiceRiskThreshold = p.MinRiskScore,
                    socialEngThreshold = p.MinRiskScore,
                    dlpSeverityThreshold = p.RequireDlpRedaction ? "HIGH" : "ANY"
                },
                isActive = p.IsActive,
                createdAt = p.CreatedAt
            }).ToList();

            return Ok(new
            {
                status = "success",
                data = new
                {
                    policies
                }
            });
        }

        // POST /api/v1/policies
        [HttpPost]
        public async Task<IActionResult> CreatePolicy([FromBody] CreatePolicyFrontendRequest req)
        {
            var role = GetRole();
            if (role != "Administrator")
                return StatusCode(403, new { status = "error", error = "Only Administrators can create policies" });

            var policyName = req.PolicyId ?? req.Name ?? $"POL_{Guid.NewGuid().ToString("N").Substring(0, 6).ToUpper()}";
            var exists = await _db.Policies.AnyAsync(p => p.Name == policyName);
            if (exists)
                return Conflict(new { status = "error", error = "Policy with this ID/Name already exists" });

            var validActions = new[] { "ALLOW", "REDACT", "ESCALATE", "BLOCK" };
            var action = req.Action?.ToUpper() ?? "BLOCK";
            if (!validActions.Contains(action))
                return BadRequest(new { status = "error", error = "Invalid action" });

            var minRisk = req.Conditions?.VoiceRiskThreshold ?? 0.50;

            var policy = new Policy
            {
                Name = policyName,
                Description = req.Description ?? req.Name ?? "Custom rule",
                TargetRole = "All",
                MinRiskScore = minRisk,
                MaxRiskScore = 1.0,
                Action = action,
                RequireDlpRedaction = true,
                Priority = req.Priority > 0 ? req.Priority : 50,
                IsActive = true
            };

            _db.Policies.Add(policy);
            await _db.SaveChangesAsync();

            return StatusCode(201, new
            {
                status = "success",
                message = "Policy created successfully",
                data = new
                {
                    policyId = policy.Name,
                    name = policy.Name,
                    description = policy.Description,
                    action = policy.Action,
                    priority = policy.Priority,
                    isActive = policy.IsActive
                }
            });
        }

        // DELETE /api/v1/policies/{id}
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeletePolicy(string id)
        {
            var role = GetRole();
            if (role != "Administrator")
                return StatusCode(403, new { status = "error", error = "Only Administrators can delete policies" });

            Policy? policy = null;
            if (int.TryParse(id, out var intId))
            {
                policy = await _db.Policies.FindAsync(intId);
            }
            if (policy == null)
            {
                policy = await _db.Policies.FirstOrDefaultAsync(p => p.Name == id);
            }

            if (policy == null)
                return NotFound(new { status = "error", error = "Policy not found" });

            _db.Policies.Remove(policy);
            await _db.SaveChangesAsync();
            return Ok(new { status = "success", message = "Policy deleted" });
        }
    }

    public class CreatePolicyFrontendRequest
    {
        public string? PolicyId { get; set; }
        public string? Name { get; set; }
        public string? Description { get; set; }
        public string? Action { get; set; }
        public int Priority { get; set; } = 50;
        public PolicyConditionsDto? Conditions { get; set; }
    }

    public class PolicyConditionsDto
    {
        public double VoiceRiskThreshold { get; set; }
        public double SocialEngThreshold { get; set; }
        public string? DlpSeverityThreshold { get; set; }
    }
}
