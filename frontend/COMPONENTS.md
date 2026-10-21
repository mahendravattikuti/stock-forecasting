# Component Documentation

**Version:** 1.0  
**Last Updated:** October 21, 2026  
**Status:** Complete  

---

## Table of Contents

1. [Overview](#overview)
2. [UI Components](#ui-components)
3. [Container Components](#container-components)
4. [Layout Components](#layout-components)
5. [Hooks](#hooks)
6. [Services](#services)
7. [Component Patterns](#component-patterns)
8. [Usage Examples](#usage-examples)

---

## Overview

This document describes all reusable components in the Stock Market Forecasting frontend.

### Component Hierarchy

```
├── Layout Components
│   ├── AppLayout
│   ├── Navigation
│   └── ThemeContext
│
├── Container Components
│   ├── Dashboard
│   ├── StockPredictor
│   ├── StockSearch
│   ├── PipelineControl
│   ├── Configuration
│   ├── LogViewer
│   ├── TechnicalIndicators
│   ├── FinancialChart
│   ├── PredictionHistory
│   └── DataAcquisition (deprecated)
│
├── UI Components (src/components/ui/)
│   ├── Card
│   ├── MetricCard
│   ├── StatusBadge
│   ├── LoadingSpinner
│   ├── ErrorAlert
│   ├── EmptyState
│   └── ConfirmModal
│
├── Hooks (src/hooks/)
│   ├── useFetch
│   ├── usePrediction
│   ├── usePipelineStatus
│   └── useConfig
│
└── Services (src/services/)
    └── api
```

---

## UI Components

### Card

Reusable container component with optional title and collapsible support.

**Location:** `src/components/ui/Card.jsx`

**Props:**
```typescript
interface CardProps {
  title?: string;           // Card title
  children: ReactNode;      // Card content
  className?: string;       // Additional CSS classes
  collapsible?: boolean;    // Enable collapse/expand
  defaultExpanded?: boolean; // Initial state
}
```

**Example:**
```jsx
import { Card } from './ui';

export function MyComponent() {
  return (
    <Card title="Stock Information" collapsible>
      <p>Stock price and details go here</p>
    </Card>
  );
}
```

**Features:**
- ✅ Accessible collapse with aria-expanded
- ✅ Smooth animation on expand/collapse
- ✅ Keyboard navigable
- ✅ Mobile responsive padding

---

### MetricCard

Display key performance indicators (KPIs) with icon and value.

**Location:** `src/components/ui/MetricCard.jsx`

**Props:**
```typescript
interface MetricCardProps {
  title: string;            // Metric name
  value: string | number;   // Metric value
  icon?: ReactNode;         // Icon component
  onClick?: () => void;     // Click handler
  className?: string;       // Additional CSS classes
  trend?: 'up' | 'down';   // Trend indicator
  trendValue?: string;      // Trend percentage
}
```

**Example:**
```jsx
import { MetricCard } from './ui';
import { TrendingUp } from 'lucide-react';

export function Dashboard() {
  return (
    <MetricCard
      title="Symbols Processed"
      value={150}
      icon={<TrendingUp size={24} />}
      trend="up"
      trendValue="+25%"
      onClick={() => console.log('clicked')}
    />
  );
}
```

**Features:**
- ✅ Keyboard accessible (Space/Enter to click)
- ✅ Trend indicators (up/down)
- ✅ Hover and focus states
- ✅ Custom icon support

---

### StatusBadge

Display status indicators with appropriate colors.

**Location:** `src/components/ui/StatusBadge.jsx`

**Props:**
```typescript
interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'pending' | 'info';
  label: string;
  loading?: boolean;       // Show loading animation
  className?: string;
}
```

**Example:**
```jsx
import { StatusBadge } from './ui';

export function PipelineStatus({ status }) {
  return (
    <div>
      <StatusBadge
        status={status.phase === 'running' ? 'pending' : 'success'}
        label={status.phase}
        loading={status.phase === 'running'}
      />
    </div>
  );
}
```

**Status Colors:**
- ✅ `success` - Green (#22c55e)
- ⚠️ `warning` - Orange (#f97316)
- ❌ `error` - Red (#ef4444)
- ⏳ `pending` - Blue (#0066cc)
- ℹ️ `info` - Cyan (#06b6d4)

---

### LoadingSpinner

Show loading animation with optional text.

**Location:** `src/components/ui/LoadingSpinner.jsx`

**Props:**
```typescript
interface LoadingSpinnerProps {
  text?: string;        // Loading message
  size?: 'sm' | 'md' | 'lg'; // Spinner size
  fullScreen?: boolean; // Take up full viewport
}
```

**Example:**
```jsx
import { LoadingSpinner } from './ui';

export function Dashboard() {
  const { data, loading } = usePipelineStatus();

  if (loading) {
    return <LoadingSpinner text="Loading pipeline status..." />;
  }

  return <div>{/* Content */}</div>;
}
```

**Sizes:**
- `sm` - Small (24px)
- `md` - Medium (48px) - default
- `lg` - Large (64px)

---

### ErrorAlert

Display error messages with optional retry action.

**Location:** `src/components/ui/ErrorAlert.jsx`

**Props:**
```typescript
interface ErrorAlertProps {
  message: string;           // Error message
  onRetry?: () => void;      // Retry callback
  onDismiss?: () => void;    // Dismiss callback
  dismissible?: boolean;     // Show dismiss button
}
```

**Example:**
```jsx
import { ErrorAlert } from './ui';

export function Dashboard() {
  const { error, refetch } = useFetch('/api/status');

  if (error) {
    return (
      <ErrorAlert
        message={error}
        onRetry={refetch}
        dismissible
      />
    );
  }

  return <div>{/* Content */}</div>;
}
```

**Features:**
- ✅ Dismissible
- ✅ Retry action
- ✅ Accessible alert role
- ✅ Close button keyboard accessible

---

### EmptyState

Display when no data is available.

**Location:** `src/components/ui/EmptyState.jsx`

**Props:**
```typescript
interface EmptyStateProps {
  title: string;              // Empty state title
  description?: string;       // Explanation
  icon?: ReactNode;          // Icon component
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

**Example:**
```jsx
import { EmptyState } from './ui';
import { Search } from 'lucide-react';

export function StockSearch() {
  const { results } = useSearch();

  if (results.length === 0) {
    return (
      <EmptyState
        title="No Results Found"
        description="Try searching for a different stock symbol"
        icon={<Search size={48} />}
        action={{
          label: 'Clear Search',
          onClick: () => setSearch('')
        }}
      />
    );
  }

  return <ul>{/* Results */}</ul>;
}
```

---

### ConfirmModal

Modal dialog for confirmation actions.

**Location:** `src/components/ui/ConfirmModal.jsx`

**Props:**
```typescript
interface ConfirmModalProps {
  isOpen: boolean;           // Show/hide modal
  title: string;            // Modal title
  message: string;          // Confirmation message
  onConfirm: () => void;    // Confirm callback
  onCancel: () => void;     // Cancel callback
  confirmText?: string;     // Confirm button label (default: "Confirm")
  cancelText?: string;      // Cancel button label (default: "Cancel")
}
```

**Example:**
```jsx
import { ConfirmModal } from './ui';
import { useState } from 'react';

export function PipelineControl() {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleStopPipeline = async () => {
    try {
      await api.post('/api/stop-pipeline');
      setShowConfirm(false);
    } catch (error) {
      console.error('Failed to stop:', error);
    }
  };

  return (
    <>
      <button onClick={() => setShowConfirm(true)}>
        Stop Pipeline
      </button>

      <ConfirmModal
        isOpen={showConfirm}
        title="Stop Pipeline?"
        message="This will stop the current data processing. Are you sure?"
        onConfirm={handleStopPipeline}
        onCancel={() => setShowConfirm(false)}
      />
    </>
  );
}
```

**Features:**
- ✅ Focus trap (Tab cycles within modal)
- ✅ Focus restoration on close
- ✅ Escape key to cancel
- ✅ ARIA modal dialog semantics
- ✅ Keyboard accessible buttons

---

## Container Components

### Dashboard

Main dashboard displaying pipeline status and metrics.

**Location:** `src/components/Dashboard.jsx`

**Features:**
- Real-time pipeline status from `/api/status`
- Latest results from `/api/results`
- Key metrics display
- Performance comparison charts

**Example:**
```jsx
import { Dashboard } from './components';

export function App() {
  return <Dashboard />;
}
```

### StockPredictor

Stock price prediction interface with technical indicators.

**Location:** `src/components/StockPredictor.jsx`

**Features:**
- Stock symbol search (autocomplete)
- Prediction request
- Technical indicators display (RSI, MACD, Bollinger Bands)
- Prediction history
- Buy/Sell/Hold signals

**Example:**
```jsx
import { StockPredictor } from './components';

export function App() {
  return <StockPredictor />;
}
```

### StockSearch

Autocomplete search for stock symbols.

**Location:** `src/components/StockSearch.jsx`

**Features:**
- Real-time search with ARIA listbox pattern
- Keyboard navigation (arrow keys)
- Keyboard-accessible selection
- Search live region announcements
- Debounced API calls

**Example:**
```jsx
import { StockSearch } from './components';
import { useState } from 'react';

export function MyComponent() {
  const [selectedSymbol, setSelectedSymbol] = useState('');

  return (
    <StockSearch
      onSelect={(symbol) => setSelectedSymbol(symbol)}
    />
  );
}
```

### PipelineControl

Control data pipeline execution.

**Location:** `src/components/PipelineControl.jsx`

**Features:**
- Start/stop pipeline buttons
- Real-time log viewer
- Log search and export
- Progress indicator
- Confirmation dialogs

**Example:**
```jsx
import { PipelineControl } from './components';

export function App() {
  return <PipelineControl />;
}
```

### Configuration

Manage pipeline configuration settings.

**Location:** `src/components/Configuration.jsx`

**Features:**
- Data source selection
- Symbol list management
- Lookback period configuration
- Train/test split settings
- Save/reset functionality

**Example:**
```jsx
import { Configuration } from './components';

export function App() {
  return <Configuration />;
}
```

### LogViewer

Real-time log streaming and display.

**Location:** `src/components/LogViewer.jsx`

**Features:**
- Real-time log streaming via Server-Sent Events
- Log filtering by level
- Search within logs
- Export to CSV
- Auto-scroll to latest

**Example:**
```jsx
import { LogViewer } from './components';

export function App() {
  return <LogViewer />;
}
```

### TechnicalIndicators

Display technical analysis indicators.

**Location:** `src/components/TechnicalIndicators.jsx`

**Indicators:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- ATR (Average True Range)
- Stochastic Oscillator
- Volume Profile

**Example:**
```jsx
import { TechnicalIndicators } from './components';

export function StockAnalysis() {
  return (
    <TechnicalIndicators symbol="AAPL" period={14} />
  );
}
```

### FinancialChart

Interactive price and prediction charts.

**Location:** `src/components/FinancialChart.jsx`

**Features:**
- Recharts LineChart with multiple series
- Actual vs predicted prices
- Responsive sizing
- Tooltip with details
- Legend for multiple lines

**Example:**
```jsx
import { FinancialChart } from './components';

export function Dashboard() {
  const data = [
    { date: '2026-01-01', actual: 150.25, predicted: 149.80 },
    { date: '2026-01-02', actual: 151.50, predicted: 151.75 }
  ];

  return (
    <FinancialChart
      data={data}
      title="Price Comparison"
    />
  );
}
```

### PredictionHistory

Display prediction history for a symbol.

**Location:** `src/components/PredictionHistory.jsx`

**Features:**
- Stores history in localStorage
- Shows past predictions
- Accuracy tracking
- Clear history option
- Export functionality

**Example:**
```jsx
import { PredictionHistory } from './components';

export function StockAnalysis() {
  return (
    <PredictionHistory symbol="AAPL" />
  );
}
```

---

## Layout Components

### AppLayout

Main app layout wrapper with navigation and structure.

**Location:** `src/layout/AppLayout.jsx`

**Features:**
- Header with navigation
- Main content area
- Sidebar/complementary area
- Skip-to-content link
- Landmark roles (header, main, aside)

**Example:**
```jsx
import { AppLayout } from './layout';

export function App() {
  return (
    <AppLayout>
      <Dashboard />
    </AppLayout>
  );
}
```

### Navigation

Top navigation bar with tab-based routing.

**Location:** `src/components/Navigation.jsx`

**Features:**
- Horizontal tab navigation
- Mobile hamburger menu (md breakpoint and below)
- Keyboard navigation (arrow keys)
- Active tab indicator
- ARIA tablist pattern

**Example:**
```jsx
import { Navigation } from './components';

export function App() {
  return (
    <>
      <Navigation />
      {/* Page content */}
    </>
  );
}
```

### ThemeContext

Global theme provider for consistency.

**Location:** `src/context/ThemeContext.jsx`

**Example:**
```jsx
import { ThemeProvider } from './context/ThemeContext';
import App from './App';

export function Root() {
  return (
    <ThemeProvider>
      <App />
    </ThemeProvider>
  );
}
```

---

## Hooks

### useFetch

Generic data fetching hook with caching.

**Location:** `src/hooks/useFetch.js`

**Usage:**
```jsx
import { useFetch } from './hooks';

export function Dashboard() {
  const { data, loading, error, refetch } = useFetch('/api/results');

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;

  return <div>{/* Use data */}</div>;
}
```

**Returns:**
```typescript
{
  data: any;              // Fetched data
  loading: boolean;       // Loading state
  error: string | null;   // Error message if any
  refetch: () => void;    // Retry fetch
}
```

### usePrediction

Stock prediction hook.

**Location:** `src/hooks/usePrediction.js`

**Usage:**
```jsx
import { usePrediction } from './hooks';

export function StockPredictor() {
  const { predictions, loading, error, predict } = usePrediction();

  const handlePredictClick = async () => {
    await predict('AAPL');
  };

  return (
    <button onClick={handlePredictClick} disabled={loading}>
      {loading ? 'Predicting...' : 'Predict'}
    </button>
  );
}
```

**Returns:**
```typescript
{
  predictions: any;          // Prediction results
  loading: boolean;          // Loading state
  error: string | null;      // Error message
  predict: (symbol) => void; // Make prediction
}
```

### usePipelineStatus

Real-time pipeline status hook with polling.

**Location:** `src/hooks/usePipelineStatus.js`

**Usage:**
```jsx
import { usePipelineStatus } from './hooks';

export function Dashboard() {
  const { status, loading } = usePipelineStatus(5000); // Poll every 5s

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <p>Phase: {status.phase}</p>
      <p>Progress: {status.progress}%</p>
    </div>
  );
}
```

**Parameters:**
```typescript
usePipelineStatus(
  interval?: number   // Poll interval in ms (default: 5000)
)
```

**Returns:**
```typescript
{
  status: any;        // Pipeline status
  loading: boolean;   // Loading state
}
```

### useConfig

Configuration management hook.

**Location:** `src/hooks/useConfig.js`

**Usage:**
```jsx
import { useConfig } from './hooks';

export function Configuration() {
  const { config, saveConfig } = useConfig();

  const handleSave = async (newConfig) => {
    await saveConfig(newConfig);
  };

  return (
    <form onSubmit={() => handleSave(config)}>
      {/* Form fields */}
    </form>
  );
}
```

**Returns:**
```typescript
{
  config: any;                        // Current config
  saveConfig: (config) => Promise;    // Save config
}
```

---

## Services

### API Service

Centralized HTTP communication.

**Location:** `src/services/api.js`

**Methods:**
```javascript
// Dashboard
api.getStatus()       // Get pipeline status
api.getResults()      // Get latest results

// Predictions
api.predictStock(symbol)           // Predict for symbol
api.getPredictionHistory(symbol)   // Get history

// Pipeline
api.runPipeline(config)  // Start pipeline
api.stopPipeline()       // Stop pipeline

// Logs
api.getLogs(limit)       // Get logs
api.streamLogs(callback) // Stream logs (SSE)

// Configuration
api.getConfig()          // Get config
api.saveConfig(config)   // Save config
```

**Example:**
```jsx
import { api } from './services/api';

// Make API calls
try {
  const results = await api.getResults();
  console.log(results);
} catch (error) {
  console.error('API error:', error);
}
```

---

## Component Patterns

### Container + Presentational

Separate data logic from UI rendering.

```jsx
// Container (src/components/Dashboard.jsx)
export function Dashboard() {
  const { status, loading } = usePipelineStatus();

  return <DashboardView status={status} loading={loading} />;
}

// Presentational (src/components/DashboardView.jsx)
export function DashboardView({ status, loading }) {
  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <MetricCard title="Status" value={status.phase} />
    </div>
  );
}
```

### Error Boundaries

Wrap components with error handling.

```jsx
export function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}

class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return <ErrorAlert message={this.state.error.message} />;
    }

    return this.props.children;
  }
}
```

### Loading States

Show appropriate UI during data fetch.

```jsx
export function Dashboard() {
  const { data, loading, error } = useFetch('/api/results');

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;
  if (error) return <ErrorAlert message={error} />;
  if (!data) return <EmptyState title="No data available" />;

  return <DashboardContent data={data} />;
}
```

---

## Usage Examples

### Complete Page Example

```jsx
// src/pages/DashboardPage.jsx
import { Dashboard } from '../components';
import { AppLayout } from '../layout';

export function DashboardPage() {
  return (
    <AppLayout>
      <Dashboard />
    </AppLayout>
  );
}
```

### With Multiple Sections

```jsx
// src/pages/AnalysisPage.jsx
import {
  StockPredictor,
  TechnicalIndicators,
  PredictionHistory,
  FinancialChart
} from '../components';
import { Card } from '../components/ui';

export function AnalysisPage() {
  const [symbol, setSymbol] = useState('AAPL');

  return (
    <div className="space-y-6">
      <Card title="Prediction">
        <StockPredictor onSymbolChange={setSymbol} />
      </Card>

      <Card title="Technical Analysis">
        <TechnicalIndicators symbol={symbol} />
      </Card>

      <Card title="History" collapsible>
        <PredictionHistory symbol={symbol} />
      </Card>

      <Card title="Price Chart">
        <FinancialChart symbol={symbol} />
      </Card>
    </div>
  );
}
```

---

## Summary

Component architecture provides:

- **Reusable UI Components** - Card, MetricCard, StatusBadge, etc.
- **Container Components** - Dashboard, StockPredictor, etc.
- **Custom Hooks** - useFetch, usePrediction, etc.
- **Centralized API Service** - Single point for HTTP calls
- **Layout Components** - AppLayout, Navigation
- **Consistent Patterns** - Container + Presentational, Error handling

Use components to build features quickly while maintaining code quality and consistency.

---

**Next Steps:** See README.md for quick start guide.
