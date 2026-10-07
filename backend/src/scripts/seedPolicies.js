// EASP Seed Policies Script - Phase 5 (T-P05-028 / T-P05-031)
// Populates baseline policy engine rules matching Chapter 1 & Task Book thresholds.

const mongoose = require('mongoose');
const env = require('../config/env');
const Policy = require('../models/Policy');

const defaultPolicies = [
  {
    name: 'High Risk Block Policy',
    description: 'Immediately blocks requests with fused risk score >= 0.70 or critical credential leakage',
    targetRole: 'All',
    minRiskScore: 0.70,
    maxRiskScore: 1.00,
    action: 'BLOCK',
    requireDlpRedaction: true,
    priority: 10,
    isActive: true
  },
  {
    name: 'Medium Risk Redact & Alert Policy',
    description: 'Applies reversible AES-256 token redaction for risk scores between 0.40 and 0.69',
    targetRole: 'All',
    minRiskScore: 0.40,
    maxRiskScore: 0.6999,
    action: 'REDACT',
    requireDlpRedaction: true,
    priority: 20,
    isActive: true
  },
  {
    name: 'Low Risk Allow Policy',
    description: 'Permits requests with fused risk score < 0.40 to proceed without alteration',
    targetRole: 'All',
    minRiskScore: 0.00,
    maxRiskScore: 0.3999,
    action: 'ALLOW',
    requireDlpRedaction: false,
    priority: 30,
    isActive: true
  },
  {
    name: 'Employee Strict Redaction Override',
    description: 'Forces DLP redaction on any Employee prompt containing detected PII, even at low risk',
    targetRole: 'Employee',
    minRiskScore: 0.10,
    maxRiskScore: 0.3999,
    action: 'REDACT',
    requireDlpRedaction: true,
    priority: 15,
    isActive: true
  }
];

async function seedPolicies() {
  console.log('[Seed] Connecting to MongoDB at:', env.MONGO_URI);
  await mongoose.connect(env.MONGO_URI);

  console.log('[Seed] Seeding Policy Rules...');
  for (const p of defaultPolicies) {
    await Policy.findOneAndUpdate({ name: p.name }, p, { upsert: true, new: true });
    console.log(`  -> Policy: ${p.name} [${p.action}]`);
  }

  console.log('[Seed] Policies seeded successfully.');
}

if (require.main === module) {
  seedPolicies()
    .then(async () => {
      await mongoose.disconnect();
      process.exit(0);
    })
    .catch((err) => {
      console.error('[Policy Seed Error]:', err);
      process.exit(1);
    });
}

module.exports = { seedPolicies };
