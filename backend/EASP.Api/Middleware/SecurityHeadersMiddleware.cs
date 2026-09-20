namespace EASP.Api.Middleware;

/// <summary>
/// T-P02-014: Enterprise HTTP Security Headers Middleware.
/// .NET equivalent of Helmet security suite.
/// Enforces defense-in-depth protection against XSS, clickjacking, MIME sniffing,
/// and cross-origin resource leakage.
/// </summary>
public class SecurityHeadersMiddleware
{
    private readonly RequestDelegate _next;

    public SecurityHeadersMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // Attach security headers before the response starts sending
        context.Response.OnStarting(() =>
        {
            var headers = context.Response.Headers;

            // 1. Prevent MIME-sniffing
            if (!headers.ContainsKey("X-Content-Type-Options"))
            {
                headers["X-Content-Type-Options"] = "nosniff";
            }

            // 2. Prevent clickjacking (SAMEORIGIN)
            if (!headers.ContainsKey("X-Frame-Options"))
            {
                headers["X-Frame-Options"] = "SAMEORIGIN";
            }

            // 3. Referrer Policy
            if (!headers.ContainsKey("Referrer-Policy"))
            {
                headers["Referrer-Policy"] = "no-referrer";
            }

            // 4. Cross-Origin Policies
            if (!headers.ContainsKey("Cross-Origin-Opener-Policy"))
            {
                headers["Cross-Origin-Opener-Policy"] = "same-origin";
            }

            if (!headers.ContainsKey("Cross-Origin-Resource-Policy"))
            {
                headers["Cross-Origin-Resource-Policy"] = "cross-origin";
            }

            // 5. Content Security Policy (API baseline)
            if (!headers.ContainsKey("Content-Security-Policy"))
            {
                headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'self';";
            }

            // 6. X-Permitted-Cross-Domain-Policies
            if (!headers.ContainsKey("X-Permitted-Cross-Domain-Policies"))
            {
                headers["X-Permitted-Cross-Domain-Policies"] = "none";
            }

            // 7. Remove server fingerprinting
            headers.Remove("Server");
            headers.Remove("X-Powered-By");

            return Task.CompletedTask;
        });

        await _next(context);
    }
}
