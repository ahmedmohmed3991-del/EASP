using System.ComponentModel.DataAnnotations;

namespace EASP.Api.DTOs;

public class CreatePolicyRequest
{
    [Required]
    public string Name { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    [Required]
    public string Category { get; set; } = "DLP";

    [Required]
    public string Action { get; set; } = "Redact"; // Block, Redact, Alert, Allow

    public string Severity { get; set; } = "Medium"; // Critical, High, Medium, Low

    public bool IsEnabled { get; set; } = true;

    public string ConfigurationJson { get; set; } = "{}";
}

public class UpdatePolicyRequest
{
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? Category { get; set; }
    public string? Action { get; set; }
    public string? Severity { get; set; }
    public bool? IsEnabled { get; set; }
    public string? ConfigurationJson { get; set; }
}

public class PolicyDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string Severity { get; set; } = string.Empty;
    public bool IsEnabled { get; set; }
    public string ConfigurationJson { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public string? CreatedByUserId { get; set; }
}
