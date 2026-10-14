import React, { useState, useEffect, useCallback } from 'react';
import { policyApi } from '../services/apiClient';

export default function PolicyGovernancePage({ currentUser }) {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);

  // New policy form state
  const [formData, setFormData] = useState({
    policyId: '',
    name: '',
    description: '',
    action: 'BLOCK',
    priority: 10,
    voiceRiskThreshold: 0.70,
    socialEngThreshold: 0.70,
    dlpSeverityThreshold: 'HIGH'
  });

  const fetchPolicies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await policyApi.getPolicies();
      setPolicies(res.data?.policies || []);
    } catch (err) {
      setError(err.message || 'Failed to load policies');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const payload = {
        policyId: formData.policyId.toUpperCase().trim(),
        name: formData.name.trim(),
        description: formData.description.trim(),
        action: formData.action,
        priority: Number(formData.priority),
        conditions: {
          voiceRiskThreshold: Number(formData.voiceRiskThreshold),
          socialEngThreshold: Number(formData.socialEngThreshold),
          dlpSeverityThreshold: formData.dlpSeverityThreshold
        }
      };
      await policyApi.createPolicy(payload);
      setShowCreateModal(false);
      setFormData({
        policyId: '',
        name: '',
        description: '',
        action: 'BLOCK',
        priority: 10,
        voiceRiskThreshold: 0.70,
        socialEngThreshold: 0.70,
        dlpSeverityThreshold: 'HIGH'
      });
      await fetchPolicies();
    } catch (err) {
      alert(`Policy creation failed: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const isAdmin = currentUser && currentUser.role === 'Administrator';

  return (
    <div>
      <div className="glass-card">
        <div className="card-title-row">
          <h2 className="card-title">
            <span className="badge-platform">GOVERNANCE</span>
            Deterministic Policy Rules & Enforcement Engine
          </h2>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            {isAdmin && (
              <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
                + Create Policy Rule
              </button>
            )}
            <button className="btn-secondary" onClick={fetchPolicies} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh Policies'}
            </button>
          </div>
        </div>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Configurable deterministic rule precedence evaluated by the EASP Policy Engine. Highest priority matching rules dictate whether an event is Permitted, Tokenized, Escalated, or Terminated.
        </p>

        {error && (
          <div style={{ padding: '0.75rem 1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger-color)', borderRadius: '6px', color: '#fca5a5', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {/* Policies Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '0.75rem 0.5rem' }}>Priority</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Policy ID</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Name</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Action</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Thresholds (Voice / NLP / DLP)</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {policies.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    {loading ? 'Loading policy rules...' : 'No active policies configured.'}
                  </td>
                </tr>
              ) : (
                policies.map((p) => (
                  <tr key={p.policyId} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '0.65rem 0.5rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                      #{p.priority}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                      {p.policyId}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <div style={{ fontWeight: 600 }}>{p.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{p.description}</div>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span className={`pill-badge pill-${p.action?.toLowerCase()}`}>
                        {p.action}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Voice &ge; {p.conditions?.voiceRiskThreshold !== undefined ? `${(p.conditions.voiceRiskThreshold * 100).toFixed(0)}%` : 'N/A'} |{' '}
                      Social &ge; {p.conditions?.socialEngThreshold !== undefined ? `${(p.conditions.socialEngThreshold * 100).toFixed(0)}%` : 'N/A'} |{' '}
                      DLP: {p.conditions?.dlpSeverityThreshold || 'ANY'}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        background: p.isActive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.05)',
                        color: p.isActive ? 'var(--success-color)' : 'var(--text-muted)'
                      }}>
                        {p.isActive ? 'ACTIVE' : 'DISABLED'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Admin Policy Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div className="glass-card" style={{ width: '90%', maxWidth: '520px', border: '1px solid var(--accent-primary)' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Create Deterministic Policy</h3>
            <form onSubmit={handleCreatePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Policy ID (e.g. POL-006):</label>
                <input
                  type="text"
                  required
                  placeholder="POL-006"
                  value={formData.policyId}
                  onChange={(e) => setFormData({ ...formData, policyId: e.target.value })}
                  style={{ width: '100%', padding: '0.45rem', background: 'var(--bg-card)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Policy Name:</label>
                <input
                  type="text"
                  required
                  placeholder="Strict API Protection"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  style={{ width: '100%', padding: '0.45rem', background: 'var(--bg-card)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Description:</label>
                <input
                  type="text"
                  placeholder="Rule purpose and justification"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  style={{ width: '100%', padding: '0.45rem', background: 'var(--bg-card)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Enforcement Action:</label>
                  <select
                    value={formData.action}
                    onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                    style={{ width: '100%', padding: '0.45rem', background: 'var(--bg-card)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                  >
                    <option value="ALLOW">ALLOW</option>
                    <option value="REDACT">REDACT</option>
                    <option value="ESCALATE">ESCALATE</option>
                    <option value="BLOCK">BLOCK</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Priority (Lower = Higher):</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    style={{ width: '100%', padding: '0.45rem', background: 'var(--bg-card)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Voice Threshold (0.0 - 1.0):</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={formData.voiceRiskThreshold}
                    onChange={(e) => setFormData({ ...formData, voiceRiskThreshold: e.target.value })}
                    style={{ width: '100%', padding: '0.45rem', background: 'var(--bg-card)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Social Eng Threshold:</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={formData.socialEngThreshold}
                    onChange={(e) => setFormData({ ...formData, socialEngThreshold: e.target.value })}
                    style={{ width: '100%', padding: '0.45rem', background: 'var(--bg-card)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? 'Saving...' : 'Deploy Policy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
