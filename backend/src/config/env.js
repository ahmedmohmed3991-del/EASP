// Centralized environment variable loader for the EASP backend.
// Supports Authentication, Encryption, Rate Limiting, and Service Endpoints.

require('dotenv').config();

const env = {
  PORT: parseInt(process.env.PORT, 10) || 5000,
  MONGO_URI: process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/easp',
  AI_SERVICE_URL: process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000',
  NODE_ENV: process.env.NODE_ENV || 'development',
  ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS || process.env.CORS_ALLOWED_ORIGINS || 'http://localhost:5173,http://localhost:3000',

  // Authentication & JWT (Phase 1)
  JWT_SECRET: process.env.JWT_SECRET || 'easp_dev_jwt_access_secret_do_not_use_in_prod_1234567890',
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '15m',
  JWT_REFRESH_SECRET: process.env.JWT_REFRESH_SECRET || 'easp_dev_jwt_refresh_secret_do_not_use_in_prod_0987654321',
  JWT_REFRESH_EXPIRES_IN: process.env.JWT_REFRESH_EXPIRES_IN || '7d',

  // Reversible Token Encryption (Phase 4 - AES-256-GCM, 32-byte hex key)
  ENCRYPTION_SECRET_KEY: process.env.ENCRYPTION_SECRET_KEY || process.env.ENCRYPTION_KEY || '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',

  // Rate Limiting (Phase 2)
  RATE_LIMIT_WINDOW_MS: parseInt(process.env.RATE_LIMIT_WINDOW_MS, 10) || 15 * 60 * 1000,
  RATE_LIMIT_MAX_AUTH: parseInt(process.env.RATE_LIMIT_MAX_AUTH, 10) || 10,
  RATE_LIMIT_MAX_GENERAL: parseInt(process.env.RATE_LIMIT_MAX_GENERAL, 10) || 200
};

if (!/^[a-f\d]{64}$/i.test(env.ENCRYPTION_SECRET_KEY)) {
  throw new Error('ENCRYPTION_SECRET_KEY must be a 32-byte hexadecimal key');
}
if (env.NODE_ENV === 'production') {
  for (const name of ['JWT_SECRET', 'JWT_REFRESH_SECRET']) {
    if (!process.env[name] || env[name].length < 32 || env[name].startsWith('easp_dev_')) {
      throw new Error(`${name} must be explicitly configured with a strong production secret`);
    }
  }
  if (env.ENCRYPTION_SECRET_KEY === '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef') {
    throw new Error('Configure a unique production encryption key');
  }
}

module.exports = env;
