namespace EASP.Api.Models;

/// <summary>
/// T-P05-031: Security Policy definition entity.
/// Replaces MongoDB policies collection.
/// </summary>
public class Policy
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Name { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Category: DLP, PROMPT_INJECTION, ACCESS_CONTROL, DATA_CLASSIFICATION
    /// </summary>
    public string Category { get; set; } = "DLP";

    /// <summary>
    /// Action: Block, Redact, Alert, Allow
    /// </summary>
    public string Action { get; set; } = "Redact";

    /// <summary>
    /// Severity: Critical, High, Medium, Low
    /// </summary>
    public string Severity { get; set; } = "Medium";

    public bool IsEnabled { get; set; } = true;

    /// <summary>
    /// JSON encoded parameters (e.g. thresholds, target entities, custom rules)
    /// </summary>
    public string ConfigurationJson { get; set; } = "{}";

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime? UpdatedAt { get; set; }

    public string? CreatedByUserId { get; set; }
}
