using System.ComponentModel.DataAnnotations;

namespace EASP.Api.DTOs;

public class TokenizeRequest
{
    [Required]
    public string OriginalValue { get; set; } = string.Empty;

    [Required]
    public string TokenType { get; set; } = "GENERIC_PII";

    /// <summary>
    /// TTL Duration in minutes (defaults to 60 minutes)
    /// </summary>
    [Range(1, 43200, ErrorMessage = "TTL minutes must be between 1 minute and 30 days.")]
    public int TtlMinutes { get; set; } = 60;
}

public class TokenizeResponse
{
    public string Token { get; set; } = string.Empty;
    public string TokenType { get; set; } = string.Empty;
    public DateTime CreatedAtUtc { get; set; }
    public DateTime ExpiresAtUtc { get; set; }
    public int TtlMinutes { get; set; }
}

public class DetokenizeRequest
{
    [Required]
    public string Token { get; set; } = string.Empty;
}

public class DetokenizeResponse
{
    public string Token { get; set; } = string.Empty;
    public string OriginalValue { get; set; } = string.Empty;
    public string TokenType { get; set; } = string.Empty;
    public DateTime ExpiresAtUtc { get; set; }
    public bool IsExpired { get; set; }
}

public class RevokeTokenRequest
{
    [Required]
    public string Token { get; set; } = string.Empty;
}
