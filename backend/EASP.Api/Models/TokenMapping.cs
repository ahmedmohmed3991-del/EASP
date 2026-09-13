namespace EASP.Api.Models;

/// <summary>
/// T-P04-027: Entity for storing surrogate token to original sensitive value mappings with TTL.
/// Replaces MongoDB tokenMappings collection with SQL Server EF Core entity.
/// </summary>
public class TokenMapping
{
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>
    /// Surrogate token (e.g. TOK_EMAIL_a8f9c2d1)
    /// </summary>
    public string Token { get; set; } = string.Empty;

    /// <summary>
    /// Original raw sensitive value (e.g. john.doe@company.com)
    /// </summary>
    public string OriginalValue { get; set; } = string.Empty;

    /// <summary>
    /// Entity classification (e.g. EMAIL_ADDRESS, CREDIT_CARD, PHONE_NUMBER)
    /// </summary>
    public string TokenType { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    /// <summary>
    /// TTL Expiration timestamp
    /// </summary>
    public DateTime ExpiresAt { get; set; }

    public bool IsRevoked { get; set; } = false;

    public string? CreatedByUserId { get; set; }
}
