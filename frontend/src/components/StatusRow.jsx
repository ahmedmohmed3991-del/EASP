import React from 'react';

// Renders a single system-status row: label + CONNECTED/DISCONNECTED badge.
export default function StatusRow({ label, connected, loading, detail }) {
  let badgeClass = 'badge badge-loading';
  let badgeText = 'CHECKING...';

  if (!loading) {
    badgeClass = connected ? 'badge badge-connected' : 'badge badge-disconnected';
    badgeText = connected ? 'CONNECTED' : 'DISCONNECTED';
  }

  return (
    <div className="status-row">
      <div className="status-label">{label}</div>
      <div className="status-right">
        <span className={badgeClass}>{badgeText}</span>
        {detail ? <div className="status-detail">{detail}</div> : null}
      </div>
    </div>
  );
}
