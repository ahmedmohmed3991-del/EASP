// Health-check API service.
// Talks to the backend /health and /health/ai endpoints and derives
// connection status for Frontend, Backend, AI Service, and Database.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

// Fetches backend health, which itself reports MongoDB state.
export async function fetchBackendHealth() {
  const response = await fetch(`${BACKEND_URL}/health`);
  if (!response.ok) {
    throw new Error(`Backend responded with status ${response.status}`);
  }
  return response.json();
}

// Fetches AI service health via the backend's proxy check.
export async function fetchAIHealth() {
  const response = await fetch(`${BACKEND_URL}/health/ai`);
  // Note: backend returns 503 (not ok) when AI service is unreachable,
  // but the JSON body still tells us what happened, so we parse it either way.
  return response.json();
}
