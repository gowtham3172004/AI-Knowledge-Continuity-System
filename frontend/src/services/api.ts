/**
 * API Service for AI Knowledge Continuity System
 * 
 * Centralized HTTP client for backend communication with auth support.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  QueryRequest,
  QueryResponse,
  IngestRequest,
  IngestResponse,
  HealthResponse,
  ErrorResponse,
} from '../types/api';

// Normalize API URL - ensures proper https:// prefix
const normalizeBaseURL = (url: string): string => {
  if (!url) return 'http://localhost:8000';
  
  let normalized = url.trim().replace(/\/$/, '');
  
  // If URL doesn't have protocol, add it
  if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
    normalized = normalized.includes('localhost') 
      ? `http://${normalized}` 
      : `https://${normalized}`;
  }
  
  return normalized;
};

// Configure base URL from environment or default to localhost
const RAW_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const BASE_URL = normalizeBaseURL(RAW_BASE_URL);

// Debug log - remove after confirming fix works
console.log('[API] Base URL Config:', { raw: RAW_BASE_URL, normalized: BASE_URL });

/**
 * API Client Configuration
 */
class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${BASE_URL}/api`,
      timeout: 60000, // 60 seconds for LLM responses
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor — inject auth token automatically
    this.client.interceptors.request.use(
      (config) => {
        // Inject auth token from localStorage
        try {
          const authData = localStorage.getItem('auth');
          if (authData) {
            const { token } = JSON.parse(authData);
            if (token) {
              config.headers.Authorization = `Bearer ${token}`;
            }
          }
        } catch {}

        if (process.env.NODE_ENV === 'development') {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
        }
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        if (process.env.NODE_ENV === 'development') {
          console.log(`[API] Response:`, response.data);
        }
        return response;
      },
      (error: AxiosError<ErrorResponse>) => {
        console.error('[API] Response error:', error.response?.data || error.message);
        return Promise.reject(this.formatError(error));
      }
    );
  }

  /**
   * Format axios error into user-friendly message
   */
  private formatError(error: AxiosError<ErrorResponse>): Error {
    if (error.response) {
      const data = error.response.data as any;
      // Handle FastAPI validation detail
      if (data?.detail) {
        return new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
      }
      const errorData = data?.error;
      if (errorData) {
        return new Error(errorData.message || 'Server error occurred');
      }
      return new Error(`Server error: ${error.response.status}`);
    } else if (error.request) {
      return new Error('Unable to reach the server. Please check your connection.');
    } else {
      return new Error(error.message || 'An unexpected error occurred');
    }
  }

  /**
   * Query the knowledge system
   */
  query = async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await this.client.post<QueryResponse>('/query', request);
    return response.data;
  }

  /**
   * Ingest new documents
   */
  ingest = async (request: IngestRequest): Promise<IngestResponse> => {
    const response = await this.client.post<IngestResponse>('/ingest', request);
    return response.data;
  }

  /**
   * Health check
   */
  healthCheck = async (): Promise<HealthResponse> => {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * Readiness check
   */
  readinessCheck = async (): Promise<HealthResponse> => {
    const response = await this.client.get<HealthResponse>('/health/ready');
    return response.data;
  }

  /**
   * Get system info
   */
  getSystemInfo = async (): Promise<HealthResponse> => {
    const response = await this.client.get<HealthResponse>('/health/info');
    return response.data;
  }

  // ==================== Conversation APIs ====================

  /**
   * List all conversations for current user
   */
  listConversations = async (): Promise<any[]> => {
    const response = await this.client.get('/conversations/');
    return response.data;
  }

  /**
   * Create a new conversation
   */
  createConversation = async (id: string, title: string): Promise<any> => {
    const response = await this.client.post('/conversations/', { id, title });
    return response.data;
  }

  /**
   * Update conversation title
   */
  updateConversation = async (id: string, title: string): Promise<void> => {
    await this.client.put(`/conversations/${id}`, { title });
  }

  /**
   * Delete a conversation
   */
  deleteConversation = async (id: string): Promise<void> => {
    await this.client.delete(`/conversations/${id}`);
  }

  /**
   * Get messages for a conversation
   */
  getMessages = async (conversationId: string): Promise<any[]> => {
    const response = await this.client.get(`/conversations/${conversationId}/messages`);
    return response.data;
  }

  /**
   * Save a message to a conversation
   */
  saveMessage = async (conversationId: string, msg: { id: string; role: string; content: string; response_data?: string }): Promise<void> => {
    await this.client.post(`/conversations/${conversationId}/messages`, msg);
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export individual methods for convenience
export const { query, ingest, healthCheck, readinessCheck, getSystemInfo } = apiClient;
