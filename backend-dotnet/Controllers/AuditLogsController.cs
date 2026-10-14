using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using EASP.API.Data;
using EASP.API.Services;

namespace EASP.API.Controllers
{
    [ApiController]
    [Route("api/v1/audit-logs")]
    [Authorize]
    public class AuditLogsController : ControllerBase
    {
        private readonly AppDbContext _db;
        private readonly AuditService _audit;

        public AuditLogsController(AppDbContext db, AuditService audit)
        {
            _db = db;
            _audit = audit;
        }

        private string GetRole() => User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value ?? "Employee";

        // GET /api/v1/audit-logs
        [HttpGet]
        public async Task<IActionResult> GetLogs(
            [FromQuery] string? eventType = null,
            [FromQuery] int page = 1,
            [FromQuery] int limit = 50)
        {
            var role = GetRole();
            if (!new[] { "Analyst", "Administrator" }.Contains(role))
                return StatusCode(403, new { status = "error", error = "Insufficient permissions" });

            var query = _db.AuditLogs.AsQueryable();
            if (!string.IsNullOrWhiteSpace(eventType)) query = query.Where(a => a.EventType == eventType.ToUpper());

            var total = await query.CountAsync();
            var rawLogs = await query
                .OrderByDescending(a => a.Timestamp)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();

            var logs = rawLogs.Select(a => new
            {
                _id = a.Id.ToString(),
                id = a.Id,
                timestamp = a.Timestamp.ToString("o"),
                eventType = a.EventType,
                actor = new
                {
                    userId = a.UserId.ToString(),
                    email = a.Username ?? "system@easp.local",
                    role = a.UserRole
                },
                ipAddress = a.IpAddress,
                actionTaken = a.ActionTaken,
                riskScore = a.RiskScore,
                riskLevel = a.RiskLevel,
                recordHash = a.Hash,
                previousHash = a.PreviousHash,
                details = a.Details
            }).ToList();

            return Ok(new
            {
                status = "success",
                data = new
                {
                    logs,
                    total,
                    page,
                    limit
                }
            });
        }

        // GET /api/v1/audit-logs/verify
        [HttpGet("verify")]
        public async Task<IActionResult> VerifyChain()
        {
            var role = GetRole();
            if (!new[] { "Analyst", "Administrator" }.Contains(role))
                return StatusCode(403, new { status = "error", error = "Insufficient permissions to verify the audit chain" });

            var result = await _audit.VerifyChainAsync();
            return Ok(new
            {
                status = "success",
                data = new
                {
                    chainValid = result.Valid,
                    verifiedRecords = result.TotalRecords,
                    headHash = result.HeadHash,
                    message = result.Message
                }
            });
        }
    }
}
