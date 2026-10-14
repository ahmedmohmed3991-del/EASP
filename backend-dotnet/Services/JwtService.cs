using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using EASP.API.Models;
using Microsoft.IdentityModel.Tokens;

namespace EASP.API.Services
{
    public class JwtService
    {
        private readonly IConfiguration _config;

        public JwtService(IConfiguration config)
        {
            _config = config;
        }

        public (string accessToken, string refreshToken) GenerateTokens(User user)
        {
            var secret = _config["Jwt:Secret"] ?? throw new InvalidOperationException("JWT secret not configured");
            var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secret));
            var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

            var claims = new[]
            {
                new Claim("userId", user.Id.ToString()),
                new Claim("username", user.Username),
                new Claim(ClaimTypes.Email, user.Email),
                new Claim(ClaimTypes.Role, user.Role)
            };

            var accessExpiry = double.Parse(_config["Jwt:AccessExpiryMinutes"] ?? "60");
            var accessToken = new JwtSecurityToken(
                claims: claims,
                expires: DateTime.UtcNow.AddMinutes(accessExpiry),
                signingCredentials: creds
            );

            // Refresh token is a random 64-byte hex string (stored in DB)
            var refreshToken = Convert.ToHexString(RandomNumberGenerator.GetBytes(64));

            return (new JwtSecurityTokenHandler().WriteToken(accessToken), refreshToken);
        }

        public ClaimsPrincipal? ValidateToken(string token)
        {
            try
            {
                var secret = _config["Jwt:Secret"]!;
                var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secret));
                var handler = new JwtSecurityTokenHandler();
                var principal = handler.ValidateToken(token, new TokenValidationParameters
                {
                    ValidateIssuerSigningKey = true,
                    IssuerSigningKey = key,
                    ValidateIssuer = false,
                    ValidateAudience = false,
                    ClockSkew = TimeSpan.Zero
                }, out _);
                return principal;
            }
            catch
            {
                return null;
            }
        }
    }
}
