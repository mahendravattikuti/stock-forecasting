/**
 * Centralized API Service
 * Handles all backend communication with proper error handling and logging
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
const REQUEST_TIMEOUT = 30000; // 30 seconds

// ==================== CONFIGURATION ====================

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
};

// ==================== ERROR HANDLING ====================

export class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

const handleResponse = async (response) => {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new APIError(
      data?.error || `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      data
    );
  }

  return data;
};

// ==================== GENERIC FETCH WRAPPER ====================

export const fetchWithTimeout = async (url, options = {}) => {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    options.timeout || REQUEST_TIMEOUT
  );

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeout);
    return await handleResponse(response);
  } catch (error) {
    clearTimeout(timeout);
    if (error.name === 'AbortError') {
      throw new APIError('Request timeout', 408);
    }
    throw error;
  }
};

// ==================== API METHODS ====================

/**
 * Predict buy/sell/hold signal for a stock
 * @param {string} symbol - Stock symbol (e.g., 'AAPL')
 * @returns {Promise<Object>} Prediction result with signal, confidence, etc.
 */
export const predictStock = async (symbol) => {
  if (!symbol) throw new Error('Symbol is required');

  return fetchWithTimeout(`${API_BASE_URL}/predict`, {
    method: 'POST',
    headers: API_CONFIG.headers,
    body: JSON.stringify({ symbol: symbol.toUpperCase() }),
  });
};

/**
 * Get current pipeline status
 * @returns {Promise<Object>} Pipeline status and timestamp
 */
export const getPipelineStatus = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/status`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Get pipeline results/output
 * @returns {Promise<Object>} Pipeline execution results
 */
export const getPipelineResults = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/results`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Get execution logs
 * @param {number} limit - Maximum number of logs to return
 * @returns {Promise<Object>} Logs array and total count
 */
export const getExecutionLogs = async (limit = 100) => {
  return fetchWithTimeout(`${API_BASE_URL}/logs?limit=${limit}`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Get current configuration
 * @returns {Promise<Object>} Current pipeline configuration
 */
export const getConfiguration = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/config`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Update configuration
 * @param {Object} config - Configuration object to save
 * @returns {Promise<Object>} Response with success status
 */
export const updateConfiguration = async (config) => {
  if (!config || typeof config !== 'object') {
    throw new Error('Configuration must be an object');
  }

  return fetchWithTimeout(`${API_BASE_URL}/config`, {
    method: 'POST',
    headers: API_CONFIG.headers,
    body: JSON.stringify(config),
  });
};

/**
 * Start pipeline execution
 * @param {Object} config - Optional configuration for this run
 * @returns {Promise<Object>} Response with success status and message
 */
export const startPipeline = async (config = null) => {
  return fetchWithTimeout(`${API_BASE_URL}/run-pipeline`, {
    method: 'POST',
    headers: API_CONFIG.headers,
    body: JSON.stringify({ config } || {}),
  });
};

/**
 * Stop running pipeline
 * @returns {Promise<Object>} Response with success status and message
 */
export const stopPipeline = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/stop-pipeline`, {
    method: 'POST',
    headers: API_CONFIG.headers,
    body: JSON.stringify({}),
  });
};

/**
 * Get health check status
 * @returns {Promise<Object>} Server health status
 */
export const getHealthStatus = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/health`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Get historical data for a stock
 * @param {string} symbol - Stock symbol
 * @param {string} startDate - Start date (YYYY-MM-DD)
 * @param {string} endDate - End date (YYYY-MM-DD)
 * @returns {Promise<Object>} Historical OHLCV data
 */
export const getHistoricalData = async (symbol, startDate, endDate) => {
  if (!symbol) throw new Error('Symbol is required');

  const params = new URLSearchParams();
  if (startDate) params.append('start', startDate);
  if (endDate) params.append('end', endDate);

  const queryString = params.toString();
  const url = `${API_BASE_URL}/data/${symbol}${queryString ? '?' + queryString : ''}`;

  return fetchWithTimeout(url, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Get stock quotes for multiple symbols
 * @param {string[]} symbols - Array of stock symbols
 * @returns {Promise<Object>} Quote data for each symbol
 */
export const getQuotes = async (symbols) => {
  if (!Array.isArray(symbols) || symbols.length === 0) {
    throw new Error('Symbols array is required');
  }

  return fetchWithTimeout(`${API_BASE_URL}/quotes`, {
    method: 'POST',
    headers: API_CONFIG.headers,
    body: JSON.stringify({ symbols }),
  });
};

/**
 * Get model evaluation metrics
 * @returns {Promise<Object>} Model performance metrics
 */
export const getEvaluationMetrics = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/evaluation`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Get feature importance scores
 * @returns {Promise<Object>} Feature names and importance scores
 */
export const getFeatureImportance = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/features/importance`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

/**
 * Get pipeline information (phases, data range, etc.)
 * @returns {Promise<Object>} Pipeline metadata
 */
export const getPipelineInfo = async () => {
  return fetchWithTimeout(`${API_BASE_URL}/pipeline/info`, {
    method: 'GET',
    headers: API_CONFIG.headers,
  });
};

// ==================== BATCH OPERATIONS ====================

/**
 * Predict for multiple symbols
 * @param {string[]} symbols - Array of stock symbols
 * @returns {Promise<Object>} Predictions for each symbol
 */
export const batchPredict = async (symbols) => {
  const predictions = {};
  const errors = {};

  for (const symbol of symbols) {
    try {
      predictions[symbol] = await predictStock(symbol);
    } catch (error) {
      errors[symbol] = error.message;
    }
  }

  return { predictions, errors };
};

// ==================== EXPORT DEFAULT ====================

export default {
  predictStock,
  getPipelineStatus,
  getPipelineResults,
  getExecutionLogs,
  getConfiguration,
  updateConfiguration,
  startPipeline,
  stopPipeline,
  getHealthStatus,
  getHistoricalData,
  getQuotes,
  getEvaluationMetrics,
  getFeatureImportance,
  getPipelineInfo,
  batchPredict,
};
