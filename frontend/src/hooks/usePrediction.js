import { useState, useCallback } from 'react';
import { api } from '../services/api';

/**
 * usePrediction Hook
 * 
 * Manages stock prediction requests and state.
 * Handles loading, error, and result states.
 * 
 * @returns {Object} Hook state and actions
 * @returns {Object} hook.data - Prediction result with signals, confidence, indicators
 * @returns {boolean} hook.loading - Loading state
 * @returns {Error|null} hook.error - Error object or null
 * @returns {function} hook.predict - Function to request prediction: (symbol, options?) => Promise
 * @returns {function} hook.clearError - Function to clear error state
 * @returns {function} hook.reset - Function to reset all state
 */
export const usePrediction = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const predict = useCallback(async (symbol, options = {}) => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.predictStock(symbol, options);
      setData(result);
      return result;
    } catch (err) {
      const errorObj = new Error(err.message || 'Failed to fetch prediction');
      setError(errorObj);
      throw errorObj;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    predict,
    clearError,
    reset,
  };
};

export default usePrediction;
