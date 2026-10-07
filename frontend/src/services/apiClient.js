import { validateSecurityResponse } from './securityContract';
// EASP Frontend API Client - Phase 11
// Handles authenticated HTTP communication with the Node.js backend.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

export function getAuthToken() {
  return localStorage.getItem('easp_jwt_token');
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('easp_jwt_token', token);
  } else {
    localStorage.removeItem('easp_jwt_token');
  }
}

export function getCurrentUser() {
  const userJson = localStorage.getItem('easp_user');
  try {
    return userJson ? JSON.parse(userJson) : null;
  } catch {
    return null;
  }
}

export function setCurrentUser(user) {
  if (user) {
    localStorage.setItem('easp_user', JSON.stringify(user));
  } else {
    localStorage.removeItem('easp_user');
  }
}

async function request(path, options = {}) {
  const token = getAuthToken();
  const headers = {
    Accept: 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Handle JSON vs FormData
  if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      setAuthToken(null);
      setCurrentUser(null);
      window.dispatchEvent(new Event('auth:logout'));
    }
    throw new Error(data.error || `HTTP error ${response.status}`);
  }
  if (path.endsWith('/scan-prompt') || path.endsWith('/analyze-call')) {
    validateSecurityResponse(data, path.endsWith('/analyze-call'));
  }
  return data;
}

// Authentication API
export const authApi = {
  login: (email, password) =>
    request('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password }
    }),
  getMe: () => request('/api/v1/auth/me')
};

// Security API
export const securityApi = {
  scanPrompt: (prompt) =>
    request('/api/v1/security/scan-prompt', {
      method: 'POST',
      body: { prompt }
    }),
  restoreToken: (tokenId) =>
    request('/api/v1/security/restore-token', {
      method: 'POST',
      body: { tokenId }
    }),
  analyzeCall: (formData) =>
    request('/api/v1/security/analyze-call', {
      method: 'POST',
      body: formData
    }),
  getSpeakerProfiles: () =>
    request('/api/v1/security/speaker-profiles'),
  evaluateRisk: (voiceScore, socialScore, dlpScore) =>
    request('/api/v1/security/evaluate-risk', {
      method: 'POST',
      body: { voiceScore, socialScore, dlpScore }
    })
};

// Incidents API
export const incidentApi = {
  getIncidents: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/v1/incidents${query ? '?' + query : ''}`);
  },
  updateIncident: (id, status, note) =>
    request(`/api/v1/incidents/${id}`, {
      method: 'PATCH',
      body: { status, note }
    })
};

// Audit Logs API
export const auditApi = {
  getLogs: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/v1/audit-logs${query ? '?' + query : ''}`);
  },
  verifyChain: () => request('/api/v1/audit-logs/verify')
};

// Policies API
export const policyApi = {
  getPolicies: () => request('/api/v1/policies'),
  createPolicy: (policy) =>
    request('/api/v1/policies', {
      method: 'POST',
      body: policy
    })
};

// Metrics API
export const metricsApi = {
  getMetrics: () => request('/api/v1/metrics')
};
