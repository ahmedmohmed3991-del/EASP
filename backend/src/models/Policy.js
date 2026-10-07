// EASP Policy Rule Schema - Phase 5 (T-P05-028 / T-P05-031)
// Defines policy enforcement rules that translate fused risk scores and DLP categories
// into enforcement actions: ALLOW, REDACT, ESCALATE, or BLOCK.

const mongoose = require('mongoose');

const PolicySchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    unique: true,
    trim: true
  },
  description: {
    type: String,
    required: true
  },
  targetRole: {
    type: String,
    enum: ['All', 'Employee', 'Analyst', 'Administrator'],
    default: 'All'
  },
  minRiskScore: {
    type: Number,
    required: true,
    min: 0.0,
    max: 1.0,
    default: 0.0
  },
  maxRiskScore: {
    type: Number,
    required: true,
    min: 0.0,
    max: 1.0,
    default: 1.0
  },
  action: {
    type: String,
    required: true,
    enum: ['ALLOW', 'REDACT', 'ESCALATE', 'BLOCK']
  },
  requireDlpRedaction: {
    type: Boolean,
    default: true
  },
  priority: {
    type: Number,
    default: 100 // Lower number = higher evaluation priority
  },
  isActive: {
    type: Boolean,
    default: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Policy', PolicySchema);
