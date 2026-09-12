using System.Security.Claims;
using EASP.Api.DTOs;
using EASP.Api.Models;
using EASP.Api.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;

namespace EASP.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly UserManager<User> _userManager;
    private readonly RoleManager<Role> _roleManager;
    private readonly IJwtTokenService _tokenService;
    private readonly ILogger<AuthController> _logger;

    public AuthController(
        UserManager<User> userManager,
        RoleManager<Role> roleManager,
        IJwtTokenService tokenService,
        ILogger<AuthController> logger)
    {
        _userManager = userManager;
        _roleManager = roleManager;
        _tokenService = tokenService;
        _logger = logger;
    }

    /// <summary>
    /// Register a new user account and assign a role (default: Employee).
    /// </summary>
    [HttpPost("register")]
    [ProducesResponseType(typeof(AuthResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Register([FromBody] RegisterRequest request)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var existingUser = await _userManager.FindByEmailAsync(request.Email);
        if (existingUser != null)
        {
            return BadRequest(new { message = $"Email '{request.Email}' is already registered." });
        }

        // Validate role or assign default Employee
        var targetRole = string.IsNullOrWhiteSpace(request.Role) ? DefaultRoles.Employee : request.Role.Trim();
        var roleExists = await _roleManager.RoleExistsAsync(targetRole);
        if (!roleExists)
        {
            return BadRequest(new
            {
                message = $"Role '{targetRole}' is invalid. Allowed roles: {string.Join(", ", DefaultRoles.All)}"
            });
        }

        var user = new User
        {
            UserName = request.Email,
            Email = request.Email,
            FullName = request.FullName,
            CreatedAt = DateTime.UtcNow
        };

        var createResult = await _userManager.CreateAsync(user, request.Password);
        if (!createResult.Succeeded)
        {
            var errors = createResult.Errors.Select(e => e.Description);
            return BadRequest(new { message = "Registration failed.", errors });
        }

        var roleResult = await _userManager.AddToRoleAsync(user, targetRole);
        if (!roleResult.Succeeded)
        {
            _logger.LogWarning("Failed to assign role {Role} to user {Email}", targetRole, user.Email);
        }

        var roles = await _userManager.GetRolesAsync(user);
        var (token, expiresAt) = _tokenService.GenerateToken(user, roles);

        var response = new AuthResponse
        {
            Token = token,
            ExpiresAtUtc = expiresAt,
            User = new UserDto
            {
                Id = user.Id,
                Email = user.Email ?? string.Empty,
                FullName = user.FullName,
                Roles = roles
            }
        };

        _logger.LogInformation("New user registered successfully: {Email} with role {Role}", user.Email, targetRole);
        return StatusCode(StatusCodes.Status201Created, response);
    }

    /// <summary>
    /// Authenticate existing user and return JWT bearer token.
    /// </summary>
    [HttpPost("login")]
    [ProducesResponseType(typeof(AuthResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> Login([FromBody] LoginRequest request)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var user = await _userManager.FindByEmailAsync(request.Email);
        if (user == null)
        {
            return Unauthorized(new { message = "Invalid email or password." });
        }

        var isPasswordValid = await _userManager.CheckPasswordAsync(user, request.Password);
        if (!isPasswordValid)
        {
            return Unauthorized(new { message = "Invalid email or password." });
        }

        var roles = await _userManager.GetRolesAsync(user);
        var (token, expiresAt) = _tokenService.GenerateToken(user, roles);

        var response = new AuthResponse
        {
            Token = token,
            ExpiresAtUtc = expiresAt,
            User = new UserDto
            {
                Id = user.Id,
                Email = user.Email ?? string.Empty,
                FullName = user.FullName,
                Roles = roles
            }
        };

        _logger.LogInformation("User logged in successfully: {Email}", user.Email);
        return Ok(response);
    }

    /// <summary>
    /// Get authenticated user details using current JWT Bearer token.
    /// </summary>
    [Authorize]
    [HttpGet("me")]
    [ProducesResponseType(typeof(UserDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetCurrentUser()
    {
        var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (string.IsNullOrEmpty(userId))
        {
            return Unauthorized(new { message = "User identifier missing from token claims." });
        }

        var user = await _userManager.FindByIdAsync(userId);
        if (user == null)
        {
            return NotFound(new { message = "User account not found." });
        }

        var roles = await _userManager.GetRolesAsync(user);

        var response = new UserDto
        {
            Id = user.Id,
            Email = user.Email ?? string.Empty,
            FullName = user.FullName,
            Roles = roles
        };

        return Ok(response);
    }
}
