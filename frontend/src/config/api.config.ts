/**
 * API Configuration - Auto-detects correct backend URL
 * 
 * For production: uses REACT_APP_API_URL env var (set in Vercel dashboard)
 * For local dev: defaults to localhost:8000
 */

// Local development URL
const LOCAL_API_URL = 'http://localhost:8000';

/**
 * Get the correct API URL based on current environment
 */
export const getApiUrl = (): string => {
  // Build-time environment variable (set in Vercel)
  const envUrl = process.env.REACT_APP_API_URL;
  if (envUrl) {
    console.log('[Config] Using env API URL:', envUrl);
    return envUrl.replace(/\/+$/, ''); // strip trailing slash
  }

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

  // Production fallback — should be overridden by REACT_APP_API_URL
  console.warn('[Config] REACT_APP_API_URL not set, using fallback');
  return LOCAL_API_URL;
};

// Export the API URL for use throughout the app
export const API_URL = getApiUrl();
