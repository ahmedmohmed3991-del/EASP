using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using EASP.API.Data;
using System.Text.Json;

namespace EASP.API.Controllers
{
    [ApiController]
    [Route("api/v1/incidents")]
    [Authorize]
    public class IncidentsController : ControllerBase
    {
        private readonly AppDbContext _db;

        public IncidentsController(AppDbContext db) => _db = db;

        private string GetRole() => User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value ?? "Employee";

        // GET /api/v1/incidents
        [HttpGet]
        public async Task<IActionResult> GetIncidents(
            [FromQuery] string? status = null,
            [FromQuery] string? severity = null,
            [FromQuery] int page = 1,
            [FromQuery] int limit = 50)
        {
            var role = GetRole();
            if (!new[] { "Analyst", "Administrator" }.Contains(role))
                return StatusCode(403, new { status = "error", error = "Insufficient permissions" });

            var query = _db.Incidents.AsQueryable();
            if (!string.IsNullOrWhiteSpace(status)) query = query.Where(i => i.Status == status.ToUpper());
            if (!string.IsNullOrWhiteSpace(severity)) query = query.Where(i => i.Severity == severity.ToUpper());

            var total = await query.CountAsync();
            var rawIncidents = await query
                .OrderByDescending(i => i.CreatedAt)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();

            var incidents = rawIncidents.Select(i =>
            {
                List<IncidentNoteDto> notesList = new();
                if (!string.IsNullOrWhiteSpace(i.NotesJson))
                {
                    try
                    {
                        notesList = JsonSerializer.Deserialize<List<IncidentNoteDto>>(i.NotesJson) ?? new();
                    }
                    catch { }
                }

                return new
                {
                    incidentId = $"INC-{i.Id:D4}",
                    id = i.Id,
                    createdAt = i.CreatedAt.ToString("o"),
                    category = i.Source ?? "DLP_VIOLATION",
                    severity = i.Severity,
                    riskScore = i.RiskScore,
                    actionTaken = i.ActionTaken,
                    status = i.Status,
                    description = i.Title,
                    assignedTo = i.Username ?? "Security SOC",
                    auditLogId = i.AuditLogId?.ToString(),
                    riskBreakdown = new
                    {
                        voiceRisk = i.VoiceRisk,
                        socialRisk = i.SocialRisk,
                        dlpRisk = i.DlpSensitivity
                    },
                    notes = notesList
                };
            }).ToList();

            return Ok(new
            {
                status = "success",
                data = new
                {
                    incidents,
                    total,
                    page,
                    limit
                }
            });
        }

        // PATCH /api/v1/incidents/{id}
        [HttpPatch("{id}")]
        public async Task<IActionResult> UpdateIncident(string id, [FromBody] UpdateIncidentRequest req)
        {
            var role = GetRole();
            if (!new[] { "Analyst", "Administrator" }.Contains(role))
                return StatusCode(403, new { status = "error", error = "Insufficient permissions" });

            int numericId = 0;
            if (id.StartsWith("INC-", StringComparison.OrdinalIgnoreCase))
            {
                int.TryParse(id.Substring(4), out numericId);
            }
            else
            {
                int.TryParse(id, out numericId);
            }

            var incident = await _db.Incidents.FindAsync(numericId);
            if (incident == null)
                return NotFound(new { status = "error", error = "Incident not found" });

            var validStatuses = new[] { "OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE" };
            if (!string.IsNullOrWhiteSpace(req.Status) && validStatuses.Contains(req.Status.ToUpper()))
            {
                incident.Status = req.Status.ToUpper();
                if (incident.Status == "RESOLVED") incident.ResolvedAt = DateTime.UtcNow;
            }

            if (!string.IsNullOrWhiteSpace(req.Note))
            {
                var notes = new List<IncidentNoteDto>();
                if (!string.IsNullOrWhiteSpace(incident.NotesJson))
                {
                    try { notes = JsonSerializer.Deserialize<List<IncidentNoteDto>>(incident.NotesJson) ?? new(); } catch { }
                }
                var username = User.FindFirst("username")?.Value ?? "Analyst";
                notes.Add(new IncidentNoteDto { Author = username, Note = req.Note, Timestamp = DateTime.UtcNow.ToString("o") });
                incident.NotesJson = JsonSerializer.Serialize(notes);
            }

            await _db.SaveChangesAsync();
            return Ok(new
            {
                status = "success",
                message = "Incident updated successfully",
                data = new
                {
                    incidentId = $"INC-{incident.Id:D4}",
                    incident.Status,
                    incident.ResolvedAt
                }
            });
        }
    }

    public class IncidentNoteDto
    {
        public string? Author { get; set; }
        public string? Note { get; set; }
        public string? Timestamp { get; set; }
    }

    public record UpdateIncidentRequest(string? Status, string? Note);
}
