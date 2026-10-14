// EASP Audit Log Schema - Phase 5 (T-P05-029 / T-P05-030)
// Implements append-only, tamper-evident cryptographic hash chaining (SHA-256).
// No update or delete operations are exposed on this collection.

const mongoose = require('mongoose');
const crypto = require('crypto');

const GENESIS_HASH = '0'.repeat(64);

const AuditLogSchema = new mongoose.Schema({
  timestamp: {
    type: Date,
    default: Date.now,
    immutable: true
  },
  eventType: {
    type: String,
    required: true,
    enum: [
      'AUTH_LOGIN',
      'AUTH_REGISTER',
      'AUTH_FAILURE',
      'DLP_SCAN',
      'DLP_REDACT',
      'DLP_RESTORE',
      'VOICE_DEEPFAKE_ANALYSIS',
      'SOCIAL_ENGINEERING_ANALYSIS',
      'RISK_EVALUATION',
      'POLICY_DECISION',
      'INCIDENT_CREATED',
      'INCIDENT_UPDATED'
    ],
    immutable: true
  },
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    default: null,
    immutable: true
  },
  username: {
    type: String,
    default: 'anonymous',
    immutable: true
  },
  userRole: {
    type: String,
    default: 'None',
    immutable: true
  },
  ipAddress: {
    type: String,
    default: 'unknown',
    immutable: true
  },
  actionTaken: {
    type: String,
    required: true,
    enum: ['ALLOW', 'REDACT', 'ESCALATE', 'BLOCK', 'INFO', 'ALERT'],
    immutable: true
  },
  riskScore: {
    type: Number,
    min: 0.0,
    max: 1.0,
    default: 0.0,
    immutable: true
  },
  riskLevel: {
    type: String,
    enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'N/A'],
    default: 'N/A',
    immutable: true
  },
  details: {
    type: mongoose.Schema.Types.Mixed,
    default: {},
    immutable: true
  },
  previousHash: {
    type: String,
    required: true,
    immutable: true
  },
  hash: {
    type: String,
    required: true,
    immutable: true
  }
});

// Compute the SHA-256 hash for an audit record
AuditLogSchema.statics.computeHash = function (previousHash, timestamp, eventType, username, actionTaken, riskScore, details) {
  const content = [
    previousHash,
    new Date(timestamp).toISOString(),
    eventType,
    username || 'anonymous',
    actionTaken,
    (riskScore || 0).toFixed(4),
    JSON.stringify(details || {})
  ].join('|');

  return crypto.createHash('sha256').update(content).digest('hex');
};

// Append a new immutable audit record to the chain
AuditLogSchema.statics.logEvent = async function ({
  eventType,
  userId = null,
  username = 'anonymous',
  userRole = 'None',
  ipAddress = 'unknown',
  actionTaken = 'INFO',
  riskScore = 0.0,
  riskLevel = 'N/A',
  details = {}
}) {
  // Find latest entry to get its hash
  const lastEntry = await this.findOne().sort({ timestamp: -1, _id: -1 });
  const previousHash = lastEntry ? lastEntry.hash : GENESIS_HASH;
  const timestamp = new Date();

  const hash = this.computeHash(
    previousHash,
    timestamp,
    eventType,
    username,
    actionTaken,
    riskScore,
    details
  );

  return this.create({
    timestamp,
    eventType,
    userId,
    username,
    userRole,
    ipAddress,
    actionTaken,
    riskScore,
    riskLevel,
    details,
    previousHash,
    hash
  });
};

// Cryptographic chain verification
AuditLogSchema.statics.verifyChain = async function () {
  const entries = await this.find().sort({ timestamp: 1, _id: 1 });
  
  if (entries.length === 0) {
    return {
      chainValid: true,
      valid: true,
      verifiedRecords: 0,
      totalRecords: 0,
      count: 0,
      headHash: GENESIS_HASH,
      message: 'Cryptographic ledger initialized at Genesis block with 0 records'
    };
  }

  let expectedPreviousHash = GENESIS_HASH;

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];

    if (entry.previousHash !== expectedPreviousHash) {
      return {
        chainValid: false,
        valid: false,
        verifiedRecords: i,
        brokenIndex: i,
        brokenId: entry._id,
        headHash: entry.previousHash,
        message: `Previous hash mismatch at record ${i}`,
        reason: `Previous hash mismatch at record ${i}: expected ${expectedPreviousHash}, found ${entry.previousHash}`
      };
    }

    const recalculatedHash = this.computeHash(
      entry.previousHash,
      entry.timestamp,
      entry.eventType,
      entry.username,
      entry.actionTaken,
      entry.riskScore,
      entry.details
    );

    if (recalculatedHash !== entry.hash) {
      return {
        chainValid: false,
        valid: false,
        verifiedRecords: i,
        brokenIndex: i,
        brokenId: entry._id,
        headHash: entry.hash,
        message: `Hash mismatch at record ${i}`,
        reason: `Hash mismatch at record ${i}: recalculated ${recalculatedHash}, stored ${entry.hash}`
      };
    }

    expectedPreviousHash = entry.hash;
  }

  const headHash = entries[entries.length - 1].hash;

  return {
    chainValid: true,
    valid: true,
    verifiedRecords: entries.length,
    totalRecords: entries.length,
    count: entries.length,
    headHash,
    message: `Chain verified successfully across ${entries.length} immutable records from Genesis to Head`
  };
};

module.exports = mongoose.model('AuditLog', AuditLogSchema);
