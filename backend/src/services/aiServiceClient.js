// Internal AI transport: failures never become synthetic successful results.
const axios = require('axios');
const FormData = require('form-data');
const env = require('../config/env');
const contract = require('./aiContract');
const client = axios.create({ baseURL: env.AI_SERVICE_URL, timeout: 8000,
  headers: process.env.AI_SERVICE_TOKEN ? { 'X-Service-Token': process.env.AI_SERVICE_TOKEN } : {} });
async function call(path, body, valid, options = {}) {
  try {
    const response = body === undefined ? await client.get(path, options) : await client.post(path, body, options);
    if (response.data?.status !== 'success' || !valid(response.data.data)) return { success: false };
    return { success: true, data: response.data.data };
  } catch { return { success: false }; }
}
const scanDlp = (text, userId = 'anonymous') => call('/dlp/scan', { text, user_id: userId }, contract.dlp);
const classifyNlp = text => call('/nlp/classify', { text }, contract.nlp);
async function analyzeAudioPipeline(buffer, filename = 'call.wav', speakerProfileId = null) {
  const form = new FormData();
  form.append('file', buffer, { filename, contentType: 'audio/wav' });
  if (speakerProfileId) form.append('speaker_profile_id', speakerProfileId);
  return call('/audio/analyze', form, contract.audio, { headers: form.getHeaders(), timeout: 120000,
    maxBodyLength: 26 * 1024 * 1024, maxContentLength: 50 * 1024 * 1024 });
}
const getSpeakerProfiles = () => call('/audio/speaker-profiles', undefined, Array.isArray);
async function checkHealth() {
  try { const res = await client.get('/health'); return { reachable: true, data: res.data }; }
  catch { return { reachable: false, error: 'AI service unavailable' }; }
}
module.exports = { scanDlp, classifyNlp, analyzeAudioPipeline, getSpeakerProfiles, checkHealth };
