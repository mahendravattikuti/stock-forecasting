import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

/**
 * usePipelineStatus Hook
 * 
 * Fetches and monitors pipeline execution status.
 * Can automatically poll for status updates at regular intervals.
 * 
 * @param {Object} options - Hook options
 * @param {boolean} [options.autoRefresh=false] - Auto-poll for status updates
 * @param {number} [options.refreshInterval=5000] - Poll interval in ms (default 5s)
 * @param {function} [options.onStatusChange] - Callback when status changes: (oldStatus, newStatus) => void
 * 
 * @returns {Object} Hook state and actions
 * @returns {Object} hook.status - Pipeline status object or null
 * @returns {boolean} hook.loading - Loading state
 * @returns {Error|null} hook.error - Error object or null
 * @returns {function} hook.refresh - Manually fetch status: () => Promise
 * @returns {function} hook.startPolling - Start auto-refresh polling
 * @returns {function} hook.stopPolling - Stop auto-refresh polling
 */
export const usePipelineStatus = ({
  autoRefresh = false,
  refreshInterval = 5000,
  onStatusChange,
} = {}) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(autoRefresh);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getPipelineStatus();
      
      // Trigger callback if status changed
      if (status && status.state !== result.state) {
        onStatusChange?.(status.state, result.state);
      }
      
      setStatus(result);
      return result;
    } catch (err) {
      const errorObj = new Error(err.message || 'Failed to fetch pipeline status');
      setError(errorObj);
      throw errorObj;
    } finally {
      setLoading(false);
    }
  }, [status, onStatusChange]);

  const startPolling = useCallback(() => {
    setIsPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  // Setup polling interval
  useEffect(() => {
    if (!isPolling) return;

    // Fetch immediately
    fetchStatus();

    // Setup interval
    const intervalId = setInterval(fetchStatus, refreshInterval);

    return () => clearInterval(intervalId);
  }, [isPolling, refreshInterval, fetchStatus]);

  return {
    status,
    loading,
    error,
    refresh: fetchStatus,
    startPolling,
    stopPolling,
  };
};

export default usePipelineStatus;
