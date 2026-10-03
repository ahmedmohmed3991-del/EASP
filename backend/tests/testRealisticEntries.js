const { appendAuditLog, readAuditLog, verifyChain } = require('../src/auditLogger');

appendAuditLog({ action: 'LOGIN', user: 'alice', result: 'success' });
appendAuditLog({ action: 'DLP_SCAN', user: 'bob', result: 'blocked' });
appendAuditLog({ action: 'POLICY_DECISION', user: 'carol', result: 'escalated' });

console.log('--- All entries ---');
console.log(readAuditLog());

console.log('\n--- Chain integrity ---');
console.log(verifyChain());  
