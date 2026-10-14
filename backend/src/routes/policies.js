// EASP Policy Management Routes - Phase 5 / Phase 11
// Admin-controlled policy rule CRUD for the EASP Policy Engine.

const express = require('express');
const Policy = require('../models/Policy');
const AuditLog = require('../models/AuditLog');
const { authenticateJWT } = require('../middleware/auth');
const { authorizeRoles } = require('../middleware/rbac');
const { apiLimiter } = require('../middleware/rateLimiter');

const router = express.Router();

router.use(apiLimiter);
router.use(authenticateJWT);

// GET /api/v1/policies - List all policies (Analyst & Admin)
router.get('/', authorizeRoles('Analyst', 'Administrator'), async (req, res) => {
  try {
    const rawPolicies = await Policy.find().sort({ priority: 1 });
    const mappedPolicies = rawPolicies.map(p => ({
      _id: p._id,
      policyId: p.name.toUpperCase().replace(/\s+/g, '_'),
      name: p.name,
      description: p.description,
      action: p.action,
      priority: p.priority,
      conditions: {
        voiceRiskThreshold: p.minRiskScore,
        socialEngThreshold: p.minRiskScore,
        dlpSeverityThreshold: p.requireDlpRedaction ? 'HIGH' : 'ANY'
      },
      minRiskScore: p.minRiskScore,
      maxRiskScore: p.maxRiskScore,
      requireDlpRedaction: p.requireDlpRedaction,
      isActive: p.isActive,
      createdAt: p.createdAt
    }));

    res.status(200).json({
      status: 'success',
      data: {
        policies: mappedPolicies
      }
    });
  } catch (err) {
    res.status(500).json({ status: 'error', error: err.message });
  }
});

// POST /api/v1/policies - Create or update policy rule (Administrator only)
router.post('/', authorizeRoles('Administrator'), async (req, res) => {
  try {
    const { policyId, name, description, action, priority, conditions, minRiskScore, maxRiskScore, requireDlpRedaction } = req.body;
    const policyName = name || policyId;
    let policy = await Policy.findOne({ name: policyName });
    let statusCode = 201;

    const minRisk = minRiskScore !== undefined ? minRiskScore : (conditions?.voiceRiskThreshold ?? 0.0);
    const maxRisk = maxRiskScore !== undefined ? maxRiskScore : 1.0;
    const dlpRedact = requireDlpRedaction !== undefined ? requireDlpRedaction : (conditions?.dlpSeverityThreshold === 'HIGH');

    const updateData = {
      name: policyName,
      description: description || `Policy rule for ${policyName}`,
      action: action || 'BLOCK',
      priority: Number(priority) || 10,
      minRiskScore: minRisk,
      maxRiskScore: maxRisk,
      requireDlpRedaction: dlpRedact,
      isActive: req.body.isActive !== undefined ? req.body.isActive : true
    };

    if (policy) {
      Object.assign(policy, updateData);
      await policy.save();
      statusCode = 200;
    } else {
      policy = new Policy(updateData);
      await policy.save();
    }

    await AuditLog.logEvent({
      eventType: 'POLICY_DECISION',
      userId: req.user.id,
      username: req.user.username,
      userRole: req.user.role,
      actionTaken: 'INFO',
      riskScore: 0.0,
      riskLevel: 'LOW',
      details: {
        action: statusCode === 201 ? 'POLICY_CREATED' : 'POLICY_UPDATED',
        policyId: policy._id,
        policyName: policy.name
      }
    });

    res.status(statusCode).json({ status: 'success', data: policy });
  } catch (err) {
    res.status(500).json({ status: 'error', error: err.message });
  }
});

// PUT /api/v1/policies/:id - Update policy rule (Administrator only)
router.put('/:id', authorizeRoles('Administrator'), async (req, res) => {
  try {
    const policy = await Policy.findByIdAndUpdate(req.params.id, req.body, { new: true });
    if (!policy) {
      return res.status(404).json({ status: 'error', error: 'Policy not found' });
    }

    await AuditLog.logEvent({
      eventType: 'POLICY_DECISION',
      userId: req.user.id,
      username: req.user.username,
      userRole: req.user.role,
      actionTaken: 'INFO',
      riskScore: 0.0,
      riskLevel: 'LOW',
      details: {
        action: 'POLICY_UPDATED',
        policyId: policy._id,
        policyName: policy.name
      }
    });

    res.status(200).json({ status: 'success', data: policy });
  } catch (err) {
    res.status(500).json({ status: 'error', error: err.message });
  }
});

// DELETE /api/v1/policies/:id - Delete policy rule (Administrator only)
router.delete('/:id', authorizeRoles('Administrator'), async (req, res) => {
  try {
    const policy = await Policy.findByIdAndDelete(req.params.id);
    if (!policy) {
      return res.status(404).json({ status: 'error', error: 'Policy not found' });
    }

    res.status(200).json({ status: 'success', message: 'Policy removed successfully' });
  } catch (err) {
    res.status(500).json({ status: 'error', error: err.message });
  }
});

module.exports = router;
