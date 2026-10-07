// EASP User Schema - Phase 1
// Implements bcrypt password hashing (>= 12 rounds), never persists or logs plaintext passwords.

const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const SALT_ROUNDS = 12;

const UserSchema = new mongoose.Schema({
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    minlength: 3,
    maxlength: 50
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true,
    match: [/^\S+@\S+\.\S+$/, 'Invalid email address format']
  },
  passwordHash: {
    type: String,
    required: true,
    select: false // Never returned in default find queries
  },
  role: {
    type: String,
    required: true,
    enum: ['Employee', 'Analyst', 'Administrator'],
    default: 'Employee'
  },
  isActive: {
    type: Boolean,
    default: true
  },
  refreshToken: {
    type: String,
    select: false
  },
  lastLoginAt: {
    type: Date
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

// Compare candidate password against stored bcrypt hash
UserSchema.methods.comparePassword = async function (candidatePassword) {
  if (!this.passwordHash) {
    throw new Error('passwordHash is required on model instance to compare');
  }
  return bcrypt.compare(candidatePassword, this.passwordHash);
};

// Static helper to hash passwords with >=12 rounds
UserSchema.statics.hashPassword = async function (plainPassword) {
  return bcrypt.hash(plainPassword, SALT_ROUNDS);
};

// Strip sensitive fields when serializing to JSON
UserSchema.methods.toJSON = function () {
  const obj = this.toObject();
  delete obj.passwordHash;
  delete obj.refreshToken;
  delete obj.__v;
  return obj;
};

module.exports = mongoose.model('User', UserSchema);
