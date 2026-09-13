namespace EASP.Api.Models;

/// <summary>
/// T-P05-031: System-wide immutable Audit Log entity.
/// Replaces MongoDB auditLogs collection.
/// </summary>
public class AuditLog
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    public string? CorrelationId { get; set; }

    public string? UserId { get; set; }

    public string? UserEmail { get; set; }

    /// <summary>
    /// Event action: AUTH_REGISTER, AUTH_LOGIN, DLP_ANALYZE, TOKENIZE, POLICY_MUTATION, etc.
    /// </summary>
    public string Action { get; set; } = string.Empty;

    /// <summary>
    /// Resource path or entity: /api/auth/login, /api/dlp/analyze, etc.
    /// </summary>
    public string Resource { get; set; } = string.Empty;

    public string? IpAddress { get; set; }

    public int StatusCode { get; set; }

    public long ExecutionTimeMs { get; set; }

    /// <summary>
    /// Detailed JSON metadata associated with the event
    /// </summary>
    public string? DetailsJson { get; set; }
}
