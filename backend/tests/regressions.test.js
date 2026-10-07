const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const jwt = require('jsonwebtoken');
const app = require('../src/server');
const env = require('../src/config/env');
const User = require('../src/models/User');
const Policy = require('../src/models/Policy');
const AuditLog = require('../src/models/AuditLog');
const Incident = require('../src/models/Incident');
const ai = require('../src/services/aiServiceClient');
const policy = require('../src/services/policyEngine');
const contract = require('../src/services/aiContract');
const { safeEntities, protectText } = require('../src/services/dlpOutput');
const user = { _id: '507f1f77bcf86cd799439011', username: 'test', role: 'Employee', isActive: true };
const server = app.listen(0, '127.0.0.1');
after(() => server.close());
async function post(path, body, authenticated = false) {
  if (!server.listening) await new Promise(resolve => server.once('listening', resolve));
  const response = await fetch(`http://127.0.0.1:${server.address().port}/api/v1/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(authenticated ? {
      Authorization: `Bearer ${jwt.sign({ userId: user._id, role: 'Administrator' }, env.JWT_SECRET)}`
    } : {}) },
    body: JSON.stringify(body)
  });
  return { status: response.status, body: await response.json() };
}

test('public registration cannot choose administrator', async t => {
  t.mock.method(User, 'findOne', async () => null);
  t.mock.method(User, 'hashPassword', async () => 'hash');
  t.mock.method(User.prototype, 'save', async function () { return this; });
  const result = await post('auth/register', { username: 'test', email: 'test@example.com', password: 'Password123!', role: 'Administrator' });
  assert.equal(result.status, 201);
  assert.equal(result.body.user.role, 'Employee');
});

test('malformed credentials return 400', async () => {
  assert.equal((await post('auth/login', { email: { $ne: null }, password: [] })).status, 400);
});

test('disabled accounts cannot use existing access tokens', async t => {
  t.mock.method(User, 'findById', async () => ({ ...user, isActive: false }));
  assert.equal((await post('security/scan-prompt', { prompt: 'hello' }, true)).status, 401);
});

test('DLP outage stops processing without returning plaintext', async t => {
  t.mock.method(User, 'findById', async () => user);
  t.mock.method(ai, 'scanDlp', async () => ({ success: false }));
  const result = await post('security/scan-prompt', { prompt: 'private data' }, true);
  assert.equal(result.status, 503);
  assert.ok(!JSON.stringify(result.body).includes('private data'));
});

test('DLP findings cannot downgrade BLOCK or ESCALATE', async t => {
  t.mock.method(AuditLog, 'logEvent', async () => ({ _id: user._id }));
  t.mock.method(Incident, 'create', async () => ({ _id: user._id }));
  for (const action of ['BLOCK', 'ESCALATE']) {
    const mock = t.mock.method(Policy, 'find', () => ({ sort: async () => [{ action, minRiskScore: 0, maxRiskScore: 1 }] }));
    const result = await policy.evaluatePolicy({ dlpFindings: [{}] });
    assert.equal(result.action, action);
    mock.mock.restore();
  }
});

test('missing policies block; explicit redaction overrides ALLOW', async t => {
  t.mock.method(AuditLog, 'logEvent', async () => ({ _id: user._id }));
  t.mock.method(Incident, 'create', async () => ({ _id: user._id }));
  let policies = [];
  t.mock.method(Policy, 'find', () => ({ sort: async () => policies }));
  assert.equal((await policy.evaluatePolicy({})).action, 'BLOCK');
  policies = [{ action: 'ALLOW', minRiskScore: 0, maxRiskScore: 1, requireDlpRedaction: true }];
  assert.equal((await policy.evaluatePolicy({})).action, 'REDACT');
  policies[0].requireDlpRedaction = false;
  assert.equal((await policy.evaluatePolicy({})).action, 'ALLOW');
});

test('BLOCK takes precedence over required redaction', async t => {
  t.mock.method(User, 'findById', async () => user);
  t.mock.method(ai, 'scanDlp', async () => ({ success: true, data: { entities: [], mappings: [], redacted_text: 'still sensitive', sensitivity_score: 0, has_sensitive_data: false } }));
  t.mock.method(ai, 'classifyNlp', async () => ({ success: true, data: { social_engineering_score: 0, threats_detected: [] } }));
  t.mock.method(policy, 'evaluatePolicy', async () => ({ action: 'BLOCK', requireDlpRedaction: true }));
  const result = await post('security/scan-prompt', { prompt: 'private data' }, true);
  assert.equal(result.status, 200);
  assert.match(result.body.data.processedPrompt, /^\[BLOCKED/);
});

test('concurrent audit appends form one verifiable chain', async t => {
  t.mock.method(AuditLog, 'init', async () => {});
  const entries = [];
  t.mock.method(AuditLog, 'findOne', () => ({ sort: async () => entries.at(-1) }));
  t.mock.method(AuditLog, 'create', async entry => { await new Promise(resolve => setImmediate(resolve)); entries.push(entry); return entry; });
  t.mock.method(AuditLog, 'find', () => ({ sort: async () => entries }));
  await Promise.all(Array.from({ length: 20 }, () => AuditLog.logEvent({ eventType: 'DLP_SCAN' })));
  assert.equal((await AuditLog.verifyChain()).valid, true);
  assert.equal(entries.length, 20);
});

test('missing AI results cannot be successful, and output removes matched plaintext', async t => {
  t.mock.method(User, 'findById', async () => user);
  t.mock.method(ai, 'scanDlp', async () => ({ success: true, data: {} }));
  assert.equal((await post('security/scan-prompt', { prompt: 'private data' }, true)).status, 503);
  assert.equal(contract.audio({}), false);
  assert.equal(contract.audio({ voice_deepfake: { success: false } }), false);
  const dlp = { entities: [{ entity_type: 'KEY', text: 'SECRET' }], mappings: [], redacted_text: '<TOKEN>' };
  assert.equal(protectText('SECRET', dlp), '<TOKEN>');
  assert.ok(!JSON.stringify(safeEntities(dlp.entities)).includes('SECRET'));
});

test('legacy audit hashes verify; v2 detects identity/details tampering and retries competing append', async t => {
  t.mock.method(AuditLog, 'init', async () => {});
  const legacy = { timestamp: new Date(0), previousHash: '0'.repeat(64), eventType: 'DLP_SCAN',
    username: 'legacy', actionTaken: 'INFO', riskScore: 0, details: {} };
  legacy.hash = AuditLog.computeEntryHash(legacy);
  const entries = [legacy];
  t.mock.method(AuditLog, 'findOne', () => ({ sort: async () => entries.at(-1) }));
  t.mock.method(AuditLog, 'find', () => ({ sort: async () => entries }));
  let competingWrite = true;
  t.mock.method(AuditLog, 'create', async entry => {
    if (competingWrite) { competingWrite = false; entries.push(entry); throw Object.assign(new Error('duplicate edge'), { code: 11000 }); }
    entries.push(entry); return entry;
  });
  await AuditLog.logEvent({ eventType: 'DLP_SCAN', details: { safe: 'metadata' } });
  assert.equal(entries.length, 3);
  assert.equal((await AuditLog.verifyChain()).valid, true);
  for (const [field, value] of Object.entries({ userId: user._id, userRole: 'Administrator', ipAddress: 'changed', riskLevel: 'HIGH', details: { changed: true } })) {
    const previous = entries[2][field]; entries[2][field] = value;
    assert.equal((await AuditLog.verifyChain()).valid, false, field);
    entries[2][field] = previous;
  }
});

test('expired refresh tokens and inactive refresh accounts are rejected', async t => {
  const expired = jwt.sign({ userId: user._id }, env.JWT_REFRESH_SECRET, { expiresIn: -1 });
  assert.equal((await post('auth/refresh', { refreshToken: expired })).status, 401);
  const token = jwt.sign({ userId: user._id }, env.JWT_REFRESH_SECRET);
  t.mock.method(User, 'findById', () => ({ select: async () => ({ ...user, isActive: false, refreshToken: token }) }));
  assert.equal((await post('auth/refresh', { refreshToken: token })).status, 401);
});
const tokens = require('../src/services/tokenService');
test('prompt mapping writes finish sequentially before classification and stop on failure', async t => {
  t.mock.method(User, 'findById', async () => user);
  const mappings = ['first', 'second'].map(token_id => ({ token_id, entity_type: 'KEY', original_value: 'private' }));
  t.mock.method(ai, 'scanDlp', async () => ({ success: true, data: { mappings, entities: [], sensitivity_score: 0, redacted_text: '<TOKEN>', has_sensitive_data: true } }));
  const events = [];
  let fail = false;
  t.mock.method(tokens, 'saveTokenMapping', async value => {
    events.push(value);
    await new Promise(resolve => setImmediate(resolve));
    if (fail) throw new Error('storage failure');
    events.push('stored');
  });
  t.mock.method(ai, 'classifyNlp', async () => { events.push('classify'); return { success: false }; });
  assert.equal((await post('security/scan-prompt', { prompt: 'private' }, true)).status, 503);
  assert.deepEqual(events, [
    { tokenId: 'first', entityType: 'KEY', plaintextValue: 'private', userId: user._id }, 'stored',
    { tokenId: 'second', entityType: 'KEY', plaintextValue: 'private', userId: user._id }, 'stored', 'classify'
  ]);
  events.length = 0;
  fail = true;
  const response = await post('security/scan-prompt', { prompt: 'private' }, true);
  assert.equal(response.status, 500);
  assert.equal(events.length, 1);
  assert.equal(response.body.error, 'Failed to process prompt security scan: ');
});
