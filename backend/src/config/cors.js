const env = require('./env');

/**
 * Parses ALLOWED_ORIGINS string into a sanitized array of valid origin strings.
 * Handles comma separation, whitespace trimming, filtering empty entries,
 * and normalizing trailing slashes.
 * 
 * @param {string} originsString 
 * @returns {string[]}
 */
function parseAllowedOrigins(originsString) {
  if (!originsString || typeof originsString !== 'string') {
    return [];
  }
  return originsString
    .split(',')
    .map(origin => origin.trim().replace(/\/+$/, ''))
    .filter(Boolean);
}

const allowedOrigins = parseAllowedOrigins(env.ALLOWED_ORIGINS);

/**
 * CORS options configuration
 * - Validates incoming request Origin against configured allow-list
 * - Allows non-browser requests (no Origin header, e.g. curl, server-to-server, Postman)
 * - Avoids insecure wildcard origins when credentials are enabled
 * - Rejects unauthorized origins with HTTP 403 status
 */
const corsOptions = {
  origin: (origin, callback) => {
    // Non-browser or same-origin requests (e.g., mobile apps, curl, server-to-server)
    if (!origin) {
      return callback(null, true);
    }

    const normalizedOrigin = origin.replace(/\/+$/, '');

    if (allowedOrigins.includes(normalizedOrigin)) {
      return callback(null, true);
    }

    const corsError = new Error(`CORS policy violation: Origin '${origin}' is not in the allowed origins list.`);
    corsError.status = 403;
    corsError.statusCode = 403;
    return callback(corsError);
  },
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'Accept',
    'Origin'
  ],
  exposedHeaders: [
    'Content-Length',
    'Content-Range',
    'X-Content-Range'
  ],
  credentials: true,
  maxAge: 86400, // 24 hours preflight cache
  optionsSuccessStatus: 204
};

module.exports = {
  corsOptions,
  parseAllowedOrigins,
  allowedOrigins
};
