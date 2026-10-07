import Icon from '../components/Icon';
import SignalArtwork from '../components/SignalArtwork';
import React, { useState } from 'react';
import { authApi, setAuthToken, setCurrentUser } from '../services/apiClient';

export default function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState('analyst@easp.local');
  const [password, setPassword] = useState('Analyst@Easp2026!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await authApi.login(email, password);
      setAuthToken(res.token);
      setCurrentUser(res.user);
      onLoginSuccess(res.user);
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const selectRole = (userEmail, userPass) => {
    setEmail(userEmail);
    setPassword(userPass);
    setError(null);
  };

  return (
    <main className="auth-layout">
      <section className="auth-story" aria-label="About EASP">
        <div className="brand-title"><span className="brand-mark"><Icon name="shield" /></span><div>EASP<span className="brand-caption">AI SECURITY PLATFORM</span></div></div>
        <div className="auth-story-copy"><span className="eyebrow">VOICE INTELLIGENCE. HUMAN CONFIDENCE.</span><h1>Hear the signal.<br /><em>See the threat.</em></h1><p>Bring voice deepfake detection, prompt protection, and security intelligence into one focused workspace.</p></div>
        <SignalArtwork />
        <div className="auth-capabilities"><span><Icon name="voice" /> Voice analysis</span><span><Icon name="shield" /> Data protection</span><span><Icon name="audit" /> Audit visibility</span></div>
        <div className="auth-story-footer">Enterprise AI Security Platform <span>Built for security operations</span></div>
      </section>
      <section className="auth-panel"><div className="auth-wrapper">
      <div className="auth-header"><span className="eyebrow">ACCESS YOUR WORKSPACE</span><h2>Welcome back.</h2><p>Sign in to your EASP account to continue.</p></div>

      {error && (
        <div role="alert" style={{ background: 'rgba(244,63,94,0.15)', border: '1px solid var(--accent-rose)', color: 'var(--accent-rose)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleLogin} aria-busy={loading}>
        <div className="input-group">
          <label htmlFor="login-email">Enterprise email</label>
          <input
            id="login-email"
            autoComplete="username"
            type="email"
            className="cyber-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="input-group">
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            autoComplete="current-password"
            type="password"
            className="cyber-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} disabled={loading}>
          {loading ? 'Authenticating...' : 'Sign In to EASP'}<Icon name="arrow" />
        </button>
      </form>

      <div style={{ marginTop: '2rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: '0.75rem' }}>
          Demo workspace · Choose a role
        </p>
        <div className="role-switcher-grid">
          <button
            type="button"
            className="role-switch-btn"
            onClick={() => selectRole('employee@easp.local', 'Employee@Easp2026!')}
          >
            Employee
          </button>
          <button
            type="button"
            className="role-switch-btn"
            onClick={() => selectRole('analyst@easp.local', 'Analyst@Easp2026!')}
          >
            Analyst (SOC)
          </button>
          <button
            type="button"
            className="role-switch-btn"
            onClick={() => selectRole('admin@easp.local', 'Admin@Easp2026!')}
          >
            Administrator
          </button>
        </div>
      </div>
      <p className="auth-footnote"><Icon name="lock" /> Authorized access to your security workspace</p>
      </div></section>
    </main>
  );
}
