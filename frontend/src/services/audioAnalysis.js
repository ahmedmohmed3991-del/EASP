export function normalizeAudioAnalysis(raw) {
  return {
  policyAction: raw.action,
  policyReason: raw.policyTriggered || raw.policyReason || 'Automated policy evaluation complete.',
  riskScore: raw.risk.score,
  riskLevel: raw.risk.level,
  incidentId: raw.incidentId,
  auditLogId: raw.auditLogId,
  // Model 1: General RawNet2 Voice Deepfake
  voiceAnalysis: {
    spoofScore: raw.voiceDeepfake?.spoofScore ?? raw.voiceAnalysis?.spoofScore ?? 0.0,
    isSynthetic: raw.voiceDeepfake?.isDeepfake ?? raw.voiceAnalysis?.isSynthetic ?? false,
    inferenceMode: raw.voiceDeepfake?.inferenceEngine ?? raw.voiceAnalysis?.inferenceMode ?? 'RawNet2-ASVspoof',
    spectralFeatures: raw.voiceDeepfake?.spectralFeatures || raw.voiceAnalysis?.spectralFeatures || null
  },
  // Model 2: Acoustic Frequency & Gender Profiler (Doctor's Frequency Model)
  acousticProfile: raw.speakerFrequencyProfile?.evaluation || null,
  callerMeasurements: raw.speakerFrequencyProfile?.caller_acoustic_measurements || null,
  targetProfile: raw.speakerFrequencyProfile?.target_profile || null,
  // Speech & NLP
  transcript: raw.transcription?.transcript ?? raw.transcript ?? '',
  nlpAnalysis: {
    socialEngineeringScore: raw.socialEngineering?.score ?? raw.nlpAnalysis?.socialEngineeringScore ?? 0.0,
    threatCategories: raw.socialEngineering?.threatsDetected ?? raw.nlpAnalysis?.threatCategories ?? []
  }
};
}
