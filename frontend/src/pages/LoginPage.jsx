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
    <div className="auth-wrapper">
      <div className="auth-header">
        <span className="role-pill role-analyst" style={{ marginBottom: '0.75rem', display: 'inline-block' }}>
          Cybersecurity & AI Defense
        </span>
        <h1>EASP Platform</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
          Enterprise AI Security Platform Authentication
        </p>
      </div>

      {error && (
        <div style={{ background: 'rgba(244,63,94,0.15)', border: '1px solid var(--accent-rose)', color: 'var(--accent-rose)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleLogin}>
        <div className="input-group">
          <label>Enterprise Identity (Email)</label>
          <input
            type="email"
            className="cyber-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="input-group">
          <label>Password</label>
          <input
            type="password"
            className="cyber-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} disabled={loading}>
          {loading ? 'Authenticating...' : 'Sign In to EASP'}
        </button>
      </form>

      <div style={{ marginTop: '2rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: '0.75rem' }}>
          Quick Demo Role Selection:
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
    </div>
  );
}
