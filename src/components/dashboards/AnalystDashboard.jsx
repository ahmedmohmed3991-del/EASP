import React, { useEffect, useState } from 'react';
import { getAuditLogs, getIncidents } from '../../services/dashboardService';
import MeasuredValue from '../common/MeasuredValue';

const cardStyle = {
  background: '#121212',
  padding: '20px',
  borderRadius: '8px',
  border: '1px solid #333',
  marginBottom: '20px',
};

function DataTable({ rows, columns, emptyText }) {
  if (!rows || rows.length === 0) {
    return <p style={{ color: '#777', fontStyle: 'italic', fontSize: '13px' }}>{emptyText}</p>;
  }
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ textAlign: 'left', color: '#aaa', borderBottom: '1px solid #333' }}>
            {columns.map((col) => (
              <th key={col.key} style={{ padding: '8px 6px', whiteSpace: 'nowrap' }}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} style={{ borderBottom: '1px solid #222' }}>
              {columns.map((col) => (
                <td key={col.key} style={{ padding: '8px 6px' }}>
                  {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AnalystDashboard() {
  const [incidents, setIncidents] = useState(null);
  const [auditPage, setAuditPage] = useState(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;
    Promise.all([getIncidents(), getAuditLogs({ pageSize: 50 })]).then(([incidentData, auditData]) => {
      if (mounted) {
        setIncidents(incidentData);
        setAuditPage(auditData);
        setLoaded(true);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!loaded) {
    return <p style={{ color: '#777', fontSize: '13px' }}>Loading...</p>;
  }

  return (
    <>
      <div style={cardStyle}>
        <h3 style={{ marginBottom: '10px' }}>Detected Incidents</h3>
        <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '20px' }}>
          Derived from audit log entries with a security-decision action (risk fusion /
          AI text analysis / AI voice analysis). Reasons are only recorded for
          risk-fusion decisions — AI text/voice entries do not carry per-model output
          in the audit trail.
        </p>
        <DataTable
          rows={incidents}
          emptyText="No incidents recorded."
          columns={[
            { key: 'timestamp', label: 'Timestamp' },
            { key: 'userEmail', label: 'User' },
            { key: 'detectedEvent', label: 'Detected Event' },
            { key: 'riskScore', label: 'Risk Score', render: (v) => <MeasuredValue value={v} /> },
            { key: 'policyAction', label: 'Policy Action', render: (v) => <MeasuredValue value={v} /> },
            { key: 'reasons', label: 'Model Result / Reasons', render: (v) => <MeasuredValue value={v} /> },
          ]}
        />
      </div>

      <div style={cardStyle}>
        <h3 style={{ marginBottom: '10px' }}>Audit Log</h3>
        <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '20px' }}>
          Append-only record of all logged actions (Phase 5), most recent first.
          {auditPage ? ` Showing ${auditPage.items.length} of ${auditPage.totalCount}.` : ''}
        </p>
        <DataTable
          rows={auditPage?.items}
          emptyText="No audit log entries recorded."
          columns={[
            { key: 'timestamp', label: 'Timestamp' },
            { key: 'userEmail', label: 'User' },
            { key: 'action', label: 'Action' },
            { key: 'resource', label: 'Resource' },
            { key: 'statusCode', label: 'Status' },
          ]}
        />
      </div>
    </>
  );
}
