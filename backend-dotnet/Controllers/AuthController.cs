using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using EASP.API.Data;
using EASP.API.Models;
using EASP.API.Services;
using BCrypt.Net;
using System.Text.Json;

namespace EASP.API.Controllers
{
    [ApiController]
    [Route("api/v1/auth")]
    public class AuthController : ControllerBase
    {
        private readonly AppDbContext _db;
        private readonly JwtService _jwt;
        private readonly AuditService _audit;

        public AuthController(AppDbContext db, JwtService jwt, AuditService audit)
        {
            _db = db;
            _jwt = jwt;
            _audit = audit;
        }

        // POST /api/v1/auth/register
        [HttpPost("register")]
        public async Task<IActionResult> Register([FromBody] RegisterRequest req)
        {
            if (string.IsNullOrWhiteSpace(req.Username) || string.IsNullOrWhiteSpace(req.Email) || string.IsNullOrWhiteSpace(req.Password))
                return BadRequest(new { status = "error", error = "username, email, and password are required" });

            if (req.Password.Length < 8)
                return BadRequest(new { status = "error", error = "password must be at least 8 characters long" });

            var exists = await _db.Users.AnyAsync(u => u.Email == req.Email.ToLower() || u.Username == req.Username);
            if (exists)
                return Conflict(new { status = "error", error = "A user with this email or username already exists" });

            // Public registration must never grant privileged roles.
            var role = "Employee";

            var user = new User
            {
                Username = req.Username,
                Email = req.Email.ToLower(),
                PasswordHash = BCrypt.Net.BCrypt.HashPassword(req.Password, workFactor: 12),
                Role = role,
                LastLoginAt = DateTime.UtcNow
            };

            _db.Users.Add(user);
            await _db.SaveChangesAsync();

            // SQL assigns the user ID before it can be included in a valid JWT.
            var (accessToken, refreshToken, refreshTokenExpiresAt) = _jwt.GenerateTokens(user);
            user.RefreshToken = refreshToken;
            user.RefreshTokenExpiresAt = refreshTokenExpiresAt;
            await _db.SaveChangesAsync();

            await _audit.LogEventAsync("AUTH_REGISTER", "INFO", user.Id, user.Username, user.Role,
                HttpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown", 0.0, "N/A",
                JsonSerializer.Serialize(new { userId = user.Id, email = user.Email }));

            return StatusCode(201, new
            {
                status = "success",
                message = "User registered successfully",
                user = new { user.Id, user.Username, user.Email, user.Role, user.IsActive, user.CreatedAt },
                token = accessToken,
                refreshToken
            });
        }

        // POST /api/v1/auth/login
        [HttpPost("login")]
        public async Task<IActionResult> Login([FromBody] LoginRequest req)
        {
            if (string.IsNullOrWhiteSpace(req.Email) || string.IsNullOrWhiteSpace(req.Password))
                return BadRequest(new { status = "error", error = "Email and password are required" });

            var user = await _db.Users.FirstOrDefaultAsync(u => u.Email == req.Email.ToLower());
            if (user == null || !user.IsActive)
                return Unauthorized(new { status = "error", error = "Invalid email or password" });

            if (!BCrypt.Net.BCrypt.Verify(req.Password, user.PasswordHash))
            {
                await _audit.LogEventAsync("AUTH_FAILURE", "ALERT", user.Id, user.Username, user.Role,
                    HttpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown", 0.5, "MEDIUM",
                    JsonSerializer.Serialize(new { email = req.Email, outcome = "FAILED_PASSWORD" }));
                return Unauthorized(new { status = "error", error = "Invalid email or password" });
            }

            var (accessToken, refreshToken, refreshTokenExpiresAt) = _jwt.GenerateTokens(user);
            user.RefreshToken = refreshToken;
            user.RefreshTokenExpiresAt = refreshTokenExpiresAt;
            user.LastLoginAt = DateTime.UtcNow;
            await _db.SaveChangesAsync();

            await _audit.LogEventAsync("AUTH_LOGIN", "INFO", user.Id, user.Username, user.Role,
                HttpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown", 0.0, "N/A",
                JsonSerializer.Serialize(new { userId = user.Id, email = user.Email }));

            return Ok(new
            {
                status = "success",
                message = "Authentication successful",
                user = new { user.Id, user.Username, user.Email, user.Role, user.IsActive, user.LastLoginAt, user.CreatedAt },
                token = accessToken,
                refreshToken
            });
        }

        // GET /api/v1/auth/me
        [HttpGet("me")]
        [Authorize]
        public async Task<IActionResult> GetMe()
        {
            var userId = int.Parse(User.FindFirst("userId")!.Value);
            var user = await _db.Users.FindAsync(userId);
            if (user == null) return NotFound(new { status = "error", error = "User not found" });

            return Ok(new
            {
                status = "success",
                user = new { user.Id, user.Username, user.Email, user.Role, user.IsActive, user.LastLoginAt, user.CreatedAt }
            });
        }

        // POST /api/v1/auth/refresh
        [HttpPost("refresh")]
        public async Task<IActionResult> Refresh([FromBody] RefreshRequest req)
        {
            if (string.IsNullOrWhiteSpace(req.RefreshToken))
                return BadRequest(new { status = "error", error = "Refresh token is required" });

            var user = await _db.Users.FirstOrDefaultAsync(u => u.RefreshToken == req.RefreshToken);
            if (user == null || !user.IsActive ||
                !string.Equals(user.RefreshToken, req.RefreshToken, StringComparison.Ordinal) ||
                user.RefreshTokenExpiresAt == null || user.RefreshTokenExpiresAt <= DateTime.UtcNow)
                return Unauthorized(new { status = "error", error = "Revoked or invalid session" });

            var (accessToken, newRefreshToken, refreshTokenExpiresAt) = _jwt.GenerateTokens(user);
            user.RefreshToken = newRefreshToken;
            user.RefreshTokenExpiresAt = refreshTokenExpiresAt;
            await _db.SaveChangesAsync();

            return Ok(new { status = "success", token = accessToken, refreshToken = newRefreshToken });
        }
    }

    public record RegisterRequest(string Username, string Email, string Password, string Role = "Employee");
    public record LoginRequest(string Email, string Password);
    public record RefreshRequest(string RefreshToken);
}
