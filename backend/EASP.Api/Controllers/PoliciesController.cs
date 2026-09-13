using System.Security.Claims;
using EASP.Api.Data;
using EASP.Api.DTOs;
using EASP.Api.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace EASP.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/[controller]")]
public class PoliciesController : ControllerBase
{
    private readonly AppDbContext _db;
    private readonly ILogger<PoliciesController> _logger;

    public PoliciesController(AppDbContext db, ILogger<PoliciesController> logger)
    {
        _db = db;
        _logger = logger;
    }

    /// <summary>
    /// List all security policies, optionally filtered by category or enabled status.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(List<PolicyDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll([FromQuery] string? category, [FromQuery] bool? enabled, CancellationToken ct)
    {
        var query = _db.Policies.AsNoTracking().AsQueryable();

        if (!string.IsNullOrWhiteSpace(category))
            query = query.Where(p => p.Category == category);

        if (enabled.HasValue)
            query = query.Where(p => p.IsEnabled == enabled.Value);

        var policies = await query.OrderByDescending(p => p.CreatedAt)
            .Select(p => new PolicyDto
            {
                Id = p.Id,
                Name = p.Name,
                Description = p.Description,
                Category = p.Category,
                Action = p.Action,
                Severity = p.Severity,
                IsEnabled = p.IsEnabled,
                ConfigurationJson = p.ConfigurationJson,
                CreatedAt = p.CreatedAt,
                UpdatedAt = p.UpdatedAt,
                CreatedByUserId = p.CreatedByUserId
            }).ToListAsync(ct);

        return Ok(policies);
    }

    /// <summary>
    /// Get a single policy by ID.
    /// </summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(PolicyDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(Guid id, CancellationToken ct)
    {
        var p = await _db.Policies.AsNoTracking().FirstOrDefaultAsync(x => x.Id == id, ct);
        if (p == null) return NotFound(new { message = $"Policy {id} not found." });

        return Ok(new PolicyDto
        {
            Id = p.Id, Name = p.Name, Description = p.Description,
            Category = p.Category, Action = p.Action, Severity = p.Severity,
            IsEnabled = p.IsEnabled, ConfigurationJson = p.ConfigurationJson,
            CreatedAt = p.CreatedAt, UpdatedAt = p.UpdatedAt, CreatedByUserId = p.CreatedByUserId
        });
    }

    /// <summary>
    /// Create a new security policy.
    /// </summary>
    [HttpPost]
    [ProducesResponseType(typeof(PolicyDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Create([FromBody] CreatePolicyRequest request, CancellationToken ct)
    {
        if (!ModelState.IsValid) return BadRequest(ModelState);

        var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);

        var policy = new Policy
        {
            Name = request.Name,
            Description = request.Description,
            Category = request.Category,
            Action = request.Action,
            Severity = request.Severity,
            IsEnabled = request.IsEnabled,
            ConfigurationJson = request.ConfigurationJson,
            CreatedByUserId = userId
        };

        _db.Policies.Add(policy);
        await _db.SaveChangesAsync(ct);

        _logger.LogInformation("Policy created: {Name} [{Category}] by {User}", policy.Name, policy.Category, userId);

        return StatusCode(StatusCodes.Status201Created, new PolicyDto
        {
            Id = policy.Id, Name = policy.Name, Description = policy.Description,
            Category = policy.Category, Action = policy.Action, Severity = policy.Severity,
            IsEnabled = policy.IsEnabled, ConfigurationJson = policy.ConfigurationJson,
            CreatedAt = policy.CreatedAt, CreatedByUserId = policy.CreatedByUserId
        });
    }

    /// <summary>
    /// Update an existing policy (partial update).
    /// </summary>
    [HttpPut("{id:guid}")]
    [ProducesResponseType(typeof(PolicyDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Update(Guid id, [FromBody] UpdatePolicyRequest request, CancellationToken ct)
    {
        var policy = await _db.Policies.FirstOrDefaultAsync(p => p.Id == id, ct);
        if (policy == null) return NotFound(new { message = $"Policy {id} not found." });

        if (request.Name != null) policy.Name = request.Name;
        if (request.Description != null) policy.Description = request.Description;
        if (request.Category != null) policy.Category = request.Category;
        if (request.Action != null) policy.Action = request.Action;
        if (request.Severity != null) policy.Severity = request.Severity;
        if (request.IsEnabled.HasValue) policy.IsEnabled = request.IsEnabled.Value;
        if (request.ConfigurationJson != null) policy.ConfigurationJson = request.ConfigurationJson;
        policy.UpdatedAt = DateTime.UtcNow;

        await _db.SaveChangesAsync(ct);
        _logger.LogInformation("Policy updated: {Id} {Name}", policy.Id, policy.Name);

        return Ok(new PolicyDto
        {
            Id = policy.Id, Name = policy.Name, Description = policy.Description,
            Category = policy.Category, Action = policy.Action, Severity = policy.Severity,
            IsEnabled = policy.IsEnabled, ConfigurationJson = policy.ConfigurationJson,
            CreatedAt = policy.CreatedAt, UpdatedAt = policy.UpdatedAt, CreatedByUserId = policy.CreatedByUserId
        });
    }

    /// <summary>
    /// Delete a policy.
    /// </summary>
    [HttpDelete("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(Guid id, CancellationToken ct)
    {
        var policy = await _db.Policies.FirstOrDefaultAsync(p => p.Id == id, ct);
        if (policy == null) return NotFound(new { message = $"Policy {id} not found." });

        _db.Policies.Remove(policy);
        await _db.SaveChangesAsync(ct);
        _logger.LogInformation("Policy deleted: {Id} {Name}", id, policy.Name);

        return Ok(new { message = $"Policy '{policy.Name}' deleted." });
    }
}
