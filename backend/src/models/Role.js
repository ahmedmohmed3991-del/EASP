// EASP Role Schema - Phase 1
// Defines standard role definitions and allowed permission sets.

const mongoose = require('mongoose');

const RoleSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    unique: true,
    enum: ['Employee', 'Analyst', 'Administrator']
  },
  description: {
    type: String,
    required: true
  },
  permissions: [{
    type: String
  }],
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Role', RoleSchema);
