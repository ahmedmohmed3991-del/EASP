import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import EmployeeDashboard from './dashboards/EmployeeDashboard';
import AnalystDashboard from './dashboards/AnalystDashboard';
import AdminDashboard from './dashboards/AdminDashboard';

// T-P11-052: role-aware routing. The role stored on the authenticated user
// (see AuthContext, hydrated from GET /api/Auth/me) decides which view
// renders — each view only requests/shows the data appropriate to that role.
function RoleDashboard({ role }) {
  switch (role) {
    case 'Administrator':
      return <AdminDashboard />;
    case 'Analyst':
      return <AnalystDashboard />;
    case 'Employee':
      return <EmployeeDashboard />;
    default:
      return (
        <p style={{ color: '#ff6b6b', fontSize: '14px' }}>
          Unrecognized role &quot;{role || 'none'}&quot; — no dashboard view is defined for it.
        </p>
      );
  }
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div style={{
      padding: '40px',
      backgroundColor: '#0a0a0a',
      color: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '20px', marginBottom: '30px' }}>
        <div>
          <h1 style={{ margin: 0 }}>EASP - Security Dashboard</h1>
          {user && (
            <p style={{ margin: '5px 0 0', color: '#aaa', fontSize: '13px' }}>
              {user.email} · {(user.roles && user.roles.join(', ')) || 'unknown role'}
            </p>
          )}
        </div>
        <Link
          to="/"
          onClick={handleLogout}
          style={{ color: '#ff4444', textDecoration: 'none', fontWeight: 'bold' }}
        >
          Logout
        </Link>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div style={{ background: '#121212', padding: '20px', borderRadius: '8px', border: '1px solid #333' }}>
          <h3>System Status</h3>
          <p style={{ color: '#4CAF50', fontWeight: 'bold', marginTop: '10px' }}>● Operational</p>
        </div>
      </div>

      <RoleDashboard role={user?.role} />
    </div>
  );
}
