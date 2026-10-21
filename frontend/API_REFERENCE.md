# API Reference

**Version:** 1.0  
**Last Updated:** October 21, 2026  
**Base URL:** `http://localhost:5000/api`  

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Dashboard Endpoints](#dashboard-endpoints)
5. [Stock Prediction Endpoints](#stock-prediction-endpoints)
6. [Pipeline Endpoints](#pipeline-endpoints)
7. [Configuration Endpoints](#configuration-endpoints)
8. [Logging Endpoints](#logging-endpoints)
9. [Example Requests](#example-requests)

---

## Overview

The Stock Market Forecasting System backend exposes REST API endpoints for the frontend to:

- Fetch pipeline status and results
- Request stock predictions
- Control data pipeline execution
- Manage configuration settings
- Stream execution logs

All endpoints return JSON responses and use standard HTTP methods (GET, POST).

---

## Authentication

Currently **no authentication** is required. In production, add:

```javascript
// Add to all requests
headers: {
  'Authorization': `Bearer ${token}`
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "Error message",
  "status": 400,
  "timestamp": "2026-10-21T14:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check parameters |
| 404 | Not Found | Verify endpoint URL |
| 500 | Server Error | Retry or contact support |

### Frontend Error Handling

```javascript
// src/services/api.js
api.get('/endpoint')
  .then(res => {
    if (res.status === 200) {
      // Success
    }
  })
  .catch(err => {
    const status = err.response?.status;
    const message = err.response?.data?.error || 'Unknown error';
    
    if (status === 400) {
      // Bad request - validation error
    } else if (status === 500) {
      // Server error - retry
    }
  });
```

---

## Dashboard Endpoints

### GET /api/status

Get current pipeline status and phase information.

**Response:**
```json
{
  "phase": "running",
  "progress": 45,
  "current_step": "Feature engineering",
  "elapsed_time": 120,
  "estimated_total": 300,
  "symbols_processed": 50,
  "data_points": 10000,
  "features_created": 250,
  "models_trained": 3,
  "last_updated": "2026-10-21T14:30:00Z"
}
```

**Usage:**
```jsx
// src/hooks/usePipelineStatus.js
const { status, loading } = usePipelineStatus();
// Polls every 5 seconds by default
```

**Component:**
```jsx
// src/components/Dashboard.jsx
<MetricCard title="Status" value={status?.phase} />
<MetricCard title="Progress" value={`${status?.progress}%`} />
```

---

### GET /api/results

Get latest model results and predictions.

**Response:**
```json
{
  "timestamp": "2026-10-21T14:30:00Z",
  "best_model": {
    "name": "Ridge Regression",
    "mae": 2.45,
    "rmse": 3.12,
    "directional_accuracy": 0.68,
    "r_squared": 0.82
  },
  "all_models": [
    {
      "name": "Ridge Regression",
      "mae": 2.45,
      "rmse": 3.12
    },
    {
      "name": "ARIMA",
      "mae": 3.21,
      "rmse": 4.05
    }
  ],
  "predictions": [
    {
      "symbol": "AAPL",
      "actual_price": 150.25,
      "predicted_price": 151.42,
      "confidence": 0.87,
      "signal": "HOLD"
    }
  ]
}
```

**Usage:**
```jsx
// src/components/Dashboard.jsx
const { data: results, loading } = useFetch('/api/results');
```

---

## Stock Prediction Endpoints

### POST /api/predict

Request stock price prediction for a symbol.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "lookback_days": 60
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "current_price": 150.25,
  "predicted_price": 151.42,
  "confidence": 0.87,
  "trend": "UPWARD",
  "signal": "BUY",
  "technical_indicators": {
    "rsi": 65,
    "macd": 2.3,
    "bollinger_upper": 155.0,
    "bollinger_lower": 145.5
  },
  "timestamp": "2026-10-21T14:30:00Z"
}
```

**Usage:**
```jsx
// src/hooks/usePrediction.js
const { predictions, loading, predict } = usePrediction();
await predict('AAPL');
```

**Component:**
```jsx
// src/components/StockPredictor.jsx
<button onClick={() => predict(symbol)}>
  Predict
</button>
{predictions && (
  <div>
    <p>Signal: {predictions.signal}</p>
    <p>Confidence: {predictions.confidence}%</p>
  </div>
)}
```

---

### GET /api/history/{symbol}

Get prediction history for a symbol.

**Parameters:**
- `symbol` (string) - Stock ticker (e.g., "AAPL")
- `limit` (number, optional) - Max records (default: 50)

**Response:**
```json
{
  "symbol": "AAPL",
  "history": [
    {
      "timestamp": "2026-10-21T14:30:00Z",
      "predicted_price": 151.42,
      "actual_price": 151.25,
      "confidence": 0.87,
      "signal": "HOLD"
    }
  ]
}
```

**Usage:**
```jsx
// src/components/PredictionHistory.jsx
const { data: history } = useFetch(`/api/history/${symbol}`);
```

---

## Pipeline Endpoints

### POST /api/run-pipeline

Start data pipeline execution.

**Request Body:**
```json
{
  "data_source": "IEX",
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "lookback_days": 365,
  "train_test_split": 0.8
}
```

**Response:**
```json
{
  "status": "started",
  "pipeline_id": "pipe-12345",
  "message": "Pipeline started successfully"
}
```

**Usage:**
```jsx
// src/components/PipelineControl.jsx
const runPipeline = async () => {
  try {
    const response = await api.post('/api/run-pipeline', config);
    console.log('Pipeline started:', response.data);
  } catch (error) {
    console.error('Failed to start pipeline:', error);
  }
};
```

---

### POST /api/stop-pipeline

Stop currently running pipeline.

**Request Body:**
```json
{
  "force": false
}
```

**Response:**
```json
{
  "status": "stopped",
  "message": "Pipeline stopped gracefully"
}
```

**Usage:**
```jsx
const stopPipeline = async () => {
  try {
    const response = await api.post('/api/stop-pipeline');
    console.log('Pipeline stopped');
  } catch (error) {
    console.error('Failed to stop pipeline:', error);
  }
};
```

---

## Configuration Endpoints

### GET /api/config

Get current configuration.

**Response:**
```json
{
  "data_acquisition": {
    "source": "IEX",
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "lookback_days": 365,
    "batch_size": 100
  },
  "preprocessing": {
    "normalize": true,
    "handle_missing": "interpolate",
    "outlier_detection": "iqr"
  },
  "feature_engineering": {
    "technical_indicators": true,
    "sentiment_analysis": false,
    "feature_selection": "mutual_info"
  },
  "model_config": {
    "train_test_split": 0.8,
    "validation_split": 0.1,
    "random_seed": 42
  },
  "reproducibility": {
    "save_intermediate": true,
    "log_level": "INFO",
    "cache_enabled": true
  }
}
```

**Usage:**
```jsx
// src/hooks/useConfig.js
const { config, saveConfig } = useConfig();
```

---

### POST /api/config

Update configuration.

**Request Body:**
```json
{
  "data_acquisition": {
    "source": "Yahoo",
    "symbols": ["TSLA", "META"],
    "lookback_days": 180
  }
}
```

**Response:**
```json
{
  "status": "saved",
  "message": "Configuration updated successfully",
  "config": {
    // Updated config
  }
}
```

**Usage:**
```jsx
const saveConfig = async (newConfig) => {
  try {
    const response = await api.post('/api/config', newConfig);
    console.log('Config saved:', response.data);
  } catch (error) {
    console.error('Failed to save config:', error);
  }
};
```

---

## Logging Endpoints

### GET /api/logs

Get recent execution logs.

**Query Parameters:**
- `limit` (number, optional) - Max logs to return (default: 100)
- `level` (string, optional) - Filter by level (DEBUG, INFO, WARNING, ERROR)

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2026-10-21T14:30:00Z",
      "level": "INFO",
      "message": "Pipeline started",
      "component": "pipeline"
    },
    {
      "timestamp": "2026-10-21T14:31:00Z",
      "level": "DEBUG",
      "message": "Loading data for AAPL",
      "component": "data_acquisition"
    }
  ]
}
```

**Usage:**
```jsx
// src/components/LogViewer.jsx
const { data: logs } = useFetch('/api/logs?limit=50');
```

---

### GET /api/logs/stream (Server-Sent Events)

Stream logs in real-time using Server-Sent Events (SSE).

**Response Stream:**
```
data: {"timestamp":"2026-10-21T14:30:00Z","level":"INFO","message":"Pipeline started"}
data: {"timestamp":"2026-10-21T14:31:00Z","level":"DEBUG","message":"Loading data"}
```

**Usage:**
```jsx
// src/services/api.js
export function streamLogs(callback) {
  const eventSource = new EventSource(`${API_BASE_URL}/logs/stream`);
  
  eventSource.onmessage = (event) => {
    const log = JSON.parse(event.data);
    callback(log);
  };
  
  return eventSource;
}

// src/components/LogViewer.jsx
useEffect(() => {
  const eventSource = streamLogs((log) => {
    setLogs(prev => [log, ...prev]);
  });
  
  return () => eventSource.close();
}, []);
```

---

## Example Requests

### Example 1: Get Dashboard Status

```javascript
// Fetch and display pipeline status
fetch('http://localhost:5000/api/status')
  .then(res => res.json())
  .then(data => {
    console.log('Phase:', data.phase);
    console.log('Progress:', `${data.progress}%`);
    console.log('Current step:', data.current_step);
  })
  .catch(err => console.error('Error:', err));
```

### Example 2: Request Stock Prediction

```javascript
// Predict stock price
fetch('http://localhost:5000/api/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbol: 'AAPL',
    lookback_days: 60
  })
})
  .then(res => res.json())
  .then(data => {
    console.log('Prediction:', data.predicted_price);
    console.log('Signal:', data.signal);
    console.log('Confidence:', data.confidence);
  })
  .catch(err => console.error('Error:', err));
```

### Example 3: Start Pipeline

```javascript
// Start data pipeline with custom config
fetch('http://localhost:5000/api/run-pipeline', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    data_source: 'Yahoo',
    symbols: ['AAPL', 'GOOGL', 'MSFT'],
    lookback_days: 180,
    train_test_split: 0.8
  })
})
  .then(res => res.json())
  .then(data => {
    console.log('Pipeline started:', data.pipeline_id);
  })
  .catch(err => console.error('Error:', err));
```

### Example 4: Stream Logs Real-Time

```javascript
// Stream logs using EventSource
const eventSource = new EventSource('http://localhost:5000/api/logs/stream');

eventSource.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`[${log.level}] ${log.message}`);
};

eventSource.onerror = (error) => {
  console.error('Stream error:', error);
  eventSource.close();
};
```

### Example 5: Update Configuration

```javascript
// Save updated configuration
fetch('http://localhost:5000/api/config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    data_acquisition: {
      source: 'IEX',
      symbols: ['TSLA', 'META', 'AMZN'],
      lookback_days: 270
    },
    model_config: {
      train_test_split: 0.75,
      validation_split: 0.15
    }
  })
})
  .then(res => res.json())
  .then(data => {
    console.log('Config saved successfully');
  })
  .catch(err => console.error('Error:', err));
```

---

## Best Practices

### 1. Error Handling

Always handle potential errors:

```javascript
try {
  const response = await api.get('/endpoint');
  // Process response
} catch (error) {
  if (error.response?.status === 404) {
    // Handle not found
  } else if (error.response?.status === 500) {
    // Handle server error - retry
  } else {
    // Handle network error
  }
}
```

### 2. Loading States

Show loading indicator during API calls:

```jsx
const { data, loading, error } = useFetch('/api/endpoint');

if (loading) return <LoadingSpinner />;
if (error) return <ErrorAlert message={error} />;

return <div>{/* Render data */}</div>;
```

### 3. Polling for Status

Use `usePipelineStatus` hook for polling:

```jsx
const { status, loading } = usePipelineStatus(3000); // Poll every 3s
```

### 4. Form Submissions

Validate before sending:

```jsx
const handleSubmit = async (formData) => {
  if (!formData.symbol) {
    setError('Symbol is required');
    return;
  }
  
  try {
    const response = await api.post('/api/predict', formData);
    setResult(response.data);
  } catch (err) {
    setError(err.message);
  }
};
```

---

## Troubleshooting

### API Not Responding

1. Check backend is running: `python api_server.py`
2. Verify base URL: `http://localhost:5000/api`
3. Check firewall/network settings

### CORS Errors

Backend should allow frontend origin. Add to Flask:

```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])
```

### Timeout Errors

Increase timeout in axios config:

```javascript
// src/services/api.js
const instance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
});
```

---

## Migration Guide

### From Mock to Real API

1. **Replace mock data** in components with API calls
2. **Use custom hooks** for data fetching (useFetch, usePrediction, etc.)
3. **Handle loading/error** states
4. **Test with real backend**

### Example Migration

**Before (Mock):**
```jsx
const mockData = {
  phase: 'running',
  progress: 45
};
return <MetricCard value={mockData.progress} />;
```

**After (Real API):**
```jsx
const { status, loading } = usePipelineStatus();
if (loading) return <LoadingSpinner />;
return <MetricCard value={status.progress} />;
```

---

## Summary

The API provides complete endpoints for:

- **Dashboard** - Status and results
- **Predictions** - Stock price forecasting
- **Pipeline** - Data processing control
- **Configuration** - Settings management
- **Logging** - Real-time log streaming

Use the provided custom hooks (useFetch, usePrediction, etc.) for simplified data access in React components.

---

**Next Steps:** See DEPLOYMENT.md for production deployment.
