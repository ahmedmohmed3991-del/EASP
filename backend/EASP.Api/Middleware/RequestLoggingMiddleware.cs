using System.Diagnostics;

namespace EASP.Api.Middleware;

/// <summary>
/// T-P02-017: Request-logging hook
/// Captures HTTP request metadata, measures execution latency (in ms),
/// and outputs structured audit/diagnostic logs.
/// </summary>
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var correlationId = context.Request.Headers["X-Correlation-ID"].FirstOrDefault()
                            ?? Guid.NewGuid().ToString();

        var stopwatch = Stopwatch.StartNew();
        var request = context.Request;
        var method = request.Method;
        var path = request.Path;
        var queryString = request.QueryString.HasValue ? request.QueryString.Value : string.Empty;
        var ipAddress = context.Connection.RemoteIpAddress?.ToString() ?? "unknown";

        _logger.LogInformation(
            "[{CorrelationId}] HTTP Incoming: {Method} {Path}{Query} from IP {IP}",
            correlationId, method, path, queryString, ipAddress);

        // Register header injection right before response starts streaming
        context.Response.OnStarting(() =>
        {
            context.Response.Headers["X-Correlation-ID"] = correlationId;
            context.Response.Headers["X-Response-Time-Ms"] = stopwatch.ElapsedMilliseconds.ToString();
            return Task.CompletedTask;
        });

        try
        {
            await _next(context);
        }
        finally
        {
            stopwatch.Stop();
            var elapsedMs = stopwatch.ElapsedMilliseconds;
            var statusCode = context.Response.StatusCode;

            if (statusCode >= 500)
            {
                _logger.LogError(
                    "[{CorrelationId}] HTTP Completed: {Method} {Path} -> {StatusCode} in {ElapsedMs}ms",
                    correlationId, method, path, statusCode, elapsedMs);
            }
            else if (statusCode >= 400)
            {
                _logger.LogWarning(
                    "[{CorrelationId}] HTTP Completed: {Method} {Path} -> {StatusCode} in {ElapsedMs}ms",
                    correlationId, method, path, statusCode, elapsedMs);
            }
            else
            {
                _logger.LogInformation(
                    "[{CorrelationId}] HTTP Completed: {Method} {Path} -> {StatusCode} in {ElapsedMs}ms",
                    correlationId, method, path, statusCode, elapsedMs);
            }
        }
    }
}
