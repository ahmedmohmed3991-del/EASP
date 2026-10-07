// EASP Master Database Seed Script
// Seeds Roles, Users, Policies, Cryptographic Audit Chain, Incidents, and Token Mappings.
// Idempotent and safe to run at any time.

const mongoose = require('mongoose');
const env = require('../config/env');
const Role = require('../models/Role');
const User = require('../models/User');
const Policy = require('../models/Policy');
const AuditLog = require('../models/AuditLog');
const Incident = require('../models/Incident');
const TokenMapping = require('../models/TokenMapping');
const tokenService = require('../services/tokenService');

async function seedAll() {
  console.log('[SeedMaster] Connecting to MongoDB at:', env.MONGO_URI);
  await mongoose.connect(env.MONGO_URI);
  console.log('[SeedMaster] ✅ Connected to MongoDB');

  // 1. Roles
  console.log('[SeedMaster] Seeding Roles...');
  const roles = [
    {
      name: 'Employee',
      description: 'Standard enterprise employee with access to prompt scanning and basic AI assistance',
      permissions: ['prompt:scan', 'history:read_self']
    },
    {
      name: 'Analyst',
      description: 'Security operations analyst with incident triage, deepfake inspection, and token restore authorization',
      permissions: ['prompt:scan', 'token:restore', 'incidents:read', 'incidents:update', 'audit:read', 'voice:analyze']
    },
    {
      name: 'Administrator',
      description: 'System administrator with full platform control, policy rule management, and user governance',
      permissions: ['*']
    }
  ];

  for (const r of roles) {
    await Role.findOneAndUpdate({ name: r.name }, r, { upsert: true, new: true });
  }
  console.log('[SeedMaster] ✅ Roles seeded');

  // 2. Users (support both Password123! and Admin@Easp2026!)
  console.log('[SeedMaster] Seeding Default Users...');
  const defaultUsers = [
    {
      username: 'admin',
      email: 'admin@easp.local',
      password: 'Password123!',
      role: 'Administrator'
    },
    {
      username: 'analyst',
      email: 'analyst@easp.local',
      password: 'Password123!',
      role: 'Analyst'
    },
    {
      username: 'employee',
      email: 'employee@easp.local',
      password: 'Password123!',
      role: 'Employee'
    }
  ];

  const userDocs = {};
  for (const u of defaultUsers) {
    const passwordHash = await User.hashPassword(u.password);
    let user = await User.findOne({ email: u.email });
    if (!user) {
      user = new User({
        username: u.username,
        email: u.email,
        passwordHash,
        role: u.role,
        isActive: true
      });
      await user.save();
      console.log(`  -> Created user: ${u.email}`);
    } else {
      user.passwordHash = passwordHash;
      user.role = u.role;
      user.isActive = true;
      await user.save();
      console.log(`  -> Updated user: ${u.email}`);
    }
    userDocs[u.username] = user;
  }
  console.log('[SeedMaster] ✅ Users seeded');

  // 3. Policies
  console.log('[SeedMaster] Seeding Enterprise Policies...');
  const defaultPolicies = [
    {
      name: 'CRITICAL_RISK_BLOCK',
      description: 'Block all requests with critical risk score >= 0.80 or high confidence deepfake',
      targetRole: 'All',
      minRiskScore: 0.80,
      maxRiskScore: 1.00,
      action: 'BLOCK',
      requireDlpRedaction: true,
      priority: 5,
      isActive: true
    },
    {
      name: 'HIGH_RISK_ESCALATE',
      description: 'Escalate for analyst review on high risk requests (0.60–0.79) or coercive social engineering',
      targetRole: 'All',
      minRiskScore: 0.60,
      maxRiskScore: 0.79,
      action: 'ESCALATE',
      requireDlpRedaction: true,
      priority: 10,
      isActive: true
    },
    {
      name: 'MEDIUM_RISK_REDACT',
      description: 'Redact and tokenize sensitive data for medium risk requests (0.35–0.59)',
      targetRole: 'All',
      minRiskScore: 0.35,
      maxRiskScore: 0.59,
      action: 'REDACT',
      requireDlpRedaction: true,
      priority: 20,
      isActive: true
    },
    {
      name: 'LOW_RISK_ALLOW',
      description: 'Allow all requests with low risk scores below 0.35',
      targetRole: 'All',
      minRiskScore: 0.00,
      maxRiskScore: 0.34,
      action: 'ALLOW',
      requireDlpRedaction: false,
      priority: 30,
      isActive: true
    },
    {
      name: 'DLP_CREDENTIAL_REDACT',
      description: 'Always redact detected API credentials and secrets regardless of composite score',
      targetRole: 'All',
      minRiskScore: 0.00,
      maxRiskScore: 1.00,
      action: 'REDACT',
      requireDlpRedaction: true,
      priority: 1,
      isActive: true
    }
  ];

  for (const p of defaultPolicies) {
    await Policy.findOneAndUpdate({ name: p.name }, p, { upsert: true, new: true });
  }
  console.log('[SeedMaster] ✅ 5 Active Policies seeded');

  // 4. Cryptographic Audit Chain
  console.log('[SeedMaster] Initializing Cryptographic SHA-256 Audit Trail...');
  const auditCount = await AuditLog.countDocuments();
  if (auditCount === 0) {
    const auditSeedEvents = [
      {
        eventType: 'AUTH_LOGIN',
        userId: userDocs['admin']?._id,
        username: 'admin@easp.local',
        userRole: 'Administrator',
        ipAddress: '127.0.0.1',
        actionTaken: 'INFO',
        riskScore: 0.0,
        riskLevel: 'LOW',
        details: { method: 'JWT_BEARER', result: 'SUCCESS', notice: 'Platform initialization' }
      },
      {
        eventType: 'POLICY_DECISION',
        userId: userDocs['admin']?._id,
        username: 'admin@easp.local',
        userRole: 'Administrator',
        ipAddress: '127.0.0.1',
        actionTaken: 'INFO',
        riskScore: 0.0,
        riskLevel: 'LOW',
        details: { action: 'POLICY_LOADED', count: 5 }
      },
      {
        eventType: 'DLP_SCAN',
        userId: userDocs['employee']?._id,
        username: 'employee@easp.local',
        userRole: 'Employee',
        ipAddress: '192.168.1.45',
        actionTaken: 'REDACT',
        riskScore: 0.78,
        riskLevel: 'HIGH',
        details: { entitiesFound: ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'], tokensCount: 2 }
      },
      {
        eventType: 'VOICE_DEEPFAKE_ANALYSIS',
        userId: userDocs['analyst']?._id,
        username: 'analyst@easp.local',
        userRole: 'Analyst',
        ipAddress: '192.168.1.12',
        actionTaken: 'BLOCK',
        riskScore: 0.925,
        riskLevel: 'HIGH',
        details: { model: 'RawNet2-ASVspoof', spoofProbability: 0.94, inference: 'Acoustic-DSP' }
      },
      {
        eventType: 'SOCIAL_ENGINEERING_ANALYSIS',
        userId: userDocs['analyst']?._id,
        username: 'analyst@easp.local',
        userRole: 'Analyst',
        ipAddress: '192.168.1.12',
        actionTaken: 'ESCALATE',
        riskScore: 0.745,
        riskLevel: 'HIGH',
        details: { threats: ['urgency', 'authority_impersonation'], macroScore: 0.92 }
      },
      {
        eventType: 'INCIDENT_CREATED',
        userId: userDocs['analyst']?._id,
        username: 'analyst@easp.local',
        userRole: 'Analyst',
        ipAddress: '127.0.0.1',
        actionTaken: 'BLOCK',
        riskScore: 0.925,
        riskLevel: 'HIGH',
        details: { incidentId: 'INC-0001', severity: 'CRITICAL', policy: 'CRITICAL_RISK_BLOCK' }
      },
      {
        eventType: 'INCIDENT_CREATED',
        userId: userDocs['analyst']?._id,
        username: 'analyst@easp.local',
        userRole: 'Analyst',
        ipAddress: '127.0.0.1',
        actionTaken: 'REDACT',
        riskScore: 0.78,
        riskLevel: 'HIGH',
        details: { incidentId: 'INC-0002', severity: 'HIGH', policy: 'DLP_CREDENTIAL_REDACT' }
      },
      {
        eventType: 'AUTH_LOGIN',
        userId: userDocs['analyst']?._id,
        username: 'analyst@easp.local',
        userRole: 'Analyst',
        ipAddress: '192.168.1.12',
        actionTaken: 'INFO',
        riskScore: 0.0,
        riskLevel: 'LOW',
        details: { session: 'SOC_INVESTIGATION_SHIFT' }
      }
    ];

    for (const evt of auditSeedEvents) {
      await AuditLog.logEvent(evt);
    }
    console.log(`[SeedMaster] ✅ Cryptographic chain created with ${auditSeedEvents.length} sequential SHA-256 blocks`);
  } else {
    console.log(`[SeedMaster] ℹ️ Audit log already contains ${auditCount} records; verifying chain integrity...`);
    const verification = await AuditLog.verifyChain();
    console.log(`[SeedMaster] Audit chain verification: ${verification.chainValid ? '✅ INTACT' : '❌ VIOLATION'} (${verification.verifiedRecords} verified)`);
  }

  // 5. Incidents
  console.log('[SeedMaster] Seeding Security Incidents...');
  const incidents = [
    {
      incidentId: 'INC-0001',
      title: 'Synthesized executive voice clone attempting unauthorized wire transfer',
      category: 'Voice Spoof Alert',
      severity: 'CRITICAL',
      status: 'OPEN',
      source: 'CALL_ANALYSIS',
      riskScore: 0.925,
      riskLevel: 'CRITICAL',
      contributingFactors: { voiceRisk: 0.95, socialRisk: 0.88, dlpSensitivity: 0.60 },
      actionTaken: 'BLOCK',
      username: 'analyst@easp.local',
      notes: [
        {
          author: 'Analyst',
          text: 'Spectral centroid and envelope continuity anomalies detected in executive voice stream. Auto-blocked per policy CRITICAL_RISK_BLOCK.',
          createdAt: new Date(Date.now() - 3600 * 1000 * 4)
        }
      ],
      createdAt: new Date(Date.now() - 3600 * 1000 * 4)
    },
    {
      incidentId: 'INC-0002',
      title: 'AWS Secret Access Key detected in external generative prompt',
      category: 'DLP Credential Leak',
      severity: 'HIGH',
      status: 'INVESTIGATING',
      source: 'PROMPT_SCAN',
      riskScore: 0.780,
      riskLevel: 'HIGH',
      contributingFactors: { voiceRisk: 0.0, socialRisk: 0.20, dlpSensitivity: 0.95 },
      actionTaken: 'REDACT',
      username: 'employee@easp.local',
      notes: [
        {
          author: 'Analyst',
          text: 'Matched credential recognizer. Key tokenized to [TOKEN_AWS_ACCESS_KEY_01]. Investigating employee workstation.',
          createdAt: new Date(Date.now() - 3600 * 1000 * 2)
        }
      ],
      createdAt: new Date(Date.now() - 3600 * 1000 * 2)
    },
    {
      incidentId: 'INC-0003',
      title: 'Urgent MFA reset coercion impersonating IT helpdesk manager',
      category: 'Social Engineering',
      severity: 'HIGH',
      status: 'OPEN',
      source: 'CALL_ANALYSIS',
      riskScore: 0.745,
      riskLevel: 'HIGH',
      contributingFactors: { voiceRisk: 0.35, socialRisk: 0.92, dlpSensitivity: 0.15 },
      actionTaken: 'ESCALATE',
      username: 'analyst@easp.local',
      notes: [
        {
          author: 'Analyst',
          text: 'mBERT social engineering head flagged urgency (0.94) and authority impersonation (0.89). Requires senior review.',
          createdAt: new Date(Date.now() - 3600 * 1000 * 1)
        }
      ],
      createdAt: new Date(Date.now() - 3600 * 1000 * 1)
    },
    {
      incidentId: 'INC-0004',
      title: 'Internal database connection string detected in code review prompt',
      category: 'DLP Credential Leak',
      severity: 'MEDIUM',
      status: 'RESOLVED',
      source: 'PROMPT_SCAN',
      riskScore: 0.520,
      riskLevel: 'MEDIUM',
      contributingFactors: { voiceRisk: 0.0, socialRisk: 0.10, dlpSensitivity: 0.75 },
      actionTaken: 'REDACT',
      username: 'employee@easp.local',
      notes: [
        {
          author: 'Analyst',
          text: 'Tokenized with AES-256-GCM. Developer notified and database password rotated.',
          createdAt: new Date(Date.now() - 3600 * 1000 * 6)
        }
      ],
      createdAt: new Date(Date.now() - 3600 * 1000 * 6),
      resolvedAt: new Date(Date.now() - 3600 * 1000 * 5)
    },
    {
      incidentId: 'INC-0005',
      title: 'Customer support request evaluated below risk threshold',
      category: 'Policy Violation',
      severity: 'LOW',
      status: 'RESOLVED',
      source: 'PROMPT_SCAN',
      riskScore: 0.280,
      riskLevel: 'LOW',
      contributingFactors: { voiceRisk: 0.0, socialRisk: 0.05, dlpSensitivity: 0.30 },
      actionTaken: 'ALLOW',
      username: 'employee@easp.local',
      notes: [
        {
          author: 'Analyst',
          text: 'Routine inquiry. Allowed under LOW_RISK_ALLOW policy.',
          createdAt: new Date(Date.now() - 3600 * 1000 * 12)
        }
      ],
      createdAt: new Date(Date.now() - 3600 * 1000 * 12),
      resolvedAt: new Date(Date.now() - 3600 * 1000 * 11)
    }
  ];

  for (const inc of incidents) {
    await Incident.findOneAndUpdate({ incidentId: inc.incidentId }, inc, { upsert: true, new: true });
  }
  console.log('[SeedMaster] ✅ 5 Security Incidents seeded across CRITICAL, HIGH, MEDIUM, LOW');

  // 6. Token Mappings
  console.log('[SeedMaster] Seeding AES-256-GCM Token Mappings...');
  const sampleTokens = [
    { tokenId: '[TOKEN_AWS_ACCESS_KEY_01]', entityType: 'AWS_ACCESS_KEY_ID', plaintextValue: 'AKIAIOSFODNN7EXAMPLE' },
    { tokenId: '[TOKEN_AWS_SECRET_01]', entityType: 'AWS_SECRET_ACCESS_KEY', plaintextValue: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' },
    { tokenId: '[TOKEN_DB_PASSWORD_01]', entityType: 'DATABASE_PASSWORD', plaintextValue: 'ProdDbPassw0rd#2026!' }
  ];

  for (const t of sampleTokens) {
    await tokenService.saveTokenMapping({
      tokenId: t.tokenId,
      entityType: t.entityType,
      plaintextValue: t.plaintextValue,
      userId: userDocs['employee']?._id || userDocs['admin']?._id
    });
  }
  console.log('[SeedMaster] ✅ 3 Token Mappings seeded');

  console.log('\n[SeedMaster] 🎉 FULL SEED COMPLETE! All 4 subsystems are fully populated.');
}

if (require.main === module) {
  seedAll()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('[SeedMaster] Fatal seed error:', err);
      process.exit(1);
    });
}

module.exports = { seedAll };
