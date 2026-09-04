import React, { useState } from 'react';

export default function PolicyAdmin() {
  const [threshold, setThreshold] = useState('75');
  const [action, setAction] = useState('Escalate');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSavePolicy = (e) => {
    e.preventDefault();
    
    console.log("Policy Saved:", { threshold, action });
    setSuccessMsg('تم حفظ وتحديث السياسة الأمنية بنجاح!');
    setTimeout(() => setSuccessMsg(''), 3000);
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#121212', border: '1px solid #333', borderRadius: '8px', color: '#fff', marginTop: '20px' }}>
      <h3>إدارة سياسات الأمان (Policy Configuration - Phase 5)</h3>
      <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '20px' }}>
  تحكم في عتبات الكشف وإجراءات النظام عند رصد مخاطر أو تسريب بيانات.
      </p>

      {successMsg && <div style={{ color: '#51cf66', marginBottom: '15px', fontSize: '13px' }}>{successMsg}</div>}

      <form onSubmit={handleSavePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '15px', maxWidth: '400px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>عتبة الخطر (Risk Threshold %):</label>
          <input 
            type="number" 
            value={threshold} 
            onChange={(e) => setThreshold(e.target.value)} 
            style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>الإجراء المتخذ (Enforcement Action):</label>
          <select 
            value={action} 
            onChange={(e) => setAction(e.target.value)}
            style={{ width: '100%', padding: '8px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
          >
            <option value="Allow">السماح (Allow)</option>
            <option value="Escalate">تصعيد للمراجع (Escalate)</option>
            <option value="Block">حظر فوري (Block)</option>
          </select>
        </div>

        <button type="submit" style={{ padding: '10px', background: '#fff', color: '#000', fontWeight: 'bold', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          حفظ السياسة
        </button>
      </form>
    </div>
  );
}