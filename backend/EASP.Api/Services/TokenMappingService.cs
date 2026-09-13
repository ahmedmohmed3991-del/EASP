using System.Security.Cryptography;
using EASP.Api.Data;
using EASP.Api.DTOs;
using EASP.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace EASP.Api.Services;

public class TokenMappingService : ITokenMappingService
{
    private readonly AppDbContext _dbContext;
    private readonly ILogger<TokenMappingService> _logger;

    public TokenMappingService(AppDbContext dbContext, ILogger<TokenMappingService> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<TokenizeResponse> TokenizeAsync(TokenizeRequest request, string? userId = null, CancellationToken cancellationToken = default)
    {
        var randomHex = Convert.ToHexString(RandomNumberGenerator.GetBytes(6)).ToLowerInvariant();
        var prefix = string.IsNullOrWhiteSpace(request.TokenType) ? "PII" : request.TokenType.Trim().ToUpperInvariant();
        var surrogateToken = $"TOK_{prefix}_{randomHex}";

        var createdAt = DateTime.UtcNow;
        var expiresAt = createdAt.AddMinutes(request.TtlMinutes);

        var mapping = new TokenMapping
        {
            Token = surrogateToken,
            OriginalValue = request.OriginalValue,
            TokenType = request.TokenType,
            CreatedAt = createdAt,
            ExpiresAt = expiresAt,
            IsRevoked = false,
            CreatedByUserId = userId
        };

        _dbContext.TokenMappings.Add(mapping);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Generated surrogate token {Token} for type {Type} with TTL {TTL}m", surrogateToken, request.TokenType, request.TtlMinutes);

        return new TokenizeResponse
        {
            Token = surrogateToken,
            TokenType = request.TokenType,
            CreatedAtUtc = createdAt,
            ExpiresAtUtc = expiresAt,
            TtlMinutes = request.TtlMinutes
        };
    }

    public async Task<DetokenizeResponse?> DetokenizeAsync(string token, CancellationToken cancellationToken = default)
    {
        var mapping = await _dbContext.TokenMappings
            .AsNoTracking()
            .FirstOrDefaultAsync(m => m.Token == token, cancellationToken);

        if (mapping == null)
        {
            return null;
        }

        var isExpired = mapping.ExpiresAt <= DateTime.UtcNow || mapping.IsRevoked;

        return new DetokenizeResponse
        {
            Token = mapping.Token,
            OriginalValue = isExpired ? "[EXPIRED_OR_REVOKED]" : mapping.OriginalValue,
            TokenType = mapping.TokenType,
            ExpiresAtUtc = mapping.ExpiresAt,
            IsExpired = isExpired
        };
    }

    public async Task<bool> RevokeAsync(string token, CancellationToken cancellationToken = default)
    {
        var mapping = await _dbContext.TokenMappings
            .FirstOrDefaultAsync(m => m.Token == token, cancellationToken);

        if (mapping == null)
        {
            return false;
        }

        mapping.IsRevoked = true;
        await _dbContext.SaveChangesAsync(cancellationToken);
        _logger.LogInformation("Revoked token mapping {Token}", token);
        return true;
    }

    public async Task<int> SweepExpiredTokensAsync(CancellationToken cancellationToken = default)
    {
        var now = DateTime.UtcNow;
        var expiredRecords = await _dbContext.TokenMappings
            .Where(m => m.ExpiresAt <= now || m.IsRevoked)
            .ToListAsync(cancellationToken);

        if (expiredRecords.Count > 0)
        {
            _dbContext.TokenMappings.RemoveRange(expiredRecords);
            await _dbContext.SaveChangesAsync(cancellationToken);
            _logger.LogInformation("TTL Sweep: purged {Count} expired/revoked token mappings from database", expiredRecords.Count);
        }

        return expiredRecords.Count;
    }
}
