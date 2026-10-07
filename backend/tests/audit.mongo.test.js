// Opt-in database boundary check. Never uses MONGO_URI or the application database.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const mongoose = require('mongoose');
const AuditLog = require('../src/models/AuditLog');

test('MongoDB index serializes independent audit writers and preserves legacy history', async () => {
  const uri = process.env.TEST_MONGO_URI;
  assert.ok(uri && new URL(uri).pathname.endsWith('_test'), 'TEST_MONGO_URI must name a dedicated _test database');
  await mongoose.connect(uri, { serverSelectionTimeoutMS: 5000 });
  try {
    assert.equal(await AuditLog.countDocuments(), 0, 'Use a fresh dedicated test database');
    await AuditLog.init();
    const entry = { timestamp: new Date(0), previousHash: '0'.repeat(64), eventType: 'DLP_SCAN',
      username: 'legacy', actionTaken: 'INFO', riskScore: 0, details: {} };
    entry.hash = AuditLog.computeEntryHash(entry);
    await AuditLog.create(entry);
    const code = `const m=require('mongoose'), A=require('./src/models/AuditLog');
      (async()=>{await m.connect(process.env.TEST_MONGO_URI);for(let i=0;i<6;i++)await A.logEvent({eventType:'DLP_SCAN'});await m.disconnect()})().catch(()=>process.exit(1));`;
    const writer = () => new Promise((resolve, reject) => {
      const child = spawn(process.execPath, ['-e', code], { cwd: require('node:path').resolve(__dirname, '..'), env: process.env, stdio: 'ignore' });
      child.on('error', reject); child.on('exit', code => code === 0 ? resolve() : reject(new Error('Audit worker failed')));
    });
    await Promise.all([writer(), writer()]);
    const result = await AuditLog.verifyChain();
    assert.equal(result.valid, true); assert.equal(result.totalRecords, 13);
    const current = await AuditLog.findOne({ hashVersion: 2 });
    // Raw collection update simulates database tampering, bypassing application immutability.
    await AuditLog.collection.updateOne({ _id: current._id }, { $set: { userRole: 'tampered' } });
    assert.equal((await AuditLog.verifyChain()).valid, false);
  } finally { await mongoose.disconnect(); }
});
