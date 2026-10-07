// EASP Incidents Routes - Phase 11 / 12
// Role-restricted incident management for Security Analysts and Administrators.

const express = require('express');
const Incident = require('../models/Incident');
const AuditLog = require('../models/AuditLog');
const { authenticateJWT } = require('../middleware/auth');
const { authorizeRoles } = require('../middleware/rbac');
const { apiLimiter } = require('../middleware/rateLimiter');

const router = express.Router();

// Apply common middleware
router.use(apiLimiter);
router.use(authenticateJWT);
router.use(authorizeRoles('Analyst', 'Administrator'));

const mongoose = require('mongoose');

function findIncidentByIdOrCode(id) {
  const isObjectId = mongoose.Types.ObjectId.isValid(id) && id.length === 24;
  return Incident.findOne({
    $or: [
      { incidentId: id },
      ...(isObjectId ? [{ _id: id }] : [])
    ]
  });
}

function formatIncident(i) {
  return {
    _id: i._id,
    id: i._id,
    incidentId: i.incidentId || `INC-${i._id.toString().slice(-4).toUpperCase()}`,
    createdAt: i.createdAt ? i.createdAt.toISOString() : new Date().toISOString(),
    category: i.category || (i.source === 'CALL_ANALYSIS' ? 'Voice Spoof Alert' : i.source === 'PROMPT_SCAN' ? 'DLP Credential Leak' : 'Policy Violation'),
    severity: i.severity,
    riskScore: i.riskScore,
    actionTaken: i.actionTaken,
    status: i.status,
    description: i.title || i.description || 'Security Incident',
    assignedTo: i.username || 'Security SOC',
    auditLogId: i.auditLogId ? i.auditLogId.toString() : null,
    riskBreakdown: {
      voiceRisk: i.contributingFactors?.voiceRisk || 0,
      socialRisk: i.contributingFactors?.socialRisk || 0,
      dlpRisk: i.contributingFactors?.dlpSensitivity || 0
    },
    notes: (i.notes || []).map(n => ({
      author: n.author || 'Analyst',
      note: n.text || n.note || '',
      text: n.text || n.note || '',
      timestamp: n.createdAt ? n.createdAt.toISOString() : new Date().toISOString(),
      createdAt: n.createdAt ? n.createdAt.toISOString() : new Date().toISOString()
    }))
  };
}

// GET /api/v1/incidents - List incidents with optional status & severity filtering
router.get('/', async (req, res) => {
  try {
    const { status, severity, limit = 50, skip = 0 } = req.query;
    const filter = {};
    if (status) filter.status = status;
    if (severity) filter.severity = severity;

    const incidents = await Incident.find(filter)
      .sort({ createdAt: -1 })
      .skip(parseInt(skip, 10))
      .limit(parseInt(limit, 10));

    const total = await Incident.countDocuments(filter);

    res.status(200).json({
      status: 'success',
      data: {
        total,
        incidents: incidents.map(formatIncident)
      }
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Failed to retrieve incidents: ' + err.message
    });
  }
});

// GET /api/v1/incidents/:id - Get single incident
router.get('/:id', async (req, res) => {
  try {
    const incident = await findIncidentByIdOrCode(req.params.id);
    if (!incident) {
      return res.status(404).json({
        status: 'error',
        error: 'Incident not found'
      });
    }

    res.status(200).json({
      status: 'success',
      data: formatIncident(incident)
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Failed to retrieve incident: ' + err.message
    });
  }
});

// PATCH /api/v1/incidents/:id - Triage incident status and append notes
router.patch('/:id', async (req, res) => {
  try {
    const { status, note } = req.body;
    const incident = await findIncidentByIdOrCode(req.params.id);

    if (!incident) {
      return res.status(404).json({
        status: 'error',
        error: 'Incident not found'
      });
    }

    if (status && ['OPEN', 'INVESTIGATING', 'RESOLVED', 'DISMISSED'].includes(status.toUpperCase())) {
      incident.status = status.toUpperCase();
      if (incident.status === 'RESOLVED') {
        incident.resolvedAt = new Date();
      }
    }

    if (note && typeof note === 'string') {
      incident.notes.push({
        author: req.user.username || 'Analyst',
        text: note,
        createdAt: new Date()
      });
    }

    await incident.save();

    // Audit log the status update
    await AuditLog.logEvent({
      eventType: 'INCIDENT_UPDATED',
      userId: req.user.id,
      username: req.user.username,
      userRole: req.user.role,
      actionTaken: 'INFO',
      riskScore: incident.riskScore,
      riskLevel: incident.riskLevel,
      details: {
        incidentId: incident.incidentId || incident._id,
        newStatus: incident.status,
        noteAdded: !!note
      }
    });

    res.status(200).json({
      status: 'success',
      message: 'Incident updated successfully',
      data: formatIncident(incident)
    });
  } catch (err) {
    res.status(500).json({
      status: 'error',
      error: 'Failed to update incident: ' + err.message
    });
  }
});

module.exports = router;
