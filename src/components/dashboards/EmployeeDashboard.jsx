import React, { useEffect, useState } from 'react';
import { getIncidents } from '../../services/dashboardService';
import { useAuth } from '../../context/AuthContext';
import MeasuredValue from '../common/MeasuredValue';

const cardStyle = {
  background: '#121212',
  padding: '20px',
  borderRadius: '8px',
  border: '1px solid #333',
};

export default function EmployeeDashboard() {
  const { user } = useAuth();
  const [incidents, setIncidents] = useState(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;
    // Scoped to the current user's own entries via the AuditLogs `userId`
    // query param. Note: this is a UI-side convenience only, not a real
    // security boundary — the backend does not enforce that a caller can
    // only request their own userId (see dashboardService.js comment).
    getIncidents({ userId: user?.id }).then((data) => {
      if (mounted) {
        setIncidents(data);
        setLoaded(true);
      }
    });
    return () => {
      mounted = false;
    };
  }, [user?.id]);

  return (
    <div style={cardStyle}>
      <h3 style={{ marginBottom: '10px' }}>My Security Activity</h3>
      <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '20px' }}>
        Detected events, risk score, and the policy action taken. Model internals and
        performance metrics are not shown at this access level.
      </p>

      {!loaded && <p style={{ color: '#777', fontSize: '13px' }}>Loading...</p>}

      {loaded && (!incidents || incidents.length === 0) && (
        <p style={{ color: '#777', fontStyle: 'italic', fontSize: '13px' }}>
          No events recorded.
        </p>
      )}

      {loaded && incidents && incidents.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ textAlign: 'left', color: '#aaa', borderBottom: '1px solid #333' }}>
              <th style={{ padding: '8px 6px' }}>Detected Event</th>
              <th style={{ padding: '8px 6px' }}>Risk Score</th>
              <th style={{ padding: '8px 6px' }}>Policy Action</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr key={incident.id} style={{ borderBottom: '1px solid #222' }}>
                <td style={{ padding: '8px 6px' }}>{incident.detectedEvent}</td>
                <td style={{ padding: '8px 6px' }}><MeasuredValue value={incident.riskScore} /></td>
                <td style={{ padding: '8px 6px' }}><MeasuredValue value={incident.policyAction} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
