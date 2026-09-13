using System.Security.Claims;
using EASP.Api.DTOs;
using EASP.Api.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace EASP.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/[controller]")]
public class TokensController : ControllerBase
{
    private readonly ITokenMappingService _tokenService;
    private readonly ILogger<TokensController> _logger;

    public TokensController(ITokenMappingService tokenService, ILogger<TokensController> logger)
    {
        _tokenService = tokenService;
        _logger = logger;
    }

    /// <summary>
    /// Generate a surrogate token for sensitive data with a TTL expiration.
    /// </summary>
    [HttpPost("tokenize")]
    [ProducesResponseType(typeof(TokenizeResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Tokenize([FromBody] TokenizeRequest request, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
        var result = await _tokenService.TokenizeAsync(request, userId, cancellationToken);
        return StatusCode(StatusCodes.Status201Created, result);
    }

    /// <summary>
    /// Resolve a surrogate token back to its original sensitive value (if not expired/revoked).
    /// </summary>
    [HttpPost("detokenize")]
    [ProducesResponseType(typeof(DetokenizeResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Detokenize([FromBody] DetokenizeRequest request, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var result = await _tokenService.DetokenizeAsync(request.Token, cancellationToken);
        if (result == null)
        {
            return NotFound(new { message = $"Token '{request.Token}' was not found or has expired." });
        }

        return Ok(result);
    }

    /// <summary>
    /// Revoke a surrogate token immediately before its TTL expiration.
    /// </summary>
    [HttpPost("revoke")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Revoke([FromBody] RevokeTokenRequest request, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var success = await _tokenService.RevokeAsync(request.Token, cancellationToken);
        if (!success)
        {
            return NotFound(new { message = $"Token '{request.Token}' was not found." });
        }

        return Ok(new { message = $"Token '{request.Token}' has been revoked successfully." });
    }

    /// <summary>
    /// Trigger an immediate manual TTL cleanup sweep for expired tokens.
    /// </summary>
    [HttpPost("sweep")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public async Task<IActionResult> TriggerSweep(CancellationToken cancellationToken)
    {
        var count = await _tokenService.SweepExpiredTokensAsync(cancellationToken);
        return Ok(new { message = $"TTL Sweep completed.", purgedTokensCount = count });
    }
}
