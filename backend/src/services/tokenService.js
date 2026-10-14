// EASP Token Mapping & Restoration Service - Phase 4 (T-P04-024 / T-P04-027)
// Manages reversible AES-256 token mappings, TTL expiration, and fail-closed RBAC-gated restore.

const TokenMapping = require('../models/TokenMapping');
const AuditLog = require('../models/AuditLog');

const DEFAULT_TTL_SECONDS = 3600 * 24; // 24 hours

// Save or refresh an encrypted token mapping
async function saveTokenMapping({ tokenId, entityType, plaintextValue, userId, ttlSeconds = DEFAULT_TTL_SECONDS }) {
  const { encryptedValue, iv, authTag } = TokenMapping.encryptValue(plaintextValue);
  const expiresAt = new Date(Date.now() + ttlSeconds * 1000);

  const mapping = await TokenMapping.findOneAndUpdate(
    { tokenId },
    {
      tokenId,
      entityType,
      encryptedValue,
      iv,
      authTag,
      userId,
      expiresAt
    },
    { upsert: true, new: true }
  );

  return mapping;
}

// Restore original sensitive value (strictly restricted to Analyst & Administrator)
async function restoreToken({ tokenId, user, ipAddress = 'unknown' }) {
  // Fail-closed authorization check
  if (!user || !['Analyst', 'Administrator'].includes(user.role)) {
    await AuditLog.logEvent({
      eventType: 'DLP_RESTORE',
      userId: user ? user.id : null,
      username: user ? user.username : 'anonymous',
      userRole: user ? user.role : 'None',
      ipAddress,
      actionTaken: 'BLOCK',
      riskScore: 0.85,
      riskLevel: 'HIGH',
      details: {
        tokenId,
        outcome: 'DENIED',
        reason: 'Insufficient permissions for token restoration'
      }
    });

    return {
      success: false,
      statusCode: 403,
      error: `Access forbidden: Role '${user ? user.role : 'None'}' is not authorized to restore sensitive values`
    };
  }

  const mapping = await TokenMapping.findOne({ tokenId });

  if (!mapping) {
    return {
      success: false,
      statusCode: 404,
      error: 'Token mapping not found or has expired'
    };
  }

  // Check TTL expiration
  if (new Date() > mapping.expiresAt) {
    await TokenMapping.deleteOne({ _id: mapping._id });
    return {
      success: false,
      statusCode: 410,
      error: 'Token mapping has expired and been purged'
    };
  }

  // Decrypt
  let originalValue;
  try {
    originalValue = mapping.decryptValue();
  } catch (err) {
    return {
      success: false,
      statusCode: 500,
      error: 'Decryption failed: cryptographic integrity error'
    };
  }

  // Audit log the restore event (IMPORTANT: NEVER LOG THE PLAINTEXT VALUE)
  await AuditLog.logEvent({
    eventType: 'DLP_RESTORE',
    userId: user.id,
    username: user.username,
    userRole: user.role,
    ipAddress,
    actionTaken: 'ALLOW',
    riskScore: 0.20,
    riskLevel: 'LOW',
    details: {
      tokenId,
      entityType: mapping.entityType,
      outcome: 'AUTHORIZED_RESTORE'
    }
  });

  return {
    success: true,
    statusCode: 200,
    tokenId,
    entityType: mapping.entityType,
    originalValue,
    expiresAt: mapping.expiresAt
  };
}

module.exports = { saveTokenMapping, restoreToken };
