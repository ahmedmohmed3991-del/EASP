using EASP.Api.DTOs;
using EASP.Api.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace EASP.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/[controller]")]
public class DlpController : ControllerBase
{
    private readonly IDlpClient _dlpClient;
    private readonly ILogger<DlpController> _logger;

    public DlpController(IDlpClient dlpClient, ILogger<DlpController> logger)
    {
        _dlpClient = dlpClient;
        _logger = logger;
    }

    /// <summary>
    /// Analyze text for sensitive PII and confidential information.
    /// </summary>
    [HttpPost("analyze")]
    [ProducesResponseType(typeof(DlpAnalyzeResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Analyze([FromBody] DlpAnalyzeRequest request, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var result = await _dlpClient.AnalyzeAsync(request, cancellationToken);
        return Ok(result);
    }

    /// <summary>
    /// Anonymize sensitive PII inside the provided text.
    /// </summary>
    [HttpPost("anonymize")]
    [ProducesResponseType(typeof(DlpAnonymizeResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Anonymize([FromBody] DlpAnonymizeRequest request, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var result = await _dlpClient.AnonymizeAsync(request, cancellationToken);
        return Ok(result);
    }
}
