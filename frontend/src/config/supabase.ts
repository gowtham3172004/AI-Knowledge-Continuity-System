/**
 * Supabase Client Configuration
 * 
 * Initialize the Supabase client for authentication and database access.
 * Environment variables are injected at build time (REACT_APP_ prefix).
 * Falls back to window.__ENV__ for runtime injection in production.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Support both build-time env vars and runtime config
const getEnv = (key: string, fallback: string = ''): string => {
  // React build-time env vars
  const reactEnv = (process.env as any)[`REACT_APP_${key}`];
  if (reactEnv) return reactEnv;

  // Runtime env injection (optional, for advanced setups)
  if (typeof window !== 'undefined' && (window as any).__ENV__) {
    return (window as any).__ENV__[key] || fallback;
  }

  return fallback;
};

const supabaseUrl = getEnv('SUPABASE_URL');
const supabaseAnonKey = getEnv('SUPABASE_ANON_KEY');

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    '[Supabase] Missing configuration. Set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY environment variables.'
  );
}

export const supabase: SupabaseClient = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key',
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  }
);

export default supabase;
