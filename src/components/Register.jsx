import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import API from '../services/api';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
     
      const response = await API.post('/api/v1/auth/register', {
        email,
        password,
      });

      console.log("Register success:", response.data);
      setSuccess("تم إنشاء الحساب بنجاح! جاري تحويلك لتسجيل الدخول...");

      setTimeout(() => {
        navigate('/');
      }, 1500);
    } catch (err) {
      
      setError(err.response?.data?.error || 'حدث خطأ أثناء إنشاء الحساب');
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#0a0a0a',
      color: '#ffffff',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        padding: '30px',
        backgroundColor: '#121212',
        border: '1px solid #333',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '380px'
      }}>
        <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>EASP Register</h2>
        
        {error && <div style={{ color: '#ff6b6b', marginBottom: '15px', fontSize: '13px', textAlign: 'center' }}>{error}</div>}
        {success && <div style={{ color: '#51cf66', marginBottom: '15px', fontSize: '13px', textAlign: 'center' }}>{success}</div>}

        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>البريد الإلكتروني:</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
              style={{ width: '100%', padding: '10px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>كلمة المرور:</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
              style={{ width: '100%', padding: '10px', background: '#222', border: '1px solid #444', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
            />
          </div>
          <button type="submit" style={{ padding: '10px', background: '#fff', color: '#000', fontWeight: 'bold', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            إنشاء حساب جديد
          </button>
          <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '13px' }}>
            <Link to="/" style={{ color: '#aaa', textDecoration: 'none' }}>لديك حساب بالفعل؟ سجل الدخول</Link>
          </div>
        </form>
      </div>
    </div>
  );
}