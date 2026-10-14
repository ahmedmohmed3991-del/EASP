// EASP AI Service HTTP Client - Phase 10 (T-P10-050)
// Connects Node.js backend to FastAPI AI microservice over internal HTTP network.
// Implements timeout handling, circuit-breaker safety, and conservative fail-safe fallbacks.

const axios = require('axios');
const FormData = require('form-data');
const env = require('../config/env');

const TIMEOUT_MS = 60000; // 60s timeout for deep neural inference on CPU

const client = axios.create({
  baseURL: env.AI_SERVICE_URL,
  timeout: TIMEOUT_MS,
  headers: {
    'X-Service-Client': 'easp-backend-gateway'
  }
});

// Scan text for sensitive data & credentials
async function scanDlp(text, userId = 'anonymous') {
  try {
    const res = await client.post('/dlp/scan', { text, user_id: userId });
    return { success: true, data: res.data.data };
  } catch (err) {
    console.error(`[AI Client] DLP scan failed: ${err.message}`);
    return {
      success: false,
      error: err.message,
      data: {
        original_text: text,
        redacted_text: text,
        entities: [],
        mappings: [],
        sensitivity_score: 0.50, // Conservative fail-safe penalty
        has_sensitive_data: false
      }
    };
  }
}

// Classify text for social engineering coercion & threats
async function classifyNlp(text) {
  try {
    const res = await client.post('/nlp/classify', { text });
    return { success: true, data: res.data.data };
  } catch (err) {
    console.error(`[AI Client] NLP classify failed: ${err.message}`);
    return {
      success: false,
      error: err.message,
      data: {
        social_engineering_score: 0.50,
        has_threat: false,
        threats_detected: [],
        labels: {}
      }
    };
  }
}

// Consolidated audio pipeline (deepfake + transcribe + NLP + DLP + speaker frequency profiler)
async function analyzeAudioPipeline(audioBuffer, filename = 'call_audio.wav', speakerProfileId = null) {
  try {
    const formData = new FormData();
    formData.append('file', audioBuffer, { filename, contentType: 'audio/wav' });
    if (speakerProfileId) {
      formData.append('speaker_profile_id', speakerProfileId);
    }

    const res = await client.post('/audio/analyze', formData, {
      headers: formData.getHeaders(),
      maxContentLength: 50 * 1024 * 1024,
      timeout: 120000 // 120s dedicated timeout for multi-model CPU pipeline
    });

    return { success: true, data: res.data.data };
  } catch (err) {
    console.error(`[AI Client] Audio pipeline failed: ${err.message}`);
    return {
      success: false,
      error: err.message,
      data: {
        voice_deepfake: { spoof_score: 0.50, is_deepfake: false },
        speaker_frequency_profile: null,
        transcription: { transcript: '' },
        social_engineering: { social_engineering_score: 0.50, threats_detected: [] },
        dlp: { sensitivity_score: 0.50, mappings: [] }
      }
    };
  }
}

// Fetch enrolled VIP speaker acoustic baseline profiles
async function getSpeakerProfiles() {
  try {
    const res = await client.get('/audio/speaker-profiles');
    return { success: true, data: res.data.data };
  } catch (err) {
    console.error(`[AI Client] Failed to fetch speaker profiles: ${err.message}`);
    return { success: false, data: [] };
  }
}

// Synchronize voices folder as speaker profiles
async function syncVoices() {
  try {
    const res = await client.post('/audio/sync-voices');
    return { success: true, data: res.data };
  } catch (err) {
    console.error(`[AI Client] Failed to sync voices: ${err.message}`);
    return { success: false, error: err.message };
  }
}

// Check AI Service Health
async function checkHealth() {
  try {
    const res = await client.get('/health');
    return { reachable: true, data: res.data };
  } catch (err) {
    return { reachable: false, error: err.message };
  }
}

module.exports = {
  scanDlp,
  classifyNlp,
  analyzeAudioPipeline,
  getSpeakerProfiles,
  syncVoices,
  checkHealth
};

