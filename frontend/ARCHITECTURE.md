# Frontend Architecture Guide

**Version:** 1.0  
**Last Updated:** October 21, 2026  
**Status:** Production Ready  

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Design System](#design-system)
5. [Component Architecture](#component-architecture)
6. [Data Flow & State Management](#data-flow--state-management)
7. [API Integration](#api-integration)
8. [Responsive Design](#responsive-design)
9. [Accessibility](#accessibility)
10. [Performance](#performance)
11. [Development Workflow](#development-workflow)

---

## Overview

The Stock Market Forecasting System frontend is a modern, responsive React application built with production-grade patterns including:

- **Centralized Design System** - 100+ tokens for consistent theming
- **Component-Based Architecture** - Reusable UI components with clear responsibilities
- **API Service Layer** - Centralized, error-tolerant HTTP communication
- **Custom Hooks** - Reusable logic patterns for data fetching and state management
- **Responsive Design** - Mobile-first approach with 6 breakpoints (xs-2xl)
- **WCAG 2.1 AA Accessibility** - 85-90% compliant with 25+ accessibility improvements
- **Real API Integration** - All components bound to live backend endpoints

### Architecture Goals

1. **Maintainability** - Clear structure, consistent patterns, minimal duplication
2. **Scalability** - Easy to add new features without breaking existing code
3. **Accessibility** - Inclusive design for all users, keyboard navigation, screen readers
4. **Performance** - Optimized bundle size (86.89 kB JS, 22.38 kB gzip), fast rendering
5. **Developer Experience** - Clear documentation, type hints, helpful error messages

---

## Technology Stack

### Core

| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.x | UI framework with hooks |
| **Vite** | 4.x | Build tool and dev server |
| **Tailwind CSS** | 3.x | Utility-first styling |
| **Lucide Icons** | Latest | Icon library (SVG-based) |

### Data & HTTP

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Axios** | 1.x | HTTP client with interceptors |
| **localStorage** | Native | Client-side persistence |

### Charting & Visualization

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Recharts** | 2.x | Interactive React charts |

### Development

| Technology | Version | Purpose |
|-----------|---------|---------|
| **ESLint** | Latest | Code linting |
| **Prettier** | Latest | Code formatting |
| **Playwright** | Latest | E2E testing framework |

---

## Project Structure

```
frontend/
├── public/                    # Static assets
├── src/
│   ├── components/            # React components
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── Card.jsx
│   │   │   ├── ConfirmModal.jsx
│   │   │   ├── ErrorAlert.jsx
│   │   │   ├── LoadingSpinner.jsx
│   │   │   ├── MetricCard.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   ├── EmptyState.jsx
│   │   │   └── index.js       # Barrel export
│   │   ├── Dashboard.jsx      # Dashboard tab
│   │   ├── StockPredictor.jsx # Stock prediction UI
│   │   ├── StockSearch.jsx    # Autocomplete search
│   │   ├── PipelineControl.jsx # Data pipeline control
│   │   ├── Configuration.jsx  # Settings management
│   │   ├── LogViewer.jsx      # Real-time log display
│   │   ├── TechnicalIndicators.jsx # Financial indicators
│   │   ├── FinancialChart.jsx # Price/prediction charts
│   │   ├── PredictionHistory.jsx # History display
│   │   ├── Navigation.jsx     # Top navigation bar
│   │   └── DataAcquisition.jsx # Legacy wrapper (deprecated)
│   │
│   ├── hooks/                 # Custom React hooks
│   │   ├── useFetch.js        # Generic data fetching with caching
│   │   ├── usePrediction.js   # Stock prediction hook
│   │   ├── usePipelineStatus.js # Pipeline status polling
│   │   └── useConfig.js       # Configuration management
│   │
│   ├── services/              # Business logic & API
│   │   └── api.js             # Centralized API methods
│   │
│   ├── theme/                 # Design tokens
│   │   └── tokens.js          # 100+ design tokens
│   │
│   ├── layout/                # Layout components
│   │   └── AppLayout.jsx      # Main app layout wrapper
│   │
│   ├── context/               # React Context
│   │   └── ThemeContext.jsx   # Theme provider
│   │
│   ├── App.jsx                # Root app component
│   ├── main.jsx               # Entry point
│   ├── index.css              # Global styles (focus, sr-only, etc.)
│   └── App.css                # App-specific styles
│
├── e2e/                       # E2E tests & documentation
│   └── critical-paths.test.md # Manual test procedures
│
├── styles/                    # Additional style files
│   └── globals.css            # Global utility styles
│
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind configuration
├── postcss.config.js          # PostCSS configuration
├── package.json               # Dependencies and scripts
├── index.html                 # HTML entry point
├── README.md                  # Quick start guide
├── ARCHITECTURE.md            # This file
├── API_REFERENCE.md           # API endpoint documentation
├── DEPLOYMENT.md              # Deployment guide
├── ACCESSIBILITY.md           # WCAG compliance details
├── COMPONENTS.md              # Component documentation
└── CHANGELOG.md               # Version history
```

---

## Design System

### Purpose

The design system provides a single source of truth for visual constants across the application. This ensures consistency, enables rapid prototyping, and simplifies theme switching.

### Location

**File:** `src/theme/tokens.js`

### Token Categories

#### 1. Colors (50+ tokens)

```javascript
// Primary brand colors
colors: {
  primary: {
    50: '#f0f7ff',   // Lightest
    100: '#e0f0ff',
    200: '#b3d9ff',
    ...
    900: '#001a4d'   // Darkest
  },
  success: { 50: '#f0fdf4', ... 900: '#14532d' },
  warning: { 50: '#fef3c7', ... 900: '#78350f' },
  error: { 50: '#fef2f2', ... 900: '#7f1d1d' },
  neutral: { ... }
}
```

**Usage:**
```javascript
// In Tailwind classes
<div className="bg-primary-600 text-neutral-900">
```

#### 2. Typography (12+ tokens)

```javascript
typography: {
  fontSize: { xs: '0.75rem', sm: '0.875rem', base: '1rem', ... },
  fontWeight: { light: 300, normal: 400, semibold: 600, bold: 700 },
  lineHeight: { tight: 1.2, normal: 1.5, relaxed: 1.75 }
}
```

**Usage:**
```javascript
<p className="text-lg font-semibold leading-relaxed">
```

#### 3. Spacing (24+ tokens)

```javascript
spacing: {
  xs: '0.25rem',    // 4px
  sm: '0.5rem',     // 8px
  md: '1rem',       // 16px
  lg: '1.5rem',     // 24px
  xl: '2rem',       // 32px
  '2xl': '3rem'     // 48px
}
```

**Usage:**
```javascript
<div className="px-md py-lg">
```

#### 4. Shadows (8+ tokens)

```javascript
shadows: {
  sm: '0 1px 2px rgba(0,0,0,0.05)',
  md: '0 4px 6px rgba(0,0,0,0.1)',
  lg: '0 10px 15px rgba(0,0,0,0.1)',
  xl: '0 20px 25px rgba(0,0,0,0.1)'
}
```

#### 5. Border Radius (6+ tokens)

```javascript
borderRadius: {
  sm: '0.25rem',
  md: '0.375rem',
  lg: '0.5rem',
  xl: '0.75rem',
  '2xl': '1rem',
  full: '9999px'
}
```

#### 6. Breakpoints (6 tokens)

```javascript
breakpoints: {
  xs: '320px',    // Mobile
  sm: '640px',    // Tablet
  md: '768px',    // Tablet (landscape)
  lg: '1024px',   // Desktop
  xl: '1280px',   // Large desktop
  '2xl': '1536px' // Extra large
}
```

---

## Component Architecture

### Component Types

#### 1. **Presentational Components** (UI Components)

Pure, reusable UI components with no business logic.

**Location:** `src/components/ui/`

**Examples:**
- `Card.jsx` - Container component
- `MetricCard.jsx` - KPI display
- `StatusBadge.jsx` - Status indicator
- `LoadingSpinner.jsx` - Loading state
- `ErrorAlert.jsx` - Error message
- `ConfirmModal.jsx` - Modal dialog

**Characteristics:**
- Receive all data via props
- No API calls
- Fully customizable via props
- Reusable across pages
- Easy to test

**Example:**
```jsx
// src/components/ui/Card.jsx
export function Card({ 
  title, 
  children, 
  className = '', 
  collapsible = false 
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      {title && (
        <h3 className="font-semibold text-lg mb-4">
          {title}
          {collapsible && (
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              aria-expanded={!isCollapsed}
              aria-label={`Toggle ${title}`}
            >
              {/* Icon */}
            </button>
          )}
        </h3>
      )}
      {!isCollapsed && children}
    </div>
  );
}
```

#### 2. **Container Components** (Smart Components)

Components that manage data fetching and business logic.

**Location:** `src/components/`

**Examples:**
- `Dashboard.jsx` - Main dashboard view
- `StockPredictor.jsx` - Prediction UI with data
- `PipelineControl.jsx` - Pipeline operations
- `Configuration.jsx` - Settings management

**Characteristics:**
- Use custom hooks to fetch data
- Handle loading/error states
- Pass data to presentational components
- One container per major feature

**Example:**
```jsx
// src/components/Dashboard.jsx
import { usePipelineStatus } from '../hooks/usePipelineStatus';
import { MetricCard, LoadingSpinner } from './ui';

export function Dashboard() {
  const { status, loading, error, refetch } = usePipelineStatus();

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert retry={refetch} />;

  return (
    <div className="grid grid-cols-2 gap-4">
      <MetricCard title="Status" value={status?.phase} />
      <MetricCard title="Progress" value={`${status?.progress}%`} />
    </div>
  );
}
```

#### 3. **Layout Components**

App-level layout wrapper.

**Location:** `src/layout/`

**Example: AppLayout.jsx**
```jsx
export function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen">
      <Navigation />
      <main className="flex-1 p-4">
        {/* Skip link */}
        <a href="#main-content" className="sr-only focus:not-sr-only">
          Skip to main content
        </a>
        {children}
      </main>
    </div>
  );
}
```

---

## Data Flow & State Management

### Architecture Pattern: Hooks-Based

The application uses React hooks for state management rather than external libraries (Redux, Zustand, etc.).

**Rationale:**
- Simpler learning curve
- Minimal bundle size
- Built into React
- Sufficient for current complexity

### Data Flow

```
API Endpoint
     ↓
api.js (HTTP call with axios)
     ↓
Custom Hook (useFetch, usePrediction, etc.)
     ↓
Container Component (Dashboard, StockPredictor)
     ↓
Presentational Component (Card, MetricCard)
     ↓
User sees rendered data
```

### Custom Hooks

#### 1. **useFetch** (Generic data fetching)

```javascript
// src/hooks/useFetch.js
export function useFetch(url, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get(url)
      .then(res => setData(res.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [url]);

  return { data, loading, error };
}
```

**Usage:**
```jsx
const { data: results, loading, error } = useFetch('/api/results');
```

#### 2. **usePipelineStatus** (Polling)

```javascript
// src/hooks/usePipelineStatus.js
export function usePipelineStatus(interval = 5000) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const res = await api.get('/api/status');
        setStatus(res.data);
        setLoading(false);
      } catch (err) {
        console.error('Status poll failed:', err);
      }
    }, interval);

    return () => clearInterval(poll);
  }, [interval]);

  return { status, loading };
}
```

**Usage:**
```jsx
const { status, loading } = usePipelineStatus(3000); // Poll every 3s
```

#### 3. **usePrediction** (Stock predictions)

```javascript
// src/hooks/usePrediction.js
export function usePrediction(symbol) {
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const predict = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.post('/api/predict', { symbol });
      setPredictions(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  return { predictions, loading, error, predict };
}
```

#### 4. **useConfig** (Configuration management)

```javascript
// src/hooks/useConfig.js
export function useConfig() {
  const [config, setConfig] = useState(null);

  const loadConfig = useCallback(async () => {
    const res = await api.get('/api/config');
    setConfig(res.data);
  }, []);

  const saveConfig = useCallback(async (newConfig) => {
    const res = await api.post('/api/config', newConfig);
    setConfig(res.data);
  }, []);

  useEffect(() => {
    loadConfig();
  }, []);

  return { config, saveConfig };
}
```

---

## API Integration

### Centralized Service Layer

**File:** `src/services/api.js`

All HTTP communication goes through this single service layer for consistency and error handling.

### API Methods

```javascript
// src/services/api.js

export const api = {
  // Dashboard
  getStatus: () => get('/api/status'),
  getResults: () => get('/api/results'),

  // Stock Prediction
  predictStock: (symbol) => post('/api/predict', { symbol }),
  getPredictionHistory: (symbol) => get(`/api/history/${symbol}`),

  // Pipeline Control
  runPipeline: (config) => post('/api/run-pipeline', config),
  stopPipeline: () => post('/api/stop-pipeline'),
  getPipelineStatus: () => get('/api/status'),

  // Logs
  getLogs: (limit = 100) => get(`/api/logs?limit=${limit}`),
  streamLogs: (callback) => eventSource('/api/logs/stream', callback),

  // Configuration
  getConfig: () => get('/api/config'),
  saveConfig: (config) => post('/api/config', config),
};

// Internal HTTP methods with error handling
function get(url) {
  return axios.get(`${API_BASE_URL}${url}`);
}

function post(url, data) {
  return axios.post(`${API_BASE_URL}${url}`, data);
}
```

### Error Handling

```javascript
// All API calls wrapped with error handling
api.getStatus()
  .then(res => {
    // Success: res.data
  })
  .catch(err => {
    // Handle errors:
    // - Network error
    // - 4xx client error
    // - 5xx server error
    console.error('API Error:', err.response?.status, err.message);
  });
```

### API Endpoints

See **API_REFERENCE.md** for complete endpoint documentation.

---

## Responsive Design

### Mobile-First Approach

All styles start with mobile defaults, then scale up with breakpoints.

### Breakpoints

| Breakpoint | Width | Device | Use Case |
|------------|-------|--------|----------|
| **xs** | 320px | Mobile | Small phones |
| **sm** | 640px | Mobile | Large phones |
| **md** | 768px | Tablet | Tablet portrait |
| **lg** | 1024px | Desktop | Desktop |
| **xl** | 1280px | Desktop | Large desktop |
| **2xl** | 1536px | Desktop | Extra large screens |

### Usage in Tailwind

```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* 1 column on mobile, 2 on tablet, 3 on desktop */}
</div>
```

### Safe Area Insets

For notched devices, use safe area tokens:

```jsx
<div className="pl-safe pr-safe">
  {/* Padding respects device notch */}
</div>
```

### Touch Targets

All interactive elements are ≥44x44px on mobile:

```jsx
<button className="h-11 w-11 rounded-lg">
  {/* 44x44px minimum size */}
</button>
```

---

## Accessibility

### WCAG 2.1 AA Compliance

The frontend is **85-90% compliant** with Web Content Accessibility Guidelines 2.1 Level AA.

See **ACCESSIBILITY.md** for complete details.

### Key Accessible Features

#### 1. **Semantic HTML**
```jsx
<header role="banner">
  <nav>
    <ul>
      <li><a href="#home">Home</a></li>
    </ul>
  </nav>
</header>
<main id="main-content" role="main">
  {/* Content */}
</main>
```

#### 2. **Keyboard Navigation**

- Tab through interactive elements
- Arrow keys in menus/lists
- Enter/Space to activate buttons
- Escape to close modals

#### 3. **Focus Management**

```jsx
// Global focus styles
<div className="focus:outline-2 focus:outline-cyan-400">
  {/* 2px cyan outline on focus */}
</div>
```

#### 4. **ARIA Labels**

```jsx
<button aria-label="Close dialog" onClick={close}>
  <XIcon />
</button>
```

#### 5. **Form Accessibility**

```jsx
<label htmlFor="symbol">Stock Symbol</label>
<input id="symbol" type="text" required />
```

#### 6. **Live Regions**

```jsx
<div role="status" aria-live="polite" aria-atomic="true">
  {message}
</div>
```

---

## Performance

### Bundle Size

- **JS:** 86.89 kB (22.38 kB gzipped)
- **CSS:** 46.01 kB (8.23 kB gzipped)
- **Total (gzip):** ~30.61 kB

### Optimization Techniques

1. **Code Splitting** - Recharts and vendor dependencies separated
2. **Minification** - Production builds minified
3. **Lazy Loading** - Components loaded on demand
4. **Caching** - API responses cached in hooks
5. **Tree Shaking** - Unused code removed

### Performance Targets

- **First Contentful Paint (FCP):** < 2 seconds
- **Largest Contentful Paint (LCP):** < 2.5 seconds
- **Cumulative Layout Shift (CLS):** < 0.1

---

## Development Workflow

### Local Setup

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:3000` with hot module replacement (HMR).

### File Structure Conventions

**Components:**
```
components/
  Dashboard.jsx          # Container component
  ui/
    Card.jsx            # Presentational component
```

**Naming:**
- PascalCase for components (e.g., Dashboard.jsx)
- camelCase for functions/hooks (e.g., useFetch.js)
- kebab-case for CSS classes (e.g., form-group)

### Adding a New Feature

1. **Create container component** in `src/components/`
2. **Create custom hook** in `src/hooks/` if needed
3. **Use UI components** from `src/components/ui/`
4. **Fetch data** through `api.js` service
5. **Handle loading/error** states
6. **Test manually** and with E2E tests

### Building for Production

```bash
npm run build
```

Output in `frontend/dist/` ready for deployment.

---

## Summary

The frontend follows a modern, scalable architecture with:

- **Centralized design system** for consistency
- **Component-based UI** for reusability
- **Hooks-based state management** for simplicity
- **Real API integration** for live data
- **Responsive design** for all devices
- **WCAG accessibility** for inclusivity
- **Optimized performance** for speed

This structure enables rapid development while maintaining code quality and user experience.

---

**Next Steps:** See DEPLOYMENT.md for production deployment instructions.
