// EASP Token Mapping Schema - Phase 4 (T-P04-024 / T-P04-027)
// Stores reversible encrypted sensitive values with mandatory MongoDB TTL expiration.
// Uses AES-256-GCM encryption with randomized IVs and authentication tags.

const mongoose = require('mongoose');
const crypto = require('crypto');
const env = require('../config/env');

const ALGORITHM = 'aes-256-gcm';
const DEFAULT_TTL_SECONDS = 3600 * 24; // 24 hours default TTL

const TokenMappingSchema = new mongoose.Schema({
  tokenId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  entityType: {
    type: String,
    required: true
  },
  encryptedValue: {
    type: String,
    required: true
  },
  iv: {
    type: String,
    required: true
  },
  authTag: {
    type: String,
    required: true
  },
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  expiresAt: {
    type: Date,
    required: true,
    index: { expires: 0 } // MongoDB TTL Index: documents expire exactly at expiresAt
  }
});

// Static helper to encrypt a plaintext value using AES-256-GCM
TokenMappingSchema.statics.encryptValue = function (plaintext) {
  const key = Buffer.from(env.ENCRYPTION_SECRET_KEY, 'hex');
  if (key.length !== 32) {
    throw new Error('ENCRYPTION_SECRET_KEY must be exactly 32 bytes (64 hex characters)');
  }

  const iv = crypto.randomBytes(12); // 96-bit IV for GCM
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);

  let encrypted = cipher.update(plaintext, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const authTag = cipher.getAuthTag().toString('hex');

  return {
    encryptedValue: encrypted,
    iv: iv.toString('hex'),
    authTag
  };
};

// Instance method to decrypt the stored encrypted value using AES-256-GCM
TokenMappingSchema.methods.decryptValue = function () {
  const key = Buffer.from(env.ENCRYPTION_SECRET_KEY, 'hex');
  const iv = Buffer.from(this.iv, 'hex');
  const authTag = Buffer.from(this.authTag, 'hex');

  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(this.encryptedValue, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
};

module.exports = mongoose.model('TokenMapping', TokenMappingSchema);
