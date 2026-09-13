using EASP.Api.DTOs;

namespace EASP.Api.Services;

public interface ITokenMappingService
{
    Task<TokenizeResponse> TokenizeAsync(TokenizeRequest request, string? userId = null, CancellationToken cancellationToken = default);
    Task<DetokenizeResponse?> DetokenizeAsync(string token, CancellationToken cancellationToken = default);
    Task<bool> RevokeAsync(string token, CancellationToken cancellationToken = default);
    Task<int> SweepExpiredTokensAsync(CancellationToken cancellationToken = default);
}
