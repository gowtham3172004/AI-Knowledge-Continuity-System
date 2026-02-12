/**
 * API Configuration - Auto-detects correct backend URL
 * 
 * This bypasses Vercel environment variable issues by detecting
 * the correct API URL based on the current hostname.
 */

// Production backend URL - HARDCODED for reliability
const PRODUCTION_API_URL = 'https://ai-knowledge-continuity-system-production.up.railway.app';

// Local development URL
const LOCAL_API_URL = 'http://localhost:8000';

/**
 * Get the correct API URL based on current environment
 * This runs at runtime, not build time, so it always works correctly
 */
export const getApiUrl = (): string => {
  // Check if we're in a browser environment
  if (typeof window === 'undefined') {
    return LOCAL_API_URL;
  }

  const hostname = window.location.hostname;

  // Local development
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    console.log('[Config] Using LOCAL API:', LOCAL_API_URL);
    return LOCAL_API_URL;
  }

  // Production (Vercel deployment)
  console.log('[Config] Using PRODUCTION API:', PRODUCTION_API_URL);
  return PRODUCTION_API_URL;
};

// Export the API URL for use throughout the app
export const API_URL = getApiUrl();
