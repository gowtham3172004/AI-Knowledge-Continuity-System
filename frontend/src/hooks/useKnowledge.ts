/**
 * useKnowledge Hook
 * 
 * Manages knowledge-specific features and metadata.
 */

import { useState, useEffect } from 'react';
import { healthCheck, getSystemInfo } from '../services/api';
import { HealthResponse } from '../types/api';

export const useKnowledge = () => {
  const [systemHealth, setSystemHealth] = useState<HealthResponse | null>(null);
  const [isHealthy, setIsHealthy] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  /**
   * Check system health
   */
  const checkHealth = async () => {
    try {
      const health = await healthCheck();
      setSystemHealth(health);
      setIsHealthy(health.status === 'healthy');
      setLastChecked(new Date());
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Health check failed:', error);
      }
      setIsHealthy(false);
      setLastChecked(new Date());
    }
  };

  /**
   * Get detailed system info
   */
  const getInfo = async () => {
    try {
      const info = await getSystemInfo();
      setSystemHealth(info);
      setLastChecked(new Date());
      return info;
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to get system info:', error);
      }
      throw error;
    }
  };

  // Check health on mount and every 30 seconds
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return {
    systemHealth,
    isHealthy,
    lastChecked,
    checkHealth,
    getInfo,
  };
};
