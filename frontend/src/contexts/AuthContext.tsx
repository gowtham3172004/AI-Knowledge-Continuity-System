/**
 * Auth context - manages user login state and tokens
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('auth');
    if (saved) {
      try {
        const { user: u, token: t } = JSON.parse(saved);
        setUser(u);
        setToken(t);
      } catch { /* ignore */ }
    }
    setIsLoading(false);
  }, []);

  // Persist to localStorage
  useEffect(() => {
    if (user && token) {
      localStorage.setItem('auth', JSON.stringify({ user, token }));
    } else {
      localStorage.removeItem('auth');
    }
  }, [user, token]);

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setUser(data.user);
    setToken(data.token);
  };

  const register = async (email: string, password: string, fullName: string, role: string) => {
    const res = await fetch(`${API}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName, role }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    setUser(data.user);
    setToken(data.token);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth');
    localStorage.removeItem('conversations');
  };

  return (
    <AuthContext.Provider value={{
      user, token, isAuthenticated: !!token, isLoading,
      login, register, logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
