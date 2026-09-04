// Automated Validation Test Suite for Task T-P02-014:
// Helmet Security Headers & CORS Allow-List Validation

const http = require('http');
const assert = require('assert');
const app = require('../src/server');
const { parseAllowedOrigins } = require('../src/config/cors');

let server;
let baseUrl;

async function runTests() {
  console.log('=== Running Security Headers & CORS Allow-List Validation Tests ===\n');
  let passedCount = 0;
  let totalCount = 0;

  function test(name, fn) {
    totalCount++;
    try {
      fn();
      console.log(`[PASS] ${name}`);
      passedCount++;
    } catch (err) {
      console.error(`[FAIL] ${name}`);
      console.error(`       ${err.message}`);
    }
  }

  async function testAsync(name, fn) {
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

  // Helper for HTTP requests
  function makeRequest({ path = '/', method = 'GET', headers = {} }) {
    return new Promise((resolve, reject) => {
      const url = new URL(path, baseUrl);
      const req = http.request(
        url,
        {
          method,
          headers
        },
        (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk));
          res.on('end', () => {
            resolve({
              statusCode: res.statusCode,
              headers: res.headers,
              body
            });
          });
        }
      );
      req.on('error', reject);
      req.end();
    });
  }

  // Start test server on dynamic port
  await new Promise((resolve) => {
    server = app.listen(0, () => {
      const port = server.address().port;
      baseUrl = `http://127.0.0.1:${port}`;
      console.log(`Test server running at ${baseUrl}\n`);
      resolve();
    });
  });

  try {
    // 1. Unit Tests for parseAllowedOrigins
    test('parseAllowedOrigins: correctly parses comma-separated origins', () => {
      const input = 'http://localhost:5173, http://localhost:3000/,  https://app.easp.local ';
      const result = parseAllowedOrigins(input);
      assert.deepStrictEqual(result, [
        'http://localhost:5173',
        'http://localhost:3000',
        'https://app.easp.local'
      ]);
    });

    test('parseAllowedOrigins: handles empty or invalid strings safely', () => {
      assert.deepStrictEqual(parseAllowedOrigins(''), []);
      assert.deepStrictEqual(parseAllowedOrigins(null), []);
      assert.deepStrictEqual(parseAllowedOrigins(undefined), []);
      assert.deepStrictEqual(parseAllowedOrigins('   '), []);
    });

    // 2. Helmet Security Headers on GET /
    await testAsync('Helmet: Root endpoint (GET /) includes all security headers', async () => {
      const res = await makeRequest({ path: '/' });
      assert.strictEqual(res.statusCode, 200);

      // Check essential security headers
      assert(res.headers['content-security-policy'], 'Missing Content-Security-Policy');
      assert.strictEqual(res.headers['x-content-type-options'], 'nosniff', 'Expected nosniff');
      assert.strictEqual(res.headers['x-frame-options'], 'SAMEORIGIN', 'Expected X-Frame-Options: SAMEORIGIN');
      assert.strictEqual(res.headers['cross-origin-opener-policy'], 'same-origin', 'Expected COOP: same-origin');
      assert.strictEqual(res.headers['cross-origin-resource-policy'], 'cross-origin', 'Expected CORP: cross-origin');
      assert.strictEqual(res.headers['referrer-policy'], 'no-referrer', 'Expected Referrer-Policy: no-referrer');
      assert.strictEqual(res.headers['x-powered-by'], undefined, 'X-Powered-By must be hidden');
    });

    // 3. Helmet Security Headers on Health Route
    await testAsync('Helmet: Health route (GET /health) includes security headers', async () => {
      const res = await makeRequest({ path: '/health' });
      assert(res.headers['content-security-policy'], 'Missing CSP on /health');
      assert.strictEqual(res.headers['x-content-type-options'], 'nosniff');
      assert.strictEqual(res.headers['x-frame-options'], 'SAMEORIGIN');
    });

    // 4. CORS: Allowed origin (http://localhost:5173)
    await testAsync('CORS: Configured origin (http://localhost:5173) is accepted with credentials', async () => {
      const res = await makeRequest({
        path: '/',
        headers: { Origin: 'http://localhost:5173' }
      });
      assert.strictEqual(res.statusCode, 200);
      assert.strictEqual(res.headers['access-control-allow-origin'], 'http://localhost:5173');
      assert.strictEqual(res.headers['access-control-allow-credentials'], 'true');
    });

    // 5. CORS: Allowed origin (http://localhost:3000)
    await testAsync('CORS: Configured origin (http://localhost:3000) is accepted with credentials', async () => {
      const res = await makeRequest({
        path: '/',
        headers: { Origin: 'http://localhost:3000' }
      });
      assert.strictEqual(res.statusCode, 200);
      assert.strictEqual(res.headers['access-control-allow-origin'], 'http://localhost:3000');
      assert.strictEqual(res.headers['access-control-allow-credentials'], 'true');
    });

    // 6. CORS: Non-browser request without Origin header (curl / server-to-server)
    await testAsync('CORS: Requests without Origin header are permitted', async () => {
      const res = await makeRequest({ path: '/' });
      assert.strictEqual(res.statusCode, 200);
      // When no Origin is sent, Access-Control-Allow-Origin is not attached
      assert.strictEqual(res.headers['access-control-allow-origin'], undefined);
    });

    // 7. CORS: Unauthorized origin rejection
    await testAsync('CORS: Unauthorized origin (http://malicious-attacker.com) is rejected with 403', async () => {
      const res = await makeRequest({
        path: '/',
        headers: { Origin: 'http://malicious-attacker.com' }
      });
      assert.strictEqual(res.statusCode, 403);
      assert.strictEqual(res.headers['access-control-allow-origin'], undefined);
      const json = JSON.parse(res.body);
      assert(json.error && json.error.includes('CORS policy violation'));
    });

    // 8. CORS: Preflight OPTIONS request for authorized origin
    await testAsync('CORS: Preflight OPTIONS request for allowed origin returns 204 with allowed methods/headers', async () => {
      const res = await makeRequest({
        path: '/',
        method: 'OPTIONS',
        headers: {
          Origin: 'http://localhost:5173',
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
      });
      assert.strictEqual(res.statusCode, 204);
      assert.strictEqual(res.headers['access-control-allow-origin'], 'http://localhost:5173');
      assert.strictEqual(res.headers['access-control-allow-credentials'], 'true');
      assert(res.headers['access-control-allow-methods'].includes('POST'));
      assert(res.headers['access-control-allow-headers'].includes('Authorization'));
      assert.strictEqual(res.headers['access-control-max-age'], '86400');
    });

    // 9. CORS: Preflight OPTIONS request for unauthorized origin
    await testAsync('CORS: Preflight OPTIONS request for unauthorized origin is rejected with 403', async () => {
      const res = await makeRequest({
        path: '/',
        method: 'OPTIONS',
        headers: {
          Origin: 'http://evil-site.com',
          'Access-Control-Request-Method': 'POST'
        }
      });
      assert.strictEqual(res.statusCode, 403);
      assert.strictEqual(res.headers['access-control-allow-origin'], undefined);
    });

  } finally {
    if (server) {
      server.close();
    }
  }

  console.log(`\n=== Test Results: ${passedCount}/${totalCount} tests passed ===`);
  if (passedCount !== totalCount) {
    process.exit(1);
  }
}

runTests().catch((err) => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
