import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as authApi from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = authApi.getStoredToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const profile = await authApi.fetchCurrentUser();
      setUser(profile);
    } catch {
      authApi.setStoredToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(async (username, password) => {
    const data = await authApi.login(username, password);
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  const hasPermission = useCallback((code) => {
    if (!user) return false;
    if (user.roles?.includes('administrator') || user.roles?.includes('system')) return true;
    return user.permissions?.includes(code);
  }, [user]);

  const value = useMemo(() => ({
    user,
    loading,
    login,
    logout,
    hasPermission,
    refreshUser: loadUser,
    isAuthenticated: Boolean(user),
  }), [user, loading, login, logout, hasPermission, loadUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
