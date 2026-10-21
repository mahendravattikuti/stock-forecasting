import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';

/**
 * useConfig Hook
 * 
 * Manages application configuration state.
 * Loads config on mount and provides update functionality.
 * 
 * @param {Object} options - Hook options
 * @param {boolean} [options.autoLoad=true] - Load config on mount
 * @param {function} [options.onConfigChange] - Callback when config is updated: (oldConfig, newConfig) => void
 * 
 * @returns {Object} Hook state and actions
 * @returns {Object} hook.config - Current configuration object or null
 * @returns {boolean} hook.loading - Loading state
 * @returns {Error|null} hook.error - Error object or null
 * @returns {function} hook.loadConfig - Manually load configuration: () => Promise
 * @returns {function} hook.updateConfig - Update configuration: (updates) => Promise
 * @returns {function} hook.clearError - Clear error state
 */
export const useConfig = ({
  autoLoad = true,
  onConfigChange,
} = {}) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getConfiguration();
      setConfig(result);
      return result;
    } catch (err) {
      const errorObj = new Error(err.message || 'Failed to load configuration');
      setError(errorObj);
      throw errorObj;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = useCallback(
    async (updates) => {
      try {
        setLoading(true);
        setError(null);
        const oldConfig = config;
        const result = await api.updateConfiguration(updates);
        setConfig(result);
        onConfigChange?.(oldConfig, result);
        return result;
      } catch (err) {
        const errorObj = new Error(err.message || 'Failed to update configuration');
        setError(errorObj);
        throw errorObj;
      } finally {
        setLoading(false);
      }
    },
    [config, onConfigChange]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load config on mount if autoLoad is true
  useEffect(() => {
    if (autoLoad) {
      loadConfig();
    }
  }, [autoLoad, loadConfig]);

  return {
    config,
    loading,
    error,
    loadConfig,
    updateConfig,
    clearError,
  };
};

export default useConfig;
