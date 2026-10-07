using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using EASP.API.Data;
using EASP.API.Services;

namespace EASP.API.Controllers
{
    [ApiController]
    public class HealthController : ControllerBase
    {
        private readonly AppDbContext _db;
        private readonly AiServiceClient _ai;

        public HealthController(AppDbContext db, AiServiceClient ai)
        {
            _db = db;
            _ai = ai;
        }

        [HttpGet("health")]
        [HttpGet("api/v1/health")]
        public async Task<IActionResult> Health()
        {
            // Check SQL Server
            bool dbOk = false;
            string dbStatus = "disconnected";
            try
            {
                dbOk = await _db.Database.CanConnectAsync();
                dbStatus = dbOk ? "connected" : "disconnected";
            }
            catch { dbStatus = "error"; }

            return Ok(new
            {
                status = "ok",
                service = "easp-backend-dotnet",
                phase = "phase-0",
                timestamp = DateTime.UtcNow.ToString("o"),
                dependencies = new
                {
                    mongodb = new // keep name mongodb/database for frontend backwards compatibility
                    {
                        state = dbStatus,
                        connected = dbOk,
                        engine = "SQL Server"
                    },
                    sqlserver = new
                    {
                        state = dbStatus,
                        connected = dbOk
                    }
                }
            });
        }

        [HttpGet("health/ai")]
        [HttpGet("api/v1/health/ai")]
        public async Task<IActionResult> HealthAi()
        {
            var startedAt = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            try
            {
                var http = new HttpClient { BaseAddress = new Uri("http://localhost:8000"), Timeout = TimeSpan.FromSeconds(3) };
                var resp = await http.GetAsync("/health");
                var elapsed = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() - startedAt;

                if (resp.IsSuccessStatusCode)
                {
                    var content = await resp.Content.ReadAsStringAsync();
                    return Ok(new
                    {
                        status = "ok",
                        service = "easp-backend-dotnet",
                        ai_service = new
                        {
                            reachable = true,
                            url = "http://localhost:8000",
                            response_time_ms = elapsed,
                            data = content
                        }
                    });
                }
                else
                {
                    return StatusCode(503, new
                    {
                        status = "degraded",
                        service = "easp-backend-dotnet",
                        ai_service = new
                        {
                            reachable = false,
                            url = "http://localhost:8000",
                            error = $"HTTP {resp.StatusCode}"
                        }
                    });
                }
            }
            catch (Exception ex)
            {
                return StatusCode(503, new
                {
                    status = "degraded",
                    service = "easp-backend-dotnet",
                    ai_service = new
                    {
                        reachable = false,
                        url = "http://localhost:8000",
                        error = ex.Message
                    }
                });
            }
        }
    }
}
