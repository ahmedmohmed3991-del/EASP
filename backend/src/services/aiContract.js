const score = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;
const dlp = d => !!d && score(d.sensitivity_score) && typeof d.redacted_text === 'string' &&
  typeof d.has_sensitive_data === 'boolean' && Array.isArray(d.entities) && Array.isArray(d.mappings) &&
  d.mappings.every(m => m && ['token_id', 'entity_type', 'original_value'].every(k => typeof m[k] === 'string'));
const nlp = d => !!d && score(d.social_engineering_score) && Array.isArray(d.threats_detected);
const audio = d => !!d && d.voice_deepfake?.success === true && d.voice_deepfake.model_loaded === true &&
  score(d.voice_deepfake.spoof_score) && typeof d.voice_deepfake.is_deepfake === 'boolean' &&
  d.transcription?.success === true && typeof d.transcription.transcript === 'string' &&
  nlp(d.social_engineering) && dlp(d.dlp);
module.exports = { score, dlp, nlp, audio };
