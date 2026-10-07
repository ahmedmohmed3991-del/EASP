using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using EASP.API.Models;
using EASP.API.Data;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
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

        public (string accessToken, string refreshToken, DateTime refreshTokenExpiresAt) GenerateTokens(User user)
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

            var refreshDays = _config.GetValue<double>("Jwt:RefreshExpiryDays", 7);
            if (!double.IsFinite(refreshDays) || refreshDays <= 0)
                throw new InvalidOperationException("Jwt:RefreshExpiryDays must be positive");

            return (new JwtSecurityTokenHandler().WriteToken(accessToken), refreshToken,
                DateTime.UtcNow.AddDays(refreshDays));
        }

        // Run after signature/lifetime validation, before authorization or restoration.
        public static async Task ValidateCurrentUserAsync(TokenValidatedContext context)
        {
            if (context.Principal?.Identity is not ClaimsIdentity identity ||
                !int.TryParse(context.Principal.FindFirst("userId")?.Value, out var userId) || userId <= 0)
            {
                context.Fail("Invalid user identity");
                return;
            }

            var db = context.HttpContext.RequestServices.GetRequiredService<AppDbContext>();
            var user = await db.Users.AsNoTracking().SingleOrDefaultAsync(u => u.Id == userId,
                context.HttpContext.RequestAborted);
            if (user == null || !user.IsActive)
            {
                context.Fail("User account is unavailable");
                return;
            }

            foreach (var claim in identity.Claims.Where(c =>
                c.Type == identity.RoleClaimType || c.Type == "username" || c.Type == ClaimTypes.Email).ToList())
                identity.RemoveClaim(claim);
            identity.AddClaim(new Claim(identity.RoleClaimType, user.Role));
            identity.AddClaim(new Claim("username", user.Username));
            identity.AddClaim(new Claim(ClaimTypes.Email, user.Email));
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
