// EASP Policy Engine Service - Phase 5 (T-P05-028 / T-P05-031)
// Evaluates fused risk scores, roles, and DLP findings against active policies
// to determine the enforced action: ALLOW, REDACT, ESCALATE, or BLOCK.
// Enforces audit logging and automatic incident generation for security escalation.

const Policy = require('../models/Policy');
const AuditLog = require('../models/AuditLog');
const Incident = require('../models/Incident');

async function evaluatePolicy({
  userId = null,
  username = 'anonymous',
  userRole = 'Employee',
  ipAddress = 'unknown',
  riskScore = 0.0,
  riskLevel = 'LOW',
  dlpFindings = [],
  contributingFactors = {},
  source = 'PROMPT_SCAN'
}) {
  // Query all active policies sorted by priority (lowest number = highest priority)
  const policies = await Policy.find({
    isActive: true,
    $or: [{ targetRole: 'All' }, { targetRole: userRole }]
  }).sort({ priority: 1 });

  let selectedPolicy = null;
  let enforcedAction = 'BLOCK';
  let requireDlpRedaction = false;

  for (const policy of policies) {
    if (riskScore >= policy.minRiskScore && riskScore <= policy.maxRiskScore) {
      selectedPolicy = policy;
      enforcedAction = policy.action;
      requireDlpRedaction = policy.requireDlpRedaction;
      break;
    }
  }

  // Override: If sensitive DLP findings exist and no coercive social engineering attack, enforce REDACT
  const socialThreat = (contributingFactors && contributingFactors.social_engineering) || 0.0;
  if (dlpFindings && dlpFindings.length > 0 && socialThreat < 0.70 && !['BLOCK', 'ESCALATE'].includes(enforcedAction)) {
    enforcedAction = 'REDACT';
    requireDlpRedaction = true;
  }

  if (requireDlpRedaction && enforcedAction === 'ALLOW') enforcedAction = 'REDACT';

  // 1. Immutable Audit Logging with SHA-256 hash chaining
  const auditEntry = await AuditLog.logEvent({
    eventType: 'POLICY_DECISION',
    userId,
    username,
    userRole,
    ipAddress,
    actionTaken: enforcedAction,
    riskScore,
    riskLevel,
    details: {
      source,
      policyName: selectedPolicy ? selectedPolicy.name : 'Default Fallback Policy',
      dlpCount: dlpFindings ? dlpFindings.length : 0,
      contributingFactors
    }
  });

  // 2. Incident Generation for ESCALATE, BLOCK, or HIGH risk events
  let incident = null;
  if (enforcedAction === 'BLOCK' || enforcedAction === 'ESCALATE' || riskLevel === 'HIGH') {
    const severity = riskScore >= 0.85 ? 'CRITICAL' : riskScore >= 0.70 ? 'HIGH' : 'MEDIUM';
    incident = await Incident.create({
      title: `Security Policy Triggered: [${enforcedAction}] on ${source}`,
      severity,
      status: 'OPEN',
      source,
      userId,
      username,
      riskScore,
      riskLevel,
      contributingFactors: {
        voiceRisk: contributingFactors.voice_deepfake || 0.0,
        socialRisk: contributingFactors.social_engineering || 0.0,
        dlpSensitivity: contributingFactors.dlp_sensitivity || 0.0
      },
      actionTaken: enforcedAction,
      auditLogId: auditEntry._id,
      notes: [{
        author: 'System (Policy Engine)',
        text: `Automated incident generated due to ${enforcedAction} policy rule '${selectedPolicy ? selectedPolicy.name : 'High Risk Rule'}'.`
      }]
    });
  }

  return {
    action: enforcedAction,
    policyName: selectedPolicy ? selectedPolicy.name : 'Default Fallback Policy',
    riskScore,
    riskLevel,
    requireDlpRedaction,
    auditLogId: auditEntry._id,
    incidentId: incident ? incident._id : null
  };
}

module.exports = { evaluatePolicy };
