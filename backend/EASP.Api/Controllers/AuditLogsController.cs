using EASP.Api.Data;
using EASP.Api.DTOs;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EASP.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/[controller]")]
public class AuditLogsController : ControllerBase
{
    private readonly AppDbContext _db;

    public AuditLogsController(AppDbContext db)
    {
        _db = db;
    }

    /// <summary>
    /// Query audit logs with optional filters and pagination.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(PagedResult<AuditLogDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll([FromQuery] AuditLogQueryParams query, CancellationToken ct)
    {
        var q = _db.AuditLogs.AsNoTracking().AsQueryable();

        if (!string.IsNullOrWhiteSpace(query.UserId))
            q = q.Where(a => a.UserId == query.UserId);

        if (!string.IsNullOrWhiteSpace(query.Action))
            q = q.Where(a => a.Action == query.Action);

        if (query.From.HasValue)
            q = q.Where(a => a.Timestamp >= query.From.Value);

        if (query.To.HasValue)
            q = q.Where(a => a.Timestamp <= query.To.Value);

        var totalCount = await q.CountAsync(ct);

        var page = Math.Max(1, query.Page);
        var pageSize = Math.Clamp(query.PageSize, 1, 200);

        var items = await q
            .OrderByDescending(a => a.Timestamp)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(a => new AuditLogDto
            {
                Id = a.Id,
                Timestamp = a.Timestamp,
                CorrelationId = a.CorrelationId,
                UserId = a.UserId,
                UserEmail = a.UserEmail,
                Action = a.Action,
                Resource = a.Resource,
                IpAddress = a.IpAddress,
                StatusCode = a.StatusCode,
                ExecutionTimeMs = a.ExecutionTimeMs,
                DetailsJson = a.DetailsJson
            })
            .ToListAsync(ct);

        return Ok(new PagedResult<AuditLogDto>
        {
            Items = items,
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize
        });
    }

    /// <summary>
    /// Get a single audit log entry by ID.
    /// </summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(AuditLogDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(Guid id, CancellationToken ct)
    {
        var entry = await _db.AuditLogs.AsNoTracking().FirstOrDefaultAsync(a => a.Id == id, ct);
        if (entry == null) return NotFound(new { message = $"AuditLog entry {id} not found." });

        return Ok(new AuditLogDto
        {
            Id = entry.Id,
            Timestamp = entry.Timestamp,
            CorrelationId = entry.CorrelationId,
            UserId = entry.UserId,
            UserEmail = entry.UserEmail,
            Action = entry.Action,
            Resource = entry.Resource,
            IpAddress = entry.IpAddress,
            StatusCode = entry.StatusCode,
            ExecutionTimeMs = entry.ExecutionTimeMs,
            DetailsJson = entry.DetailsJson
        });
    }
}
