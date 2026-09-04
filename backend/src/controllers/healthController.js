// Health check logic for the backend service.
// Phase 0 scope only: reports backend status, MongoDB state, and AI service reachability.

const axios = require('axios');
const env = require('../config/env');
const { getConnectionState } = require('../config/db');

// GET /health
function getHealth(req, res) {
  const mongoState = getConnectionState();

  res.status(200).json({
    status: 'ok',
    service: 'easp-backend',
    phase: 'phase-0',
    timestamp: new Date().toISOString(),
    dependencies: {
      mongodb: {
        state: mongoState,
        connected: mongoState === 'connected'
      }
    }
  });
}

// GET /health/ai
// Verifies connectivity from the backend to the AI (FastAPI) service.
async function getAIHealth(req, res) {
  const startedAt = Date.now();

  try {
    const response = await axios.get(`${env.AI_SERVICE_URL}/health`, {
      timeout: 3000
    });

    res.status(200).json({
      status: 'ok',
      service: 'easp-backend',
      ai_service: {
        reachable: true,
        url: env.AI_SERVICE_URL,
        response_time_ms: Date.now() - startedAt,
        data: response.data
      }
    });
  } catch (err) {
    res.status(503).json({
      status: 'degraded',
      service: 'easp-backend',
      ai_service: {
        reachable: false,
        url: env.AI_SERVICE_URL,
        error: err.message
      }
    });
  }
}

module.exports = { getHealth, getAIHealth };
