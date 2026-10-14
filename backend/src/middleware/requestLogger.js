// EASP Request Logging Hook - Phase 2 (T-P02-017)
// Captures request metadata, client IP, path, method, and latency.
// Pre-cursor hook to the security audit logger, ensuring no plaintext credentials/secrets are logged.

function requestLogger(req, res, next) {
  const startTime = Date.now();
  const clientIp = req.ip || req.connection.remoteAddress || 'unknown';

  // Hook on response finish to calculate duration
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    // Redact sensitive authorization headers from debug output
    const authStatus = req.headers.authorization ? '[AUTHENTICATED]' : '[ANONYMOUS]';

    // Only log non-sensitive summaries
    if (process.env.NODE_ENV !== 'test') {
      console.log(
        `[REQ] ${new Date().toISOString()} | ${req.method} ${req.originalUrl || req.url} | Status: ${res.statusCode} | Duration: ${duration}ms | IP: ${clientIp} | ${authStatus}`
      );
    }
  });

  next();
}

module.exports = { requestLogger };
