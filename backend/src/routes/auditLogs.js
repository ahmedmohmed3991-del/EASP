// EASP Audit Log Routes - Phase 5 / Phase 11
// Read-only access to immutable audit records and cryptographic hash chain verification.
// Append-only guarantee: strictly NO write, update, or delete endpoints exposed.

const express = require('express');
const AuditLog = require('../models/AuditLog');
const { authenticateJWT } = require('../middleware/auth');
const { authorizeRoles } = require('../middleware/rbac');
const { apiLimiter } = require('../middleware/rateLimiter');

const router = express.Router();

router.use(apiLimiter);
router.use(authenticateJWT);
router.use(authorizeRoles('Analyst', 'Administrator'));

// GET /api/v1/audit-logs - Query audit entries with pagination
router.get('/', async (req, res) => {
  try {
    const { eventType, actionTaken, limit = 50, skip = 0 } = req.query;
    const filter = {};
    if (eventType) filter.eventType = eventType;
    if (actionTaken) filter.actionTaken = actionTaken;

    const logs = await AuditLog.find(filter)
      .sort({ timestamp: -1, _id: -1 })
      .skip(parseInt(skip, 10))
      .limit(parseInt(limit, 10));

    const total = await AuditLog.countDocuments(filter);

    const formattedLogs = logs.map(log => ({
      _id: log._id,
      timestamp: log.timestamp,
      eventType: log.eventType,
      actor: {
        email: log.username || 'system@easp.local',
        userId: log.userId ? log.userId.toString() : 'system',
        role: log.userRole || 'None'
      },
      username: log.username,
      ipAddress: log.ipAddress,
      actionTaken: log.actionTaken,
      riskScore: log.riskScore,
      riskLevel: log.riskLevel,
      recordHash: log.hash,
      hash: log.hash,
      previousHash: log.previousHash,
      details: log.details
    }));

    res.status(200).json({
      status: 'success',
      data: {
        total,
        logs: formattedLogs
      }
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Failed to retrieve audit records: ' + err.message
    });
  }
});

// GET /api/v1/audit-logs/verify - Cryptographic SHA-256 chain verification
router.get('/verify', async (req, res) => {
  try {
    const verification = await AuditLog.verifyChain();
    res.status(200).json({
      status: 'success',
      data: verification
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Audit chain verification failed: ' + err.message
    });
  }
});

module.exports = router;
