// EASP Rate Limiting Middleware - Phase 2 (T-P02-013)
// Enforces separate rate limits for sensitive routes (auth, token restore) and general API routes.

const rateLimit = require('express-rate-limit');
const env = require('../config/env');

// Strict limiter for authentication endpoints to mitigate credential stuffing and brute-force
const authLimiter = rateLimit({
  windowMs: env.RATE_LIMIT_WINDOW_MS,
  max: env.RATE_LIMIT_MAX_AUTH, // e.g. 10 requests per 15 min
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    status: 'error',
    statusCode: 429,
    error: 'Too many authentication attempts from this IP. Please try again after 15 minutes.'
  }
});

// General limiter for standard API routes
const apiLimiter = rateLimit({
  windowMs: env.RATE_LIMIT_WINDOW_MS,
  max: env.RATE_LIMIT_MAX_GENERAL, // e.g. 200 requests per 15 min
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    status: 'error',
    statusCode: 429,
    error: 'API rate limit exceeded. Please throttle your requests.'
  }
});

module.exports = { authLimiter, apiLimiter };
