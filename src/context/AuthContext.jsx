import React, { createContext, useContext, useEffect, useState } from 'react';
import API, { getToken, setToken, clearToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { id, email, role }
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = async () => {
    try {
      const response = await API.get('/api/Auth/me');
      // Confirmed shape from AuthController.GetCurrentUser -> UserDto:
      // { id, email, fullName, roles: string[] }. Note it's `roles` (plural,
      // an array) — Identity supports multiple roles per user even though
      // this app's registration flow only ever assigns exactly one
      // (Employee/Analyst/Administrator). We normalize to a single `role`
      // for the UI's role-aware routing, since that's the only case the
      // dashboards need to handle; `roles` is kept as-is for anything that
      // needs the full list.
      const data = response.data;
      const currentUser = {
        ...data,
        role: Array.isArray(data.roles) ? data.roles[0] : undefined,
      };
      setUser(currentUser);
      return currentUser;
    } catch (err) {
      clearToken();
      setUser(null);
      return null;
    }
  };

  useEffect(() => {
    const bootstrap = async () => {
      if (getToken()) {
        await fetchCurrentUser();
      }
      setLoading(false);
    };
    bootstrap();
  }, []);

  // Called after a successful /auth/login call. Expects the raw axios
  // response data from the login endpoint, which per the Phase 1 JWT design
  // should include at least a token.
  const login = async (loginResponseData) => {
    if (loginResponseData?.token) {
      setToken(loginResponseData.token);
    }
    return fetchCurrentUser();
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser: fetchCurrentUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
