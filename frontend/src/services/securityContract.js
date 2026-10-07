export function validateSecurityResponse(response, audio = false) {
  const data = response?.data;
  const score = x => typeof x === 'number' && Number.isFinite(x) && x >= 0 && x <= 1;
  if (response?.status !== 'success' || !['ALLOW', 'REDACT', 'BLOCK', 'ESCALATE'].includes(data?.action) ||
      !score(data.risk?.score) || !['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].includes(data.risk?.level) ||
      !Array.isArray(data.dlp?.entitiesDetected) || !score(data.socialEngineering?.score) ||
      !Array.isArray(data.socialEngineering?.threatsDetected) ||
      (audio ? !score(data.voiceDeepfake?.spoofScore) || typeof data.voiceDeepfake?.isDeepfake !== 'boolean' ||
        typeof data.transcription?.transcript !== 'string' : typeof data.processedPrompt !== 'string')) {
    throw new Error('Security analysis is incomplete or invalid. Please retry.');
  }
  return response;
}
