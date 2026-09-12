using Microsoft.AspNetCore.Mvc;

namespace EASP.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    [HttpGet]
    public IActionResult Get()
    {
        return Ok(new
        {
            status = "Healthy",
            service = "EASP.Api",
            timestamp = DateTime.UtcNow
        });
    }
}
