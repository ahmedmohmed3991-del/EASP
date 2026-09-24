import React, { useState } from 'react';
import AnalystDashboard from './AnalystDashboard';
import MeasuredValue from '../common/MeasuredValue';

const cardStyle = {
  background: '#121212',
  padding: '20px',
  borderRadius: '8px',
  border: '1px solid #333',
  marginBottom: '20px',
};

function MeasuredPerformance() {
  // getEvaluationResults() intentionally makes no network call: the backend
  // (verified against EASP.Api's controllers, DbContext, and Program.cs) has
  // no evaluation-results table or endpoint at all yet. Phase 13 (final EER/
  // F1/DLP-metrics measurement), which is what would populate this, hasn't
  // been implemented. This section is wired and ready — once a real
  // endpoint exists, only dashboardService.js needs to change.
  const [results] = useState(null);

  return (
    <div style={cardStyle}>
      <h3 style={{ marginBottom: '10px' }}>Measured Performance</h3>
      <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '20px' }}>
        Final metrics from Phase 13 evaluation. No evaluation-results endpoint exists in
        the backend yet, so this correctly shows the Phase 11 fallback rather than a
        placeholder number.
      </p>

      {(!results || results.length === 0) && (
        <MeasuredValue value={null} />
      )}

      {results && results.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ textAlign: 'left', color: '#aaa', borderBottom: '1px solid #333' }}>
              <th style={{ padding: '8px 6px' }}>Model</th>
              <th style={{ padding: '8px 6px' }}>Metric</th>
              <th style={{ padding: '8px 6px' }}>Value</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result, idx) => (
              <tr key={result.id || idx} style={{ borderBottom: '1px solid #222' }}>
                <td style={{ padding: '8px 6px' }}>{result.model ?? '—'}</td>
                <td style={{ padding: '8px 6px' }}>{result.metric ?? '—'}</td>
                <td style={{ padding: '8px 6px' }}>
                  <MeasuredValue value={result.value} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// The Phase 5 policy configuration stub, relocated (not duplicated) from the
// old dashboard.jsx into the Administrator-only view. Behavior is unchanged
// from the original stub (local-only, no backend call yet).
function PolicyConfiguration() {
  const [threshold, setThreshold] = React.useState('75');
  const [action, setAction] = React.useState('Escalate');
  const [successMsg, setSuccessMsg] = React.useState('');

  const handleSavePolicy = (e) => {
    e.preventDefault();
    console.log('Policy Saved:', { threshold, action });
    setSuccessMsg('Policy updated successfully!');
    setTimeout(() => setSuccessMsg(''), 3000);
  };

  return (
    <div style={{ ...cardStyle, maxWidth: '600px' }}>
      <h3 style={{ marginBottom: '10px' }}>Policy Configuration</h3>
      <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '20px' }}>
        Manage threat detection thresholds and automated enforcement actions.
      </p>

      {successMsg && <div style={{ color: '#51cf66', marginBottom: '15px', fontSize: '13px' }}>{successMsg}</div>}

      <form onSubmit={handleSavePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Risk Threshold (%):</label>
          <input
            type="number"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            style={{ width: '100%', padding: '10px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Enforcement Action:</label>
          <select
            value={action}
            onChange={(e) => setAction(e.target.value)}
            style={{ width: '100%', padding: '10px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
          >
            <option value="Allow">Allow</option>
            <option value="Escalate">Escalate</option>
            <option value="Block">Block</option>
          </select>
        </div>
        <button type="submit" style={{ padding: '10px', background: '#fff', color: '#000', fontWeight: 'bold', border: 'none', borderRadius: '4px', cursor: 'pointer', marginTop: '5px' }}>
          Save Policy
        </button>
      </form>
    </div>
  );
}

export default function AdminDashboard() {
  return (
    <>
      <AnalystDashboard />
      <MeasuredPerformance />
      <PolicyConfiguration />
    </>
  );
}
