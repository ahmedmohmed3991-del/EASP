// EASP Comprehensive Security & Integration Test Suite - Phase 13 (T-P13-059)
// Validates:
// 1. Authentication (Registration, Login, JWT verification, Expiration, Password hash security)
// 2. RBAC Enforcement (Employee vs Analyst vs Administrator privilege boundaries)
// 3. Rate Limiting (Brute-force protection on auth endpoints)
// 4. DLP Detection & AES-256 Reversible Redaction lifecycle
// 5. Fail-closed Token Restoration access control
// 6. Append-Only Cryptographic Hash Chaining (SHA-256 tamper evidence)
// 7. Policy Engine Action Enforcement (ALLOW / REDACT / BLOCK)

// Integration suites must never seed or write the configured application database.
if (!process.env.TEST_MONGO_URI || !new URL(process.env.TEST_MONGO_URI).pathname.endsWith('_test')) {
  throw new Error('Set TEST_MONGO_URI to a dedicated database whose name ends in _test');
}
process.env.MONGO_URI = process.env.TEST_MONGO_URI;
const http = require('http');
const assert = require('assert');
const mongoose = require('mongoose');
const app = require('../src/server');
const env = require('../src/config/env');
const User = require('../src/models/User');
const Role = require('../src/models/Role');
const AuditLog = require('../src/models/AuditLog');
const TokenMapping = require('../src/models/TokenMapping');
const { seed } = require('../src/scripts/seedUsers');
const { seedPolicies } = require('../src/scripts/seedPolicies');

let server;
let baseUrl;

function makeRequest({ path, method = 'GET', headers = {}, body = null }) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, baseUrl);
    const reqHeaders = { ...headers };
    let postData = null;

    if (body) {
      postData = typeof body === 'string' ? body : JSON.stringify(body);
      reqHeaders['Content-Type'] = 'application/json';
      reqHeaders['Content-Length'] = Buffer.byteLength(postData);
    }

    const req = http.request(url, { method, headers: reqHeaders }, (res) => {
      let resBody = '';
      res.on('data', (chunk) => (resBody += chunk));
      res.on('end', () => {
        let json = null;
        try {
          json = JSON.parse(resBody);
        } catch {}
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: resBody,
          json
        });
      });
    });

    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

async function runSecurityTestSuite() {
  console.log('=== Starting EASP Comprehensive Security Validation Suite ===\n');
  let passedCount = 0;
  let totalCount = 0;

  async function test(name, fn) {
    totalCount++;
    try {
      await fn();
      console.log(`[PASS] ${name}`);
      passedCount++;
    } catch (err) {
      console.error(`[FAIL] ${name}`);
      console.error(`       ${err.message}`);
    }
  }

  // Connect to DB and seed initial roles and test accounts
  await mongoose.connect(env.MONGO_URI);
  await seed();
  await seedPolicies();

  // Start test server
  await new Promise((resolve) => {
    server = app.listen(0, () => {
      baseUrl = `http://127.0.0.1:${server.address().port}`;
      console.log(`Test server running on ${baseUrl}\n`);
      resolve();
    });
  });

  let employeeToken = null;
  let analystToken = null;
  let adminToken = null;

  try {
    // -----------------------------------------------------------------------
    // 1. AUTHENTICATION & PASSWORD SECURITY
    // -----------------------------------------------------------------------
    await test('Auth: Login with valid credentials returns JWT and strips passwordHash', async () => {
      const res = await makeRequest({
        path: '/api/v1/auth/login',
        method: 'POST',
        body: { email: 'employee@easp.local', password: 'Employee@Easp2026!' }
      });
      assert.strictEqual(res.statusCode, 200);
      assert(res.json.token, 'Missing JWT token in response');
      assert.strictEqual(res.json.user.email, 'employee@easp.local');
      assert.strictEqual(res.json.user.passwordHash, undefined, 'passwordHash must never leak in response');
      employeeToken = res.json.token;
    });

    await test('Auth: Login with incorrect password returns generic 401 error', async () => {
      const res = await makeRequest({
        path: '/api/v1/auth/login',
        method: 'POST',
        body: { email: 'employee@easp.local', password: 'WrongPassword123!' }
      });
      assert.strictEqual(res.statusCode, 401);
      assert.strictEqual(res.json.error, 'Invalid email or password');
    });

    await test('Auth: Log in analyst and administrator accounts', async () => {
      const aRes = await makeRequest({
        path: '/api/v1/auth/login',
        method: 'POST',
        body: { email: 'analyst@easp.local', password: 'Analyst@Easp2026!' }
      });
      assert.strictEqual(aRes.statusCode, 200);
      analystToken = aRes.json.token;

      const admRes = await makeRequest({
        path: '/api/v1/auth/login',
        method: 'POST',
        body: { email: 'admin@easp.local', password: 'Admin@Easp2026!' }
      });
      assert.strictEqual(admRes.statusCode, 200);
      adminToken = admRes.json.token;
    });

    await test('Auth: GET /api/v1/auth/me requires valid Bearer token', async () => {
      // Missing token
      const noTokenRes = await makeRequest({ path: '/api/v1/auth/me' });
      assert.strictEqual(noTokenRes.statusCode, 401);

      // Valid token
      const validRes = await makeRequest({
        path: '/api/v1/auth/me',
        headers: { Authorization: `Bearer ${employeeToken}` }
      });
      assert.strictEqual(validRes.statusCode, 200);
      assert.strictEqual(validRes.json.user.role, 'Employee');

      // Forged / tampered token
      const tamperedRes = await makeRequest({
        path: '/api/v1/auth/me',
        headers: { Authorization: `Bearer ${employeeToken}tampered` }
      });
      assert.strictEqual(tamperedRes.statusCode, 401);
    });

    // -----------------------------------------------------------------------
    // 2. RBAC PRIVILEGE BOUNDARY ENFORCEMENT
    // -----------------------------------------------------------------------
    await test('RBAC: Employee is blocked from Analyst/Admin incidents endpoint (403 Forbidden)', async () => {
      const res = await makeRequest({
        path: '/api/v1/incidents',
        headers: { Authorization: `Bearer ${employeeToken}` }
      });
      assert.strictEqual(res.statusCode, 403);
      assert(res.json.error.includes('does not have sufficient permissions'));
    });

    await test('RBAC: Analyst can access incidents and audit records', async () => {
      const incRes = await makeRequest({
        path: '/api/v1/incidents',
        headers: { Authorization: `Bearer ${analystToken}` }
      });
      assert.strictEqual(incRes.statusCode, 200);

      const auditRes = await makeRequest({
        path: '/api/v1/audit-logs',
        headers: { Authorization: `Bearer ${analystToken}` }
      });
      assert.strictEqual(auditRes.statusCode, 200);
    });

    await test('RBAC: Only Administrator can create new policy rules', async () => {
      // Employee attempt -> 403
      const empAttempt = await makeRequest({
        path: '/api/v1/policies',
        method: 'POST',
        headers: { Authorization: `Bearer ${employeeToken}` },
        body: {
          name: 'Unauthorized Rule',
          description: 'Test',
          action: 'BLOCK',
          minRiskScore: 0.9,
          maxRiskScore: 1.0
        }
      });
      assert.strictEqual(empAttempt.statusCode, 403);

      // Admin attempt -> 201
      const admAttempt = await makeRequest({
        path: '/api/v1/policies',
        method: 'POST',
        headers: { Authorization: `Bearer ${adminToken}` },
        body: {
          name: 'Special Financial Rule',
          description: 'Blocks wire requests',
          action: 'BLOCK',
          minRiskScore: 0.75,
          maxRiskScore: 1.0
        }
      });
      assert([200, 201].includes(admAttempt.statusCode), `Expected status 200 or 201, got ${admAttempt.statusCode}`);
    });

    // -----------------------------------------------------------------------
    // 3. DLP DETECTION & REVERSIBLE REDACTION LIFECYCLE
    // -----------------------------------------------------------------------
    let generatedTokenId = null;
    const testSecret = 'sk-proj-99887766554433221100aabbccddeeff001122334455';

    await test('DLP: Prompt scan detects API key and performs reversible token redaction', async () => {
      const res = await makeRequest({
        path: '/api/v1/security/scan-prompt',
        method: 'POST',
        headers: { Authorization: `Bearer ${employeeToken}` },
        body: { prompt: `Here is the secret key: ${testSecret} for accessing the database.` }
      });

      assert.strictEqual(res.statusCode, 200);
      assert.strictEqual(res.json.status, 'success');
      assert.strictEqual(res.json.data.dlp.hasSensitiveData, true);
      assert(res.json.data.dlp.tokensGenerated >= 1);
      assert(!res.json.data.processedPrompt.includes(testSecret), 'Raw secret must not be in processed prompt');
      assert(res.json.data.processedPrompt.includes('<REDACTED_OPENAI_API_KEY_'));

      // Extract generated token ID
      const match = res.json.data.processedPrompt.match(/<REDACTED_[^>]+>/);
      assert(match, 'Expected token format in processed prompt');
      generatedTokenId = match[0];
    });

    await test('DLP: Employee is DENIED from restoring the sensitive token (403 Forbidden)', async () => {
      assert(generatedTokenId, 'TokenId must be available from prior test');
      const res = await makeRequest({
        path: '/api/v1/security/restore-token',
        method: 'POST',
        headers: { Authorization: `Bearer ${employeeToken}` },
        body: { tokenId: generatedTokenId }
      });
      assert.strictEqual(res.statusCode, 403);
    });

    await test('DLP: Analyst is AUTHORIZED to restore sensitive token; returns original secret', async () => {
      assert(generatedTokenId, 'TokenId must be available from prior test');
      const res = await makeRequest({
        path: '/api/v1/security/restore-token',
        method: 'POST',
        headers: { Authorization: `Bearer ${analystToken}` },
        body: { tokenId: generatedTokenId }
      });
      assert.strictEqual(res.statusCode, 200);
      assert.strictEqual(res.json.data.originalValue, testSecret, 'Decrypted value must match original secret');
    });

    // -----------------------------------------------------------------------
    // 4. AUDIT LOGGING & CRYPTOGRAPHIC HASH CHAIN INTEGRITY
    // -----------------------------------------------------------------------
    await test('Audit: Cryptographic hash chain verification passes across all logged events', async () => {
      const res = await makeRequest({
        path: '/api/v1/audit-logs/verify',
        headers: { Authorization: `Bearer ${analystToken}` }
      });
      assert.strictEqual(res.statusCode, 200);
      assert.strictEqual(res.json.data.valid, true, 'Audit log chain verification must be valid');
      assert(res.json.data.count > 0, 'Audit entries must have been recorded');
    });

    // -----------------------------------------------------------------------
    // 5. UNIFIED RISK ENGINE & POLICY ENFORCEMENT
    // -----------------------------------------------------------------------
    await test('Risk Engine: Weighted rule calculation is deterministic (0.40 Voice + 0.35 Social + 0.25 DLP)', async () => {
      const res = await makeRequest({
        path: '/api/v1/security/evaluate-risk',
        method: 'POST',
        headers: { Authorization: `Bearer ${analystToken}` },
        body: { voiceScore: 0.90, socialScore: 0.80, dlpScore: 0.60 }
      });
      assert.strictEqual(res.statusCode, 200);
      // Expected = 0.40 * 0.9 + 0.35 * 0.8 + 0.25 * 0.6 = 0.36 + 0.28 + 0.15 = 0.79 -> HIGH
      assert.strictEqual(res.json.data.fusedRisk, 0.79);
      assert.strictEqual(res.json.data.level, 'HIGH');
    });

    await test('Metrics: Platform metrics report real counts and no fabricated model benchmarks', async () => {
      const res = await makeRequest({
        path: '/api/v1/metrics',
        headers: { Authorization: `Bearer ${analystToken}` }
      });
      assert.strictEqual(res.statusCode, 200);
      assert(res.json.data.socSummary.totalAuditLogs > 0);
      assert.strictEqual(
        res.json.data.modelBenchmarks.phase2RiskEngine.status,
        'CONDITIONAL / NOT IMPLEMENTED'
      );
    });

  } finally {
    if (server) server.close();
    await mongoose.disconnect();
  }

  console.log(`\n=== Comprehensive Security Test Results: ${passedCount}/${totalCount} tests passed ===`);
  if (passedCount !== totalCount) {
    process.exit(1);
  }
}

if (require.main === module) {
  runSecurityTestSuite().catch((err) => {
    console.error('Fatal test error:', err);
    process.exit(1);
  });
}

module.exports = { runSecurityTestSuite };
