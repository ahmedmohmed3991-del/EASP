import Icon from './components/Icon';
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
  const [menuOpen, setMenuOpen] = useState(false);

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

  const pages = {
    'prompt-scanner': ['Prompt security', 'Inspect sensitive data and social engineering signals before sharing a prompt.', 'prompt'],
    'voice-deepfake': ['Voice intelligence', 'Analyze voice authenticity, acoustic signals, and social engineering risk.', 'voice'],
    'incident-desk': ['Incident desk', 'Investigate security events and coordinate your response.', 'incident'],
    'audit-chain': ['Audit trail', 'Trace security decisions and verify the integrity of the ledger.', 'audit'],
    'policy-engine': ['Policy governance', 'Review the rules that guide security decisions across the platform.', 'policy'],
    'platform-metrics': ['Security overview', 'A consolidated view of incident telemetry and model evaluations.', 'chart'],
    'system-status': ['System health', 'Monitor connectivity across your security infrastructure.', 'pulse']
  };
  const page = pages[activeTab];
  const navItem = (tab, label) => (
    <button className={`nav-btn ${activeTab === tab ? 'active' : ''}`}
      aria-current={activeTab === tab ? 'page' : undefined}
      onClick={() => { setActiveTab(tab); setMenuOpen(false); }}>
      <Icon name={pages[tab][2]} /><span>{label}</span>
    </button>
  );

  return (
    <div className="app-container">
      <a className="skip-link" href="#workspace">Skip to workspace</a>
      <aside className="sidebar">
        <div className="brand-title"><span className="brand-mark"><Icon name="shield" /></span><div>EASP<span className="brand-caption">AI SECURITY PLATFORM</span></div></div>
        <button className="mobile-menu-btn" aria-expanded={menuOpen} aria-controls="workspace-navigation" onClick={() => setMenuOpen(!menuOpen)}><Icon name="menu" />Menu</button>
        <nav id="workspace-navigation" className={`nav-links ${menuOpen ? 'is-open' : ''}`} aria-label="Main navigation">
          <div className="nav-section-label">Analysis workspace</div>
          {navItem('prompt-scanner', 'Prompt security')}
          {navItem('voice-deepfake', 'Voice intelligence')}
          {isAnalystOrAdmin && <>
            <div className="nav-section-label">Security operations</div>
            {navItem('platform-metrics', 'Security overview')}
            {navItem('incident-desk', 'Incident desk')}
            {navItem('audit-chain', 'Audit trail')}
            {navItem('policy-engine', 'Policy rules')}
          </>}
          <div className="nav-section-label">Platform</div>
          {navItem('system-status', 'System health')}
        </nav>
        <div className="sidebar-footer">
          <div className="user-profile-badge">
            <span className="user-avatar">{(currentUser.name || currentUser.email || 'U').slice(0, 1).toUpperCase()}</span>
            <div className="user-details"><strong>{currentUser.name || currentUser.email}</strong><span>{currentUser.email}</span></div>
          </div>
          <span className={`role-pill role-${role.toLowerCase()}`}>{role}</span>
          <button className="logout-btn" onClick={handleLogout} title="Log out of session"><Icon name="logout" />Log out</button>
        </div>
      </aside>
      <div className="workspace-shell">
        <header className="workspace-topbar"><span>Workspace <span className="breadcrumb-separator">/</span> <strong>{page[0]}</strong></span><span className="workspace-label"><Icon name="lock" /> Enterprise AI security</span></header>
        <main className="main-content" id="workspace" tabIndex={-1}>
          <header className="page-heading"><div><span className="eyebrow">EASP / SECURITY WORKSPACE</span><h1>{page[0]}</h1><p>{page[1]}</p></div><div className="page-heading-icon"><Icon name={page[2]} /></div></header>
        {activeTab === 'prompt-scanner' && <PromptScannerPage currentUser={currentUser} />}
        {activeTab === 'voice-deepfake' && <VoiceDeepfakePage currentUser={currentUser} />}
        {activeTab === 'incident-desk' && isAnalystOrAdmin && <IncidentDeskPage currentUser={currentUser} />}
        {activeTab === 'audit-chain' && isAnalystOrAdmin && <AuditLogPage currentUser={currentUser} />}
        {activeTab === 'policy-engine' && isAnalystOrAdmin && <PolicyGovernancePage currentUser={currentUser} />}
        {activeTab === 'platform-metrics' && isAnalystOrAdmin && <PlatformMetricsPage currentUser={currentUser} />}
        {activeTab === 'system-status' && <SystemStatusPage />}
        </main>
        <footer className="workspace-footer"><span>EASP · Enterprise AI Security Platform</span><span>Voice intelligence. Informed decisions.</span></footer>
      </div>
    </div>
  );
}
