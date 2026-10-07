import React, { useEffect, useState, useCallback } from 'react';
import StatusRow from '../components/StatusRow.jsx';
import { fetchBackendHealth, fetchAIHealth } from '../services/healthService.js';

const POLL_INTERVAL_MS = 10000;

// Phase 0 infrastructure monitoring screen.
// This is NOT the final EASP Security Dashboard - it only reflects
// live connectivity of Frontend / Backend / AI Service / Database,
// derived from the actual backend health responses.
export default function SystemStatusPage() {
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState(null);
  const [status, setStatus] = useState({
    frontend: { connected: true, detail: 'Rendering in browser' },
    backend: { connected: false, detail: 'Not checked yet' },
    aiService: { connected: false, detail: 'Not checked yet' },
    database: { connected: false, detail: 'Not checked yet' }
  });

  const checkHealth = useCallback(async () => {
    setLoading(true);

    // Backend + Database (Database state comes from inside the backend response)
    let backendConnected = false;
    let dbConnected = false;
    let backendDetail = 'Unreachable';
    let dbDetail = 'Unreachable';

    try {
      const backendData = await fetchBackendHealth();
      backendConnected = backendData.status === 'ok';
      backendDetail = `HTTP 200 - ${backendData.service || 'backend'}`;

      const mongoInfo = backendData.dependencies && backendData.dependencies.mongodb;
      if (mongoInfo) {
        dbConnected = Boolean(mongoInfo.connected);
        dbDetail = `state: ${mongoInfo.state}`;
      }
    } catch (err) {
      backendDetail = err.message;
      dbDetail = 'Backend unreachable, state unknown';
    }

    // AI Service (checked through the backend's /health/ai proxy)
    let aiConnected = false;
    let aiDetail = 'Unreachable';

    try {
      const aiData = await fetchAIHealth();
      aiConnected = Boolean(aiData.ai_service && aiData.ai_service.reachable);
      aiDetail = aiConnected
        ? `HTTP 200 via backend (${aiData.ai_service.response_time_ms} ms)`
        : (aiData.ai_service && aiData.ai_service.error) || 'Unreachable';
    } catch (err) {
      aiDetail = err.message;
    }

    setStatus({
      frontend: { connected: true, detail: 'Rendering in browser' },
      backend: { connected: backendConnected, detail: backendDetail },
      aiService: { connected: aiConnected, detail: aiDetail },
      database: { connected: dbConnected, detail: dbDetail }
    });

    setLastChecked(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <div className="page-pane">
      <section className="card">
        <div className="card-header">
          <h2>System Status</h2>
          <button onClick={checkHealth} disabled={loading} className="refresh-btn">
            {loading ? 'Checking...' : 'Refresh'}
          </button>
        </div>

        <StatusRow label="Frontend" connected={status.frontend.connected} loading={false} detail={status.frontend.detail} />
        <StatusRow label="Backend" connected={status.backend.connected} loading={loading} detail={status.backend.detail} />
        <StatusRow label="AI Service" connected={status.aiService.connected} loading={loading} detail={status.aiService.detail} />
        <StatusRow label="Database" connected={status.database.connected} loading={loading} detail={status.database.detail} />

        <div className="last-checked">
          {lastChecked ? `Last checked: ${lastChecked.toLocaleTimeString()}` : ''}
        </div>
      </section>

      <footer className="footer">
        Connectivity is checked every 10 seconds. Service availability does not indicate an analysis result.
      </footer>
    </div>
  );
}
