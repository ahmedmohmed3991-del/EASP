// EASP Seed Script - Phase 1 (T-P01-010)
// Populates default Roles and initial test user accounts with bcrypt-hashed passwords.

const mongoose = require('mongoose');
const env = require('../config/env');
const Role = require('../models/Role');
const User = require('../models/User');

const defaultRoles = [
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

const defaultUsers = [
  {
    username: 'admin',
    email: 'admin@easp.local',
    password: 'Admin@Easp2026!',
    role: 'Administrator'
  },
  {
    username: 'analyst',
    email: 'analyst@easp.local',
    password: 'Analyst@Easp2026!',
    role: 'Analyst'
  },
  {
    username: 'employee',
    email: 'employee@easp.local',
    password: 'Employee@Easp2026!',
    role: 'Employee'
  }
];

async function seed() {
  console.log('[Seed] Connecting to MongoDB at:', env.MONGO_URI);
  await mongoose.connect(env.MONGO_URI);

  console.log('[Seed] Seeding Roles...');
  for (const r of defaultRoles) {
    await Role.findOneAndUpdate({ name: r.name }, r, { upsert: true, new: true });
    console.log(`  -> Role: ${r.name}`);
  }

  console.log('[Seed] Seeding Default Users...');
  for (const u of defaultUsers) {
    const existing = await User.findOne({ email: u.email });
    if (!existing) {
      const passwordHash = await User.hashPassword(u.password);
      await User.create({
        username: u.username,
        email: u.email,
        passwordHash,
        role: u.role
      });
      console.log(`  -> Created user: ${u.email} (${u.role})`);
    } else {
      console.log(`  -> User already exists: ${u.email} (${u.role})`);
    }
  }

  console.log('[Seed] Database initialization complete.');
}

if (require.main === module) {
  seed()
    .then(async () => {
      await mongoose.disconnect();
      process.exit(0);
    })
    .catch((err) => {
      console.error('[Seed Error]:', err);
      process.exit(1);
    });
}

module.exports = { seed };
