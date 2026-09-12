const { appendAuditLog, verifyChain, LOG_FILE } = require('./auditLogger');
const fs = require('fs');

appendAuditLog({ action: 'LOGIN', user: 'alice', result: 'success' });
appendAuditLog({ action: 'DLP_SCAN', user: 'bob', result: 'blocked' });
appendAuditLog({ action: 'POLICY_DECISION', user: 'carol', result: 'escalated' });

console.log('Before tampering:', verifyChain());

// Simulate tampering: directly edit the log file, bypassing the module entirely
let raw = fs.readFileSync(LOG_FILE, 'utf-8');
raw = raw.replace('success', 'FAKE!!');
fs.writeFileSync(LOG_FILE, raw);

console.log('After tampering: ', verifyChain());