// EASP Unified Risk Engine - Phase 6 (T-P06-033 / T-P06-034)
// Deterministic weighted rule fusion combining Voice Deepfake, Social Engineering, and DLP sensitivity.
// Fail-safe: Missing or malformed inputs trigger conservative default values.

// Phase 1 Baseline Weights (documented implementation decision pending formal committee sign-off)
const WEIGHTS = {
  voice_deepfake: 0.40,
  social_engineering: 0.35,
  dlp_sensitivity: 0.25
};

const THRESHOLDS = {
  LOW_MAX: 0.3999,
  MEDIUM_MAX: 0.6999,
  HIGH_MIN: 0.70
};

function calculateRisk({
  voiceScore = 0.0,
  socialScore = 0.0,
  dlpScore = 0.0,
  isVoiceApplicable = true,
  hasVoiceError = false,
  hasSocialError = false,
  hasDlpError = false
}) {
  // Fail-safe: If an active upstream service failed or is unavailable, adopt conservative penalty
  let safeVoice = Number(voiceScore);
  let safeSocial = Number(socialScore);
  let safeDlp = Number(dlpScore);

  if (isVoiceApplicable && (hasVoiceError || isNaN(safeVoice))) safeVoice = 0.50;
  if (hasSocialError || isNaN(safeSocial)) safeSocial = 0.50;
  if (hasDlpError || isNaN(safeDlp)) safeDlp = 0.50;

  // Clamp signals to [0.0, 1.0]
  safeVoice = Math.max(0.0, Math.min(1.0, safeVoice));
  safeSocial = Math.max(0.0, Math.min(1.0, safeSocial));
  safeDlp = Math.max(0.0, Math.min(1.0, safeDlp));

  let fusedRisk = 0.0;

  if (isVoiceApplicable) {
    // Standard tri-factor fusion across audio + text + DLP
    fusedRisk =
      WEIGHTS.voice_deepfake * safeVoice +
      WEIGHTS.social_engineering * safeSocial +
      WEIGHTS.dlp_sensitivity * safeDlp;
  } else {
    // Text-only modality normalization (prevents dilution when voice is not in scope)
    const textTotalWeight = WEIGHTS.social_engineering + WEIGHTS.dlp_sensitivity; // 0.60
    const normSocial = WEIGHTS.social_engineering / textTotalWeight; // ~0.583
    const normDlp = WEIGHTS.dlp_sensitivity / textTotalWeight;       // ~0.417
    fusedRisk = normSocial * safeSocial + normDlp * safeDlp;
  }

  // Elevate to HIGH if social engineering coercion is severe (>= 0.80) or combined attacks
  if (safeSocial >= 0.80 || (safeSocial >= 0.60 && safeDlp >= 0.70) || (isVoiceApplicable && safeVoice >= 0.80 && safeSocial >= 0.60)) {
    fusedRisk = Math.max(fusedRisk, 0.75);
  }

  // Classify level
  let level = 'LOW';
  if (fusedRisk >= THRESHOLDS.HIGH_MIN) {
    level = 'HIGH';
  } else if (fusedRisk > THRESHOLDS.LOW_MAX) {
    level = 'MEDIUM';
  }

  return {
    scoringProfile: 'node-v1',
    fusedRisk: Number(fusedRisk.toFixed(4)),
    level,
    weights: WEIGHTS,
    isVoiceApplicable,
    contributingFactors: {
      voice_deepfake: isVoiceApplicable ? safeVoice : null,
      social_engineering: safeSocial,
      dlp_sensitivity: safeDlp
    },
    failSafeTriggered: hasVoiceError || hasSocialError || hasDlpError
  };
}

module.exports = { calculateRisk, WEIGHTS, THRESHOLDS };
