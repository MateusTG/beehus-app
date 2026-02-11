import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login?: string | null;
}

interface AuthContextType {
  token: string | null;
  refreshTokenValue: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getTokenExpiryMs = (token: string): number | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [refreshTokenValue, setRefreshTokenValue] = useState<string | null>(
    localStorage.getItem('refresh_token')
  );
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('access_token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('access_token');
    }
  }, [token]);

  useEffect(() => {
    if (refreshTokenValue) {
      localStorage.setItem('refresh_token', refreshTokenValue);
    } else {
      localStorage.removeItem('refresh_token');
    }
  }, [refreshTokenValue]);

  const logout = useCallback(() => {
    setToken(null);
    setRefreshTokenValue(null);
    setUser(null);
  }, []);

  const fetchCurrentUser = useCallback(async () => {
    if (!token) return;
    try {
      const response = await axios.get(`${apiBaseUrl}/users/me`);
      setUser(response.data);
    } catch (error) {
      logout();
    }
  }, [token, logout]);

  const refreshToken = useCallback(async () => {
    if (!refreshTokenValue) return;
    try {
      const response = await axios.post(`${apiBaseUrl}/auth/refresh`, {
        refresh_token: refreshTokenValue,
      });
      const { access_token, refresh_token } = response.data;
      setToken(access_token);
      setRefreshTokenValue(refresh_token);
    } catch (error) {
      logout();
    }
  }, [refreshTokenValue, logout]);

  const login = useCallback(async (accessToken: string, refreshTokenRaw: string) => {
    setToken(accessToken);
    setRefreshTokenValue(refreshTokenRaw);
    try {
      const response = await axios.get(`${apiBaseUrl}/users/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setUser(response.data);
    } catch (error) {
      logout();
    }
  }, [logout]);

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token, fetchCurrentUser]);

  useEffect(() => {
    if (!token || !refreshTokenValue) return;
    const expiryMs = getTokenExpiryMs(token);
    if (!expiryMs) return;

    const refreshAt = expiryMs - 60 * 1000;
    const delay = Math.max(refreshAt - Date.now(), 1000);
    const timer = window.setTimeout(() => {
      refreshToken();
    }, delay);
    return () => window.clearTimeout(timer);
  }, [token, refreshTokenValue, refreshToken]);

  return (
    <AuthContext.Provider
      value={{
        token,
        refreshTokenValue,
        user,
        isAuthenticated: !!token,
        isAdmin: user?.role === 'admin',
        login,
        logout,
        refreshToken,
        fetchCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
