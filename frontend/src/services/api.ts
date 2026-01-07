/**
 * API Service for AI Knowledge Continuity System
 * 
 * Centralized HTTP client for backend communication.
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

// Configure base URL from environment or default to localhost
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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

    // Request interceptor for logging (development only)
    this.client.interceptors.request.use(
      (config) => {
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
      // Server responded with error
      const errorData = error.response.data?.error;
      if (errorData) {
        return new Error(errorData.message || 'Server error occurred');
      }
      return new Error(`Server error: ${error.response.status}`);
    } else if (error.request) {
      // Request made but no response
      return new Error('Unable to reach the server. Please check your connection.');
    } else {
      // Something else happened
      return new Error(error.message || 'An unexpected error occurred');
    }
  }

  /**
   * Query the knowledge system
   */
  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>('/query', request);
    return response.data;
  }

  /**
   * Ingest new documents
   */
  async ingest(request: IngestRequest): Promise<IngestResponse> {
    const response = await this.client.post<IngestResponse>('/ingest', request);
    return response.data;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * Readiness check
   */
  async readinessCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health/ready');
    return response.data;
  }

  /**
   * Get system info
   */
  async getSystemInfo(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health/info');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export individual methods for convenience
export const { query, ingest, healthCheck, readinessCheck, getSystemInfo } = apiClient;
