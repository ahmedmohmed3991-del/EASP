using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using EASP.Api.Models;
using Microsoft.IdentityModel.Tokens;

namespace EASP.Api.Services;

public class JwtTokenService : IJwtTokenService
{
    private readonly IConfiguration _configuration;

    public JwtTokenService(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    public (string Token, DateTime ExpiresAtUtc) GenerateToken(User user, IList<string> roles)
    {
        var secretKey = _configuration["Jwt:Key"] ?? "EASP_Default_Secret_Key_For_Jwt_Authentication_Must_Be_Long_Enough_2026!";
        var issuer = _configuration["Jwt:Issuer"] ?? "EASP";
        var audience = _configuration["Jwt:Audience"] ?? "EASP-Client";

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, user.Id),
            new(ClaimTypes.Email, user.Email ?? string.Empty),
            new(ClaimTypes.Name, user.UserName ?? string.Empty),
            new("fullName", user.FullName ?? string.Empty),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())
        };

        foreach (var role in roles)
        {
            claims.Add(new Claim(ClaimTypes.Role, role));
        }

        var expiresAtUtc = DateTime.UtcNow.AddHours(8);

        var token = new JwtSecurityToken(
            issuer: issuer,
            audience: audience,
            claims: claims,
            notBefore: DateTime.UtcNow,
            expires: expiresAtUtc,
            signingCredentials: creds
        );

        var tokenString = new JwtSecurityTokenHandler().WriteToken(token);
        return (tokenString, expiresAtUtc);
    }
}
