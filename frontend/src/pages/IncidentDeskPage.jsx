import React, { useState, useEffect, useCallback } from 'react';
import { incidentApi } from '../services/apiClient';

export default function IncidentDeskPage({ currentUser }) {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [noteInput, setNoteInput] = useState('');
  const [updating, setUpdating] = useState(false);

  const fetchIncidents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (severityFilter) params.severity = severityFilter;
      const res = await incidentApi.getIncidents(params);
      setIncidents(res.data?.incidents || []);
    } catch (err) {
      setError(err.message || 'Failed to load incidents');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, severityFilter]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const handleStatusChange = async (incidentId, newStatus) => {
    setUpdating(true);
    try {
      await incidentApi.updateIncident(incidentId, newStatus, noteInput.trim() || undefined);
      setNoteInput('');
      await fetchIncidents();
      // Update selected if open
      if (selectedIncident && selectedIncident.incidentId === incidentId) {
        setSelectedIncident((prev) => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  const handleAddNote = async () => {
    if (!selectedIncident || !noteInput.trim()) return;
    setUpdating(true);
    try {
      await incidentApi.updateIncident(selectedIncident.incidentId, selectedIncident.status, noteInput.trim());
      setNoteInput('');
      await fetchIncidents();
      // refresh selected incident
      const res = await incidentApi.getIncidents({});
      const updated = res.data?.incidents?.find((inc) => inc.incidentId === selectedIncident.incidentId);
      if (updated) setSelectedIncident(updated);
    } catch (err) {
      alert(`Failed to add note: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  const isAnalystOrAdmin = currentUser && ['Analyst', 'Administrator'].includes(currentUser.role);

  return (
    <div className="page-pane">
      <div className="glass-card">
        <div className="card-title-row">
          <h2 className="card-title">
            <span className="badge-platform">SOC DESK</span>
            Security Incident Triage Queue
          </h2>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button className="btn-secondary" onClick={fetchIncidents} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh Queue'}
            </button>
          </div>
        </div>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Centralized threat queue populated by DLP token redactions, RawNet2 voice spoof alerts, and mBERT social engineering interventions.
        </p>

        {/* Filter Bar */}
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(0,0,0,0.2)', borderRadius: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="incident-status-filter" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Status:</label>
            <select
              id="incident-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: '0.35rem 0.6rem', background: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '4px' }}
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="INVESTIGATING">INVESTIGATING</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="incident-severity-filter" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Severity:</label>
            <select
              id="incident-severity-filter"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{ padding: '0.35rem 0.6rem', background: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '4px' }}
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            Showing {incidents.length} incidents
          </span>
        </div>

        {error && (
          <div className="alert-error" role="alert">
            {error}
          </div>
        )}

        {/* Incidents Table */}
        <div className="table-scroll" role="region" aria-label="IncidentDesk data table" tabIndex={0}>
          <table className="cyber-table">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>ID</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Timestamp</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Category</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Severity</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Threat Score</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Policy Action</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Status</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {incidents.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    {loading ? 'Loading incidents...' : 'No security incidents match the filter criteria.'}
                  </td>
                </tr>
              ) : (
                incidents.map((inc) => (
                  <tr
                    key={inc.incidentId}
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      backgroundColor: selectedIncident?.incidentId === inc.incidentId ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                      cursor: 'pointer'
                    }}
                    onClick={() => setSelectedIncident(inc)}
                  >
                    <td style={{ padding: '0.65rem 0.5rem', fontFamily: 'monospace', color: 'var(--accent-primary)' }}>
                      {inc.incidentId}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-secondary)' }}>
                      {new Date(inc.createdAt).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span style={{ padding: '0.2rem 0.5rem', background: 'rgba(255,255,255,0.08)', borderRadius: '4px' }}>
                        {inc.category}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span className={`pill-badge pill-${inc.severity?.toLowerCase()}`}>
                        {inc.severity}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', fontWeight: 600 }}>
                      {(inc.riskScore * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span className={`pill-badge pill-${inc.actionTaken?.toLowerCase()}`}>
                        {inc.actionTaken}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      {isAnalystOrAdmin ? (
                        <select
                          aria-label={`Status for incident ${inc.incidentId || inc._id}`}
                          value={inc.status}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => handleStatusChange(inc.incidentId, e.target.value)}
                          disabled={updating}
                          style={{
                            padding: '0.2rem 0.4rem',
                            fontSize: '0.8rem',
                            background: inc.status === 'OPEN' ? 'rgba(239, 68, 68, 0.2)' : inc.status === 'RESOLVED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '4px'
                          }}
                        >
                          <option value="OPEN">OPEN</option>
                          <option value="INVESTIGATING">INVESTIGATING</option>
                          <option value="RESOLVED">RESOLVED</option>
                          <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
                        </select>
                      ) : (
                        <span>{inc.status}</span>
                      )}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <button
                        className="btn-secondary"
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedIncident(inc);
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Incident Deep Inspection Drawer */}
      {selectedIncident && (
        <div className="glass-card" style={{ marginTop: '1.5rem', borderLeft: '4px solid var(--accent-primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>
              Incident Dossier: <span style={{ fontFamily: 'monospace', color: 'var(--accent-primary)' }}>{selectedIncident.incidentId}</span>
            </h3>
            <button className="btn-secondary" style={{ padding: '0.25rem 0.5rem' }} onClick={() => setSelectedIncident(null)}>
              Close
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '1rem', fontSize: '0.85rem' }}>
            <div>
              <p><strong>Description:</strong> {selectedIncident.description}</p>
              <p><strong>Risk Components:</strong></p>
              <ul style={{ margin: '0.25rem 0', paddingLeft: '1.25rem', color: 'var(--text-secondary)' }}>
                <li>Voice Threat: {selectedIncident.riskBreakdown?.voiceRisk !== undefined ? `${(selectedIncident.riskBreakdown.voiceRisk * 100).toFixed(1)}%` : 'N/A'}</li>
                <li>Social Eng Threat: {selectedIncident.riskBreakdown?.socialRisk !== undefined ? `${(selectedIncident.riskBreakdown.socialRisk * 100).toFixed(1)}%` : 'N/A'}</li>
                <li>DLP Threat: {selectedIncident.riskBreakdown?.dlpRisk !== undefined ? `${(selectedIncident.riskBreakdown.dlpRisk * 100).toFixed(1)}%` : 'N/A'}</li>
              </ul>
            </div>

            <div>
              <p><strong>Assigned Analyst:</strong> {selectedIncident.assignedTo || 'Unassigned'}</p>
              <p><strong>Associated Audit Log:</strong> <span style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{selectedIncident.auditLogId || 'None'}</span></p>
              <p><strong>Created:</strong> {new Date(selectedIncident.createdAt).toLocaleString()}</p>
            </div>
          </div>

          {/* Analyst Notes Section */}
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem' }}>Analyst Investigation Notes</h4>
            <div style={{ maxHeight: '150px', overflowY: 'auto', marginBottom: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {selectedIncident.notes && selectedIncident.notes.length > 0 ? (
                selectedIncident.notes.map((n, i) => (
                  <div key={i} style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.25)', borderRadius: '4px', fontSize: '0.8rem' }}>
                    <div style={{ color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                      {n.author || 'Analyst'} • {new Date(n.timestamp).toLocaleString()}
                    </div>
                    <div>{n.note}</div>
                  </div>
                ))
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No notes recorded yet.</div>
              )}
            </div>

            {isAnalystOrAdmin && (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  aria-label="Analyst note"
                  placeholder="Enter analyst note..."
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '0.45rem 0.75rem',
                    background: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px'
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                />
                <button className="btn-primary" onClick={handleAddNote} disabled={updating || !noteInput.trim()}>
                  Append Note
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
