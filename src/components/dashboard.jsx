import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [threshold, setThreshold] = useState('75');
  const [action, setAction] = useState('Escalate');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSavePolicy = (e) => {
    e.preventDefault();
    console.log("Policy Saved:", { threshold, action });
    setSuccessMsg('Policy updated successfully!');
    setTimeout(() => setSuccessMsg(''), 3000);
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
        <h1>EASP - Security Dashboard</h1>
        <Link to="/" style={{ color: '#ff4444', textDecoration: 'none', fontWeight: 'bold' }}>Logout</Link>
      </header>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div style={{ background: '#121212', padding: '20px', borderRadius: '8px', border: '1px solid #333' }}>
          <h3>System Status</h3>
          <p style={{ color: '#4CAF50', fontWeight: 'bold', marginTop: '10px' }}>● Operational</p>
        </div>
        <div style={{ background: '#121212', padding: '20px', borderRadius: '8px', border: '1px solid #333' }}>
          <h3>Security Alerts</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '10px' }}>0</p>
        </div>
      </div>

      <div style={{ background: '#121212', padding: '25px', borderRadius: '8px', border: '1px solid #333', maxWidth: '600px', direction: 'ltr', textAlign: 'left' }}>
        <h3 style={{ marginBottom: '10px' }}>Policy Configuration</h3>
        <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '20px' }}>
          Manage threat detection thresholds and automated enforcement actions.
        </p>

        {successMsg && <div style={{ color: '#51cf66', marginBottom: '15px', fontSize: '13px' }}>{successMsg}</div>}

        <form onSubmit={handleSavePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Risk Threshold (%):</label>
            <input 
              type="number" 
              value={threshold} 
              onChange={(e) => setThreshold(e.target.value)} 
              style={{ width: '100%', padding: '10px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Enforcement Action:</label>
            <select 
              value={action} 
              onChange={(e) => setAction(e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
            >
              <option value="Allow">Allow</option>
              <option value="Escalate">Escalate</option>
              <option value="Block">Block</option>
            </select>
          </div>

          <button type="submit" style={{ padding: '10px', background: '#fff', color: '#000', fontWeight: 'bold', border: 'none', borderRadius: '4px', cursor: 'pointer', marginTop: '5px' }}>
            Save Policy
          </button>
        </form>
      </div>
    </div>
  );
}