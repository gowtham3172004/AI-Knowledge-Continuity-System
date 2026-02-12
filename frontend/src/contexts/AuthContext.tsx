/**
 * Auth context - manages user login state and tokens
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { API_URL } from '../config/api.config';

// Use centralized API URL config
const API = API_URL;

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
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      // Check if response has content before parsing
      const text = await res.text();
      
      if (!res.ok) {
        let errorMessage = 'Login failed';
        try {
          const err = JSON.parse(text);
          errorMessage = err.detail || err.message || errorMessage;
        } catch {
          errorMessage = text || errorMessage;
        }
        throw new Error(errorMessage);
      }
      
      // Parse success response
      const data = JSON.parse(text);
      setUser(data.user);
      setToken(data.token);
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error. Please check if the backend is running and try again.');
    }
  };

  const register = async (email: string, password: string, fullName: string, role: string) => {
    try {
      const res = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName, role }),
      });
      
      // Check if response has content before parsing
      const text = await res.text();
      
      if (!res.ok) {
        let errorMessage = 'Registration failed';
        try {
          const err = JSON.parse(text);
          errorMessage = err.detail || err.message || errorMessage;
        } catch {
          errorMessage = text || errorMessage;
        }
        throw new Error(errorMessage);
      }
      
      // Parse success response
      const data = JSON.parse(text);
      setUser(data.user);
      setToken(data.token);
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error. Please check if the backend is running and try again.');
    }
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
