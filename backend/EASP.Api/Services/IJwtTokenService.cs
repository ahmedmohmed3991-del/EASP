using EASP.Api.Models;

namespace EASP.Api.Services;

public interface IJwtTokenService
{
    (string Token, DateTime ExpiresAtUtc) GenerateToken(User user, IList<string> roles);
}
