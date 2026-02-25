/**
 * Auth Context — Supabase Authentication
 * 
 * Manages user authentication state using Supabase Auth.
 * Provides login, register, logout, and session persistence.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase } from '../config/supabase';
import { Session, User } from '@supabase/supabase-js';

export interface AppUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextType {
  user: AppUser | null;
  session: Session | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

/** Convert Supabase User to our app user shape */
const toAppUser = (user: User): AppUser => ({
  id: user.id,
  email: user.email || '',
  full_name: user.user_metadata?.full_name || user.email?.split('@')[0] || '',
  role: user.user_metadata?.role || 'developer',
});

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<AppUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize: get existing session and listen for auth changes
  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session: s } }) => {
      setSession(s);
      if (s?.user) setUser(toAppUser(s.user));
      setIsLoading(false);
    });

    // Listen for auth state changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, s) => {
        setSession(s);
        setUser(s?.user ? toAppUser(s.user) : null);
        setIsLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const token = session?.access_token || null;

  const login = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw new Error(error.message);
    if (data.user) setUser(toAppUser(data.user));
  };

  const register = async (email: string, password: string, fullName: string, role: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          role: role,
        },
      },
    });
    if (error) throw new Error(error.message);
    if (data.user) setUser(toAppUser(data.user));
  };

  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    localStorage.removeItem('conversations');
  };

  return (
    <AuthContext.Provider value={{
      user,
      session,
      token,
      isAuthenticated: !!session,
      isLoading,
      login,
      register,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
