// EASP Security Engine Routes - Phase 12 (T-P12-057 / T-P12-058)
// Core operational endpoints connecting DLP, Voice Anti-Spoofing, Social Engineering,
// Unified Risk Engine, Policy Engine, and Append-Only Audit Logging.

const express = require('express');
const multer = require('multer');
const { authenticateJWT } = require('../middleware/auth');
const { authorizeRoles } = require('../middleware/rbac');
const { validateBody } = require('../middleware/validate');
const { apiLimiter } = require('../middleware/rateLimiter');
const aiClient = require('../services/aiServiceClient');
const contract = require('../services/aiContract');
const riskEngine = require('../services/riskEngine');
const policyEngine = require('../services/policyEngine');
const tokenService = require('../services/tokenService');
const { safeEntities, protectText } = require('../services/dlpOutput');

const router = express.Router();

async function persistDlpMappings(mappings, userId) {
  if (!mappings || mappings.length === 0) return;
  for (const mapping of mappings) {
    await tokenService.saveTokenMapping({
      tokenId: mapping.token_id,
      entityType: mapping.entity_type,
      plaintextValue: mapping.original_value,
      userId
    });
  }
}

// Configure Multer memory storage for audio streams (max 25MB)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 }
});

// 1. POST /api/v1/security/scan-prompt
// Employee & above: Scans text prompts for DLP secrets, runs NLP threat detection, enforces policy
router.post(
  '/scan-prompt',
  apiLimiter,
  authenticateJWT,
  validateBody({
    prompt: { required: true, type: 'string', min: 1, max: 20000 }
  }),
  async (req, res) => {
    try {
      const { prompt } = req.body;
      const user = req.user;
      const ipAddress = req.ip || req.connection.remoteAddress || 'unknown';

      // Step 1: DLP Scan & Token Generation
      const dlpResponse = await aiClient.scanDlp(prompt, user.id);
      if (!dlpResponse.success || !contract.dlp(dlpResponse.data)) {
        return res.status(503).json({ status: 'error', error: 'DLP scanning is unavailable. Prompt processing was stopped.' });
      }
      const dlpData = dlpResponse.data;

      // Step 2: Persist Reversible Encrypted Token Mappings into MongoDB
      await persistDlpMappings(dlpData.mappings, user.id);

      // Step 3: NLP Social Engineering Threat Classification
      const nlpResponse = await aiClient.classifyNlp(prompt);
      if (!nlpResponse.success || !contract.nlp(nlpResponse.data)) {
        return res.status(503).json({ status: 'error', error: 'Threat classification is unavailable. Prompt processing was stopped.' });
      }
      const nlpData = nlpResponse.data;

      // Step 4: Phase 1 Unified Risk Engine Fusion (modality normalized for text)
      const riskAssessment = riskEngine.calculateRisk({
        voiceScore: 0.0,
        socialScore: nlpData.social_engineering_score || 0.0,
        dlpScore: dlpData.sensitivity_score || 0.0,
        isVoiceApplicable: false,
        hasSocialError: !nlpResponse.success,
        hasDlpError: !dlpResponse.success
      });

      // Step 5: Policy Engine Enforcement & Append-Only Audit Logging
      const policyDecision = await policyEngine.evaluatePolicy({
        userId: user.id,
        username: user.username,
        userRole: user.role,
        ipAddress,
        riskScore: riskAssessment.fusedRisk,
        riskLevel: riskAssessment.level,
        dlpFindings: dlpData.entities,
        contributingFactors: riskAssessment.contributingFactors,
        source: 'PROMPT_SCAN'
      });

      // Step 6: Formulate Protected Output Response
      let finalPrompt = protectText(prompt, dlpData);
      if (policyDecision.action === 'BLOCK') {
        finalPrompt = '[BLOCKED BY EASP SECURITY POLICY: HIGH RISK CONTENT DETECTED]';
      } else if (policyDecision.action === 'REDACT' || policyDecision.requireDlpRedaction) {
        finalPrompt = protectText(prompt, dlpData, true);
      }

      res.status(200).json({
        status: 'success',
        data: {
          action: policyDecision.action,
          policyTriggered: policyDecision.policyName,
          risk: {
            scoringProfile: riskAssessment.scoringProfile,
            score: riskAssessment.fusedRisk,
            level: riskAssessment.level,
            contributingFactors: riskAssessment.contributingFactors
          },
          dlp: {
            hasSensitiveData: dlpData.has_sensitive_data,
            entitiesDetected: dlpData.entities.map(e => ({
              type: e.entity_type,
              category: e.category,
              confidence: e.confidence,
              severity: e.severity
            })),
            tokensGenerated: dlpData.mappings ? dlpData.mappings.length : 0
          },
          socialEngineering: {
            score: nlpData.social_engineering_score,
            threatsDetected: nlpData.threats_detected || []
          },
          processedPrompt: finalPrompt,
          incidentId: policyDecision.incidentId,
          auditLogId: policyDecision.auditLogId
        }
      });
    } catch (err) {
      console.error('[scan-prompt error]', err.name);
      res.status(500).json({
        status: 'error',
        error: 'Failed to process prompt security scan: '
      });
    }
  }
);

// 2. POST /api/v1/security/analyze-call
// Analyst & above: Analyzes audio stream for deepfakes, transcribes, scans NLP & DLP, enforces policy
router.post(
  '/analyze-call',
  apiLimiter,
  authenticateJWT,
  upload.single('audio'),
  async (req, res) => {
    try {
      if (!req.file || !req.file.buffer) {
        return res.status(400).json({
          status: 'error',
          error: 'Audio file upload is required (field name: "audio")'
        });
      }

      const user = req.user;
      const ipAddress = req.ip || req.connection.remoteAddress || 'unknown';
      const speakerProfileId = req.body.speakerProfileId || null;

      // Step 1: Execute Consolidated Audio Pipeline via FastAPI
      const pipelineRes = await aiClient.analyzeAudioPipeline(
        req.file.buffer,
        req.file.originalname || 'call.wav',
        speakerProfileId
      );
      const pipelineData = pipelineRes.data;
      if (!pipelineRes.success || !contract.audio(pipelineData)) {
        return res.status(503).json({ status: 'error', error: 'Audio analysis is incomplete or unavailable. Please retry.' });
      }

      const voiceScore = pipelineData.voice_deepfake?.spoof_score || 0.0;
      const transcript = pipelineData.transcription?.transcript || '';
      const socialScore = pipelineData.social_engineering?.social_engineering_score || 0.0;
      const dlpData = pipelineData.dlp || { sensitivity_score: 0.0, entities: [], mappings: [] };
      const freqProfileData = pipelineData.speaker_frequency_profile || null;

      // If an executive profile was checked, fuse the higher of RawNet2 spoof score vs Impersonation discrepancy
      const impersonationRisk = freqProfileData?.evaluation?.impersonation_risk_score ?? 0.0;
      const effectiveVoiceScore = Math.max(voiceScore, impersonationRisk);

      // Step 2: Store any detected DLP tokens from the transcription
      await persistDlpMappings(dlpData.mappings, user.id);

      // Step 3: Unified Risk Fusion
      const riskAssessment = riskEngine.calculateRisk({
        voiceScore: effectiveVoiceScore,
        socialScore,
        dlpScore: dlpData.sensitivity_score || 0.0,
        hasVoiceError: !pipelineRes.success,
        hasSocialError: !pipelineRes.success,
        hasDlpError: !pipelineRes.success
      });

      // Step 4: Policy Enforcement & Audit Logging
      const isFreqMismatch = freqProfileData?.evaluation?.pitch_in_range === false;
      const policyDecision = await policyEngine.evaluatePolicy({
        userId: user.id,
        username: user.username,
        userRole: user.role,
        ipAddress,
        riskScore: riskAssessment.fusedRisk,
        riskLevel: riskAssessment.level,
        dlpFindings: dlpData.entities,
        contributingFactors: riskAssessment.contributingFactors,
        source: 'CALL_ANALYSIS'
      });

      res.status(200).json({
        status: 'success',
        data: {
          action: policyDecision.action,
          policyTriggered: isFreqMismatch ? `${policyDecision.policyName} (Acoustic Frequency Discrepancy)` : policyDecision.policyName,
          policyReason: isFreqMismatch ? freqProfileData.evaluation.explanation : 'Automated security policy evaluation complete.',
          risk: {
            scoringProfile: riskAssessment.scoringProfile,
            score: riskAssessment.fusedRisk,
            level: riskAssessment.level,
            contributingFactors: riskAssessment.contributingFactors
          },
          // Model 1: General RawNet2 Voice Deepfake Detection
          voiceDeepfake: {
            spoofScore: voiceScore,
            isDeepfake: pipelineData.voice_deepfake?.is_deepfake || false,
            inferenceEngine: pipelineData.voice_deepfake?.inference_engine || 'RawNet2-ASVspoof',
            spectralFeatures: pipelineData.voice_deepfake?.spectral_variance ? {
              zeroCrossingRate: pipelineData.voice_deepfake?.zero_crossing_rate,
              spectralVariance: pipelineData.voice_deepfake?.spectral_variance
            } : null
          },
          // Model 2: Speaker Acoustic Frequency Baseline Profiler (Doctor's Model)
          speakerFrequencyProfile: freqProfileData,
          transcription: {
            transcript: protectText(transcript, dlpData),
            language: pipelineData.transcription?.language || 'en',
            durationSeconds: pipelineData.transcription?.duration_seconds || 0
          },
          socialEngineering: {
            score: socialScore,
            threatsDetected: pipelineData.social_engineering?.threats_detected || []
          },
          dlp: {
            sensitivityScore: dlpData.sensitivity_score,
            entitiesDetected: safeEntities(dlpData.entities)
          },
          incidentId: policyDecision.incidentId,
          auditLogId: policyDecision.auditLogId
        }
      });
    } catch (err) {
      res.status(500).json({
        status: 'error',
        error: 'Failed to analyze call audio: '
      });
    }
  }
);

// 2.1 GET /api/v1/security/speaker-profiles
// Returns list of enrolled VIP acoustic baseline profiles
router.get(
  '/speaker-profiles',
  apiLimiter,
  authenticateJWT,
  async (req, res) => {
    try {
      const profilesRes = await aiClient.getSpeakerProfiles();
      if (!profilesRes.success) return res.status(503).json({ status: "error", error: "AI service unavailable" });
      res.status(200).json({
        status: 'success',
        data: profilesRes.data || []
      });
    } catch (err) {
      res.status(500).json({
        status: 'error',
        error: 'Failed to retrieve speaker profiles: '
      });
    }
  }
);

// 3. POST /api/v1/security/restore-token
// Strictly restricted to Analyst & Administrator: Restores original sensitive value from encrypted token
router.post(
  '/restore-token',
  apiLimiter,
  authenticateJWT,
  authorizeRoles('Analyst', 'Administrator'),
  validateBody({
    tokenId: { required: true, type: 'string', min: 5, max: 100 }
  }),
  async (req, res) => {
    try {
      const { tokenId } = req.body;
      const ipAddress = req.ip || req.connection.remoteAddress || 'unknown';

      const restoreResult = await tokenService.restoreToken({
        tokenId,
        user: req.user,
        ipAddress
      });

      if (!restoreResult.success) {
        return res.status(restoreResult.statusCode || 400).json({
          status: 'error',
          error: restoreResult.error
        });
      }

      res.status(200).json({
        status: 'success',
        data: {
          tokenId: restoreResult.tokenId,
          entityType: restoreResult.entityType,
          originalValue: restoreResult.originalValue,
          expiresAt: restoreResult.expiresAt
        }
      });
    } catch (err) {
      res.status(500).json({
        status: 'error',
        error: 'Failed to restore token mapping: '
      });
    }
  }
);

// 4. POST /api/v1/security/evaluate-risk
// Internal/Admin endpoint for standalone risk calculation & verification
router.post(
  '/evaluate-risk',
  apiLimiter,
  authenticateJWT,
  validateBody({
    voiceScore: { required: false, type: 'number', min: 0.0, max: 1.0 },
    socialScore: { required: false, type: 'number', min: 0.0, max: 1.0 },
    dlpScore: { required: false, type: 'number', min: 0.0, max: 1.0 }
  }),
  (req, res) => {
    const { voiceScore = 0.0, socialScore = 0.0, dlpScore = 0.0 } = req.body;
    const result = riskEngine.calculateRisk({ voiceScore, socialScore, dlpScore });
    res.status(200).json({ status: 'success', data: result });
  }
);

module.exports = router;
