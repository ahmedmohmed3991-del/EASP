const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

const LOG_FILE = path.join(__dirname, '../audit.log.jsonl');
const GENESIS_HASH = '0'.repeat(64);

function getLastHash() {
  if (!fs.existsSync(LOG_FILE)) return GENESIS_HASH;
  const lines = fs.readFileSync(LOG_FILE, 'utf-8').trim().split('\n').filter(Boolean);
  if (lines.length === 0) return GENESIS_HASH;
  const last = JSON.parse(lines[lines.length - 1]);
  return last.hash;
}

function appendAuditLog(entry) {
  const prevHash = getLastHash();
  const timestamp = new Date().toISOString();
  const payload = { ...entry, timestamp, prevHash };

  const hash = crypto
    .createHash('sha256')
    .update(JSON.stringify(payload))
    .digest('hex');

  const record = { ...payload, hash };
  fs.appendFileSync(LOG_FILE, JSON.stringify(record) + '\n', { flag: 'a' });
  return record;
}

function readAuditLog() {
  if (!fs.existsSync(LOG_FILE)) return [];
  return fs.readFileSync(LOG_FILE, 'utf-8')
    .trim()
    .split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line));
}

function verifyChain() {
  const lines = readAuditLog();
  let expectedPrev = GENESIS_HASH;

  for (let i = 0; i < lines.length; i++) {
    const { hash, ...payload } = lines[i];
    const recomputed = crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex');

    if (recomputed !== hash || payload.prevHash !== expectedPrev) {
      return { valid: false, brokenAt: i };
    }
    expectedPrev = hash;
  }
  return { valid: true, brokenAt: null };
}

// LAZEM no deleteAuditLog() AW updateAuditLog() export (T-P05-029).
module.exports = { appendAuditLog, readAuditLog, verifyChain, LOG_FILE };