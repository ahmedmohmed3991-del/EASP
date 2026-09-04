// Centralized environment variable loader for the backend.
// Phase 0: only infrastructure-related variables. No auth secrets yet.

require('dotenv').config();

const env = {
  PORT: parseInt(process.env.PORT, 10) || 5000,
  MONGO_URI: process.env.MONGO_URI || 'mongodb://localhost:27017/easp',
  AI_SERVICE_URL: process.env.AI_SERVICE_URL || 'http://localhost:8000',
  NODE_ENV: process.env.NODE_ENV || 'development',
  ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS || process.env.CORS_ALLOWED_ORIGINS || 'http://localhost:5173,http://localhost:3000'
};

module.exports = env;

