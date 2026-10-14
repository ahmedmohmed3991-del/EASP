import React, { useState, useEffect } from 'react';
import { getCurrentUser, setCurrentUser, setAuthToken, getAuthToken } from './services/apiClient';
import LoginPage from './pages/LoginPage.jsx';
import PromptScannerPage from './pages/PromptScannerPage.jsx';
import VoiceDeepfakePage from './pages/VoiceDeepfakePage.jsx';
import IncidentDeskPage from './pages/IncidentDeskPage.jsx';
import AuditLogPage from './pages/AuditLogPage.jsx';
import PolicyGovernancePage from './pages/PolicyGovernancePage.jsx';
import PlatformMetricsPage from './pages/PlatformMetricsPage.jsx';
import SystemStatusPage from './pages/SystemStatusPage.jsx';

export default function App() {
  const [currentUser, setLocalCurrentUser] = useState(getCurrentUser());
  const [activeTab, setActiveTab] = useState('prompt-scanner');

  useEffect(() => {
    // If not logged in, ensure we stay on prompt-scanner by default once logged in
    const token = getAuthToken();
    const user = getCurrentUser();
    if (token && user) {
      setLocalCurrentUser(user);
    }

    const onAuthLogout = () => {
      setLocalCurrentUser(null);
    };
    window.addEventListener('auth:logout', onAuthLogout);
    return () => window.removeEventListener('auth:logout', onAuthLogout);
  }, []);

  const handleLoginSuccess = (user) => {
    setLocalCurrentUser(user);
    setActiveTab('prompt-scanner');
  };

  const handleLogout = () => {
    setAuthToken(null);
    setCurrentUser(null);
    setLocalCurrentUser(null);
  };

  if (!currentUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const role = currentUser.role || 'Employee';
  const isAnalystOrAdmin = ['Analyst', 'Administrator'].includes(role);
  const isAdmin = role === 'Administrator';

  return (
    <div className="app-container">
      {/* Top Cyber Navigation Bar */}
      <header className="navbar">
        <div className="brand-area">
          <div className="brand-title">
            <span className="badge-platform">EASP</span>
            <span>Enterprise AI Security Platform</span>
          </div>

          <nav className="nav-links">
            <button
              className={`nav-btn ${activeTab === 'prompt-scanner' ? 'active' : ''}`}
              onClick={() => setActiveTab('prompt-scanner')}
            >
              DLP & Prompt
            </button>
            <button
              className={`nav-btn ${activeTab === 'voice-deepfake' ? 'active' : ''}`}
              onClick={() => setActiveTab('voice-deepfake')}
            >
              Voice & Deepfake
            </button>

            {isAnalystOrAdmin && (
              <>
                <button
                  className={`nav-btn ${activeTab === 'incident-desk' ? 'active' : ''}`}
                  onClick={() => setActiveTab('incident-desk')}
                >
                  Incident Desk
                </button>
                <button
                  className={`nav-btn ${activeTab === 'audit-chain' ? 'active' : ''}`}
                  onClick={() => setActiveTab('audit-chain')}
                >
                  Audit Trail
                </button>
                <button
                  className={`nav-btn ${activeTab === 'policy-engine' ? 'active' : ''}`}
                  onClick={() => setActiveTab('policy-engine')}
                >
                  Policy Rules
                </button>
                <button
                  className={`nav-btn ${activeTab === 'platform-metrics' ? 'active' : ''}`}
                  onClick={() => setActiveTab('platform-metrics')}
                >
                  SOC Telemetry
                </button>
              </>
            )}

            <button
              className={`nav-btn ${activeTab === 'system-status' ? 'active' : ''}`}
              onClick={() => setActiveTab('system-status')}
            >
              Health
            </button>
          </nav>
        </div>

        {/* User Identity & Logout */}
        <div className="user-profile-badge">
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{currentUser.name || currentUser.email}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{currentUser.email}</div>
          </div>
          <span className={`role-pill role-${role.toLowerCase()}`}>
            {role}
          </span>
          <button className="logout-btn" onClick={handleLogout} title="Log out of session">
            Logout
          </button>
        </div>
      </header>

      {/* Main Tabbed View Workspace */}
      <main className="main-content">
        {activeTab === 'prompt-scanner' && <PromptScannerPage currentUser={currentUser} />}
        {activeTab === 'voice-deepfake' && <VoiceDeepfakePage currentUser={currentUser} />}
        {activeTab === 'incident-desk' && isAnalystOrAdmin && <IncidentDeskPage currentUser={currentUser} />}
        {activeTab === 'audit-chain' && isAnalystOrAdmin && <AuditLogPage currentUser={currentUser} />}
        {activeTab === 'policy-engine' && isAnalystOrAdmin && <PolicyGovernancePage currentUser={currentUser} />}
        {activeTab === 'platform-metrics' && isAnalystOrAdmin && <PlatformMetricsPage currentUser={currentUser} />}
        {activeTab === 'system-status' && <SystemStatusPage />}
      </main>
    </div>
  );
}
