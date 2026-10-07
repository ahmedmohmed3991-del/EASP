// EASP Audit Log Schema - Phase 5 (T-P05-029 / T-P05-030)
// Implements append-only, tamper-evident cryptographic hash chaining (SHA-256).
// No update or delete operations are exposed on this collection.

const mongoose = require('mongoose');
const crypto = require('crypto');

const GENESIS_HASH = '0'.repeat(64);
// Serialize appends in this API process so concurrent requests cannot fork the chain.
let appendQueue = Promise.resolve();

const AuditLogSchema = new mongoose.Schema({
  hashVersion: { type: Number, default: 1, immutable: true },
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

// Only new-format edges are unique; historical data is neither rewritten nor reindexed as unique.
AuditLogSchema.index({ previousHash: 1 }, { unique: true, partialFilterExpression: { hashVersion: 2 } });
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    if (value.toJSON) return canonical(value.toJSON());
    return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  }
  return value;
}
AuditLogSchema.statics.computeEntryHash = function (entry) {
  if ((entry.hashVersion ?? 1) === 1) return this.computeHash(entry.previousHash, entry.timestamp,
    entry.eventType, entry.username, entry.actionTaken, entry.riskScore, entry.details);
  if (entry.hashVersion !== 2) throw new Error('Unsupported audit hash version');
  const content = { hashVersion: 2, previousHash: entry.previousHash,
    timestamp: new Date(entry.timestamp).toISOString(), eventType: entry.eventType,
    userId: entry.userId ? String(entry.userId) : null, username: entry.username,
    userRole: entry.userRole, ipAddress: entry.ipAddress, actionTaken: entry.actionTaken,
    riskScore: entry.riskScore, riskLevel: entry.riskLevel, details: entry.details };
  return crypto.createHash('sha256').update(JSON.stringify(canonical(content))).digest('hex');
};

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
  const append = appendQueue.then(async () => {
    await this.init(); // Unique edge index must exist before accepting writes.
    for (let attempt = 0; attempt < 8; attempt++) {
      const last = await this.findOne().sort({ timestamp: -1, _id: -1 });
      const entry = { hashVersion: 2, previousHash: last ? last.hash : GENESIS_HASH,
        timestamp: new Date(Math.max(Date.now(), last ? new Date(last.timestamp).getTime() + 1 : 0)),
        eventType, userId, username, userRole, ipAddress, actionTaken, riskScore, riskLevel, details };
      // Match the persisted Mixed representation (e.g. omit undefined fields) before hashing.
      entry.details = JSON.parse(JSON.stringify(details || {}));
      entry.hash = this.computeEntryHash(entry);
      try { return await this.create(entry); }
      catch (error) { if (error.code !== 11000 || attempt === 7) throw error; }
    }
  });
  appendQueue = append.catch(() => {});
  return append;
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

    const version = entry.hashVersion ?? 1;
    if (![1, 2].includes(version) || (i > 0 && (entries[i - 1].hashVersion ?? 1) === 2 && version === 1)) {
      return { chainValid: false, valid: false, brokenIndex: i, message: 'Invalid audit hash version transition' };
    }
    const recalculatedHash = this.computeEntryHash(entry);

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
