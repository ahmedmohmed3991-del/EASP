import React, { useState, useEffect, useCallback } from 'react';
import { auditApi } from '../services/apiClient';

export default function AuditLogPage({ currentUser }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await auditApi.getLogs({ limit: 50 });
      setLogs(res.data?.logs || []);
    } catch (err) {
      setError(err.message || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleVerifyChain = async () => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const res = await auditApi.verifyChain();
      setVerificationResult(res.data);
    } catch (err) {
      alert(`Verification error: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="page-pane">
      <div className="glass-card">
        <div className="card-title-row">
          <h2 className="card-title">
            <span className="badge-platform">CRYPTOGRAPHY</span>
            Immutable Audit Trail & Hash-Chaining
          </h2>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              className="btn-primary"
              onClick={handleVerifyChain}
              disabled={verifying}
            >
              {verifying ? 'Verifying Hashes...' : 'Verify SHA-256 Chain'}
            </button>
            <button className="btn-secondary" onClick={fetchLogs} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh Logs'}
            </button>
          </div>
        </div>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Every security scan, redaction, policy enforcement, and authentication event is committed to an append-only cryptographic ledger where each record includes the SHA-256 digest of the predecessor.
        </p>

        {/* Verification Status Banner */}
        {verificationResult && (
          <div style={{
            marginBottom: '1.25rem',
            padding: '1rem',
            borderRadius: '6px',
            border: `1px solid ${verificationResult.chainValid ? 'var(--success-color)' : 'var(--danger-color)'}`,
            background: verificationResult.chainValid ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: 'var(--text-primary)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>{verificationResult.chainValid ? '🛡️' : '🚨'}</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '1rem', color: verificationResult.chainValid ? 'var(--success-color)' : 'var(--danger-color)' }}>
                    {verificationResult.chainValid ? 'CRYPTOGRAPHIC AUDIT CHAIN INTACT' : 'CHAIN INTEGRITY VIOLATION DETECTED'}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                    {verificationResult.verifiedRecords || 0} sequential records cryptographically verified from Genesis to Head.
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right', fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                {verificationResult.headHash ? `Head: ${verificationResult.headHash.substring(0, 16)}...` : ''}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="alert-error" role="alert">
            {error}
          </div>
        )}

        {/* Audit Logs Table */}
        <div className="table-scroll" role="region" aria-label="AuditLog data table" tabIndex={0}>
          <table className="cyber-table">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Timestamp</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Event Type</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Actor</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Action</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Risk Score</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>SHA-256 Digest</th>
                <th scope="col" style={{ padding: '0.75rem 0.5rem' }}>Previous Digest</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    {loading ? 'Loading cryptographic ledger...' : 'No audit records found.'}
                  </td>
                </tr>
              ) : (
                logs.map((log, idx) => (
                  <tr key={log._id || idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', fontWeight: 600 }}>
                      <span style={{ padding: '0.2rem 0.4rem', background: 'rgba(0, 242, 254, 0.1)', color: 'var(--accent-primary)', borderRadius: '4px', fontSize: '0.8rem' }}>
                        {log.eventType}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-primary)' }}>
                      {log.actor?.email || log.actor?.userId || 'SYSTEM'}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span className={`pill-badge pill-${log.actionTaken?.toLowerCase() || 'allow'}`} style={{ fontSize: '0.75rem' }}>
                        {log.actionTaken || 'N/A'}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', fontWeight: 600 }}>
                      {log.riskScore !== undefined ? `${(log.riskScore * 100).toFixed(1)}%` : '0.0%'}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--accent-primary)' }}>
                      {log.recordHash ? `${log.recordHash.substring(0, 12)}...` : 'N/A'}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem', fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {log.previousHash ? (
                        log.previousHash === 'GENESIS_BLOCK_EASP_2026' ? 'GENESIS_BLOCK' : `${log.previousHash.substring(0, 12)}...`
                      ) : 'GENESIS'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
