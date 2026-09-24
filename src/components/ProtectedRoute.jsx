import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const pageStyle = {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  backgroundColor: '#0a0a0a',
  color: '#ffffff',
  fontFamily: 'Arial, sans-serif',
};

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={pageStyle}>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div style={pageStyle}>
        <div>
          <h2>Access denied</h2>
          <p style={{ color: '#aaa', fontSize: '14px' }}>
            Your role ({user.role || 'unknown'}) is not permitted to view this page.
          </p>
        </div>
      </div>
    );
  }

  return children;
}
