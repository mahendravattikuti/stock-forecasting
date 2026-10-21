# Contributing Guidelines

**Version:** 1.0  
**Last Updated:** October 21, 2026  

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Code Standards](#code-standards)
4. [Testing](#testing)
5. [Documentation](#documentation)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Architecture Guidelines](#architecture-guidelines)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Node.js 16+
- npm 8+
- Git
- Text editor (VS Code recommended)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/mahendravattikuti/stock-forecasting.git
cd stock-forecasting/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# App opens at http://localhost:3000
```

### Verify Setup

```bash
# Run build
npm run build

# Check bundle size
ls -lh dist/assets/

# All should complete without errors
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/description-of-feature
```

**Branch naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test additions
- `perf/` - Performance improvements

### 2. Make Changes

```bash
# Edit files in src/
nano src/components/MyComponent.jsx

# Save with Ctrl+S
# Auto-format with Prettier (if configured)
```

### 3. Test Changes

```bash
# Dev server with hot reload
npm run dev

# Manual testing at http://localhost:3000
```

### 4. Commit Changes

```bash
# Stage specific files (not all)
git add src/components/MyComponent.jsx

# Commit with clear message
git commit -m "feat: Add new stock search feature"

# Push to remote
git push origin feature/description-of-feature
```

### 5. Create Pull Request

```bash
# On GitHub, create PR from feature branch to main
# Add description of changes
# Request review from team
```

### 6. Address Review Feedback

```bash
# Make requested changes
git add .
git commit -m "fix: Address code review feedback"

# Push updates (same branch)
git push origin feature/description-of-feature
```

### 7. Merge to Main

```bash
# After approval, merge PR on GitHub
# Delete feature branch after merge
```

---

## Code Standards

### File Organization

```
src/
├── components/           # React components
│   ├── Container.jsx    # Container (smart) components
│   ├── ui/
│   │   ├── Button.jsx   # Presentational (dumb) components
│   │   └── index.js     # Barrel export
│   └── index.js
├── hooks/               # Custom React hooks
│   ├── useFetch.js
│   └── index.js
├── services/            # Business logic & API
│   ├── api.js
│   └── index.js
├── context/             # React Context
│   └── ThemeContext.jsx
├── theme/               # Design tokens
│   ├── tokens.js
│   └── index.js
├── layout/              # Layout components
│   └── AppLayout.jsx
├── App.jsx              # Root component
├── main.jsx             # Entry point
└── index.css            # Global styles
```

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase | `Dashboard.jsx` |
| Hooks | camelCase with `use` prefix | `useFetch.js` |
| Functions | camelCase | `handleClick` |
| Constants | UPPER_SNAKE_CASE | `API_BASE_URL` |
| CSS classes | kebab-case | `btn-primary` |
| Files | Match exported item | `Dashboard.jsx` exports `Dashboard` |

### Component Structure

```jsx
// src/components/MyComponent.jsx

import React, { useState, useEffect } from 'react';
import { Card, MetricCard } from './ui';
import { useFetch } from '../hooks';
import { api } from '../services/api';

/**
 * MyComponent - Description of what it does
 * 
 * Features:
 * - Feature 1
 * - Feature 2
 */
export function MyComponent({ title, children }) {
  const [state, setState] = useState(null);
  const { data, loading } = useFetch('/api/endpoint');

  useEffect(() => {
    // Effects here
  }, []);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState />;

  return (
    <Card title={title}>
      {children}
    </Card>
  );
}

export default MyComponent;
```

### Code Quality

```jsx
// ✅ Good: Clear, readable code

function handlePrediction(symbol) {
  if (!symbol.trim()) {
    setError('Symbol is required');
    return;
  }

  setLoading(true);
  api.predictStock(symbol)
    .then(data => {
      setPredictions(data);
      setError(null);
    })
    .catch(err => {
      setError(err.message);
      console.error('Prediction failed:', err);
    })
    .finally(() => setLoading(false));
}

// ❌ Bad: Unclear, hard to follow

function pred(s) {
  if (s) {
    setL(true);
    api.p(s).then(d => setP(d)).catch(e => setE(e)).finally(() => setL(false));
  }
}
```

### Import Statements

```jsx
// ✅ Good: Organized imports

// External libraries
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Custom components
import { Card, MetricCard } from './ui';
import { Dashboard } from '../Dashboard';

// Hooks
import { useFetch } from '../../hooks';

// Services
import { api } from '../../services/api';

// Styles
import './MyComponent.css';

// ❌ Bad: Random order, mixing
import { api } from '../../services/api';
import React from 'react';
import { Card } from './ui';
import './MyComponent.css';
import { useFetch } from '../../hooks';
```

### Error Handling

```jsx
// ✅ Good: Comprehensive error handling

try {
  const response = await api.get('/endpoint');
  setData(response.data);
} catch (error) {
  if (error.response?.status === 404) {
    setError('Resource not found');
  } else if (error.response?.status === 500) {
    setError('Server error - please try again later');
  } else if (error.message === 'Network Error') {
    setError('Network connection failed');
  } else {
    setError('An unexpected error occurred');
  }
  console.error('API error:', error);
}

// ❌ Bad: Ignoring errors

const data = await api.get('/endpoint');
setData(data);
```

### Comments

```jsx
// ✅ Good: Meaningful comments explaining WHY, not WHAT

// Need to debounce search to reduce API calls
const debouncedSearch = useCallback(
  debounce((value) => {
    api.search(value);
  }, 500),
  []
);

// ❌ Bad: Comments stating obvious

// Set the state
setState(value);

// This is a function that fetches data
const fetchData = async () => { ... }
```

---

## Testing

### Manual Testing

Before submitting PR, test:

1. **Functionality**
   ```
   - Navigate through all pages
   - Click all buttons
   - Fill and submit forms
   - Verify data displays correctly
   ```

2. **Keyboard Navigation**
   ```
   - Tab through all elements
   - Use arrow keys in menus
   - Enter to activate buttons
   - Escape to close modals
   ```

3. **Screen Reader (NVDA/VoiceOver)**
   ```
   - Elements announced correctly
   - Form labels associated
   - Page landmarks announced
   - Status updates announced
   ```

4. **Responsive Design**
   ```
   - Chrome DevTools: Responsive mode
   - Test xs, sm, md, lg, xl, 2xl breakpoints
   - Check mobile menu works
   - Touch targets ≥44x44px
   ```

5. **Performance**
   ```
   - No console errors
   - Lighthouse score > 80
   - Bundle size acceptable
   - Animations smooth
   ```

### Writing Tests

Tests go in `e2e/` directory:

```markdown
# e2e/feature-name.test.md

## Feature: Stock Search

### Test 1: Search returns results
1. Load app
2. Click search box
3. Type "AAPL"
4. Verify results appear
5. ✅ PASS

### Test 2: Keyboard navigation
1. Load app
2. Click search box
3. Type "AAPL"
4. Press arrow keys to navigate
5. Press Enter to select
6. Verify selection made
7. ✅ PASS
```

---

## Documentation

### When to Document

- New components
- New hooks
- API changes
- Configuration changes
- Major features

### Where to Document

1. **Component Comments** (in code)
   ```jsx
   /**
    * MyComponent - Description
    * 
    * Features:
    * - Feature 1
    * - Feature 2
    */
   ```

2. **README.md** (quick start)
   ```markdown
   ## New Feature
   Brief description and quick example
   ```

3. **COMPONENTS.md** (detailed docs)
   ```markdown
   ### MyComponent
   Props, examples, features
   ```

4. **CHANGELOG.md** (version history)
   ```markdown
   ### Added
   - New MyComponent with features
   ```

---

## Commit Guidelines

### Commit Message Format

```
type(scope): subject

body

footer
```

### Type

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting)
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Tests
- `chore` - Dependencies, build config

### Examples

```bash
# Good commits
git commit -m "feat: Add stock search autocomplete"
git commit -m "fix: Focus trap not working in modal"
git commit -m "docs: Update accessibility documentation"
git commit -m "perf: Optimize bundle size by removing unused deps"

# Bad commits
git commit -m "update"
git commit -m "fix stuff"
git commit -m "changes"
```

### Detailed Message

For complex changes:

```bash
git commit -m "feat: Add real-time log streaming

- Implement SSE (Server-Sent Events) for log updates
- Add log filtering by level
- Add search within logs
- Add export to CSV

Closes #123"
```

---

## Pull Request Process

### PR Title

Keep under 70 characters, be descriptive:

```
✅ Good:
- Add stock search with autocomplete
- Fix modal focus trap on close
- Update accessibility documentation

❌ Bad:
- fix bugs
- update components
- phase 3
```

### PR Description

```markdown
## Description
Brief explanation of changes

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [x] Manual testing complete
- [x] Keyboard navigation verified
- [x] Responsive design tested
- [x] Lighthouse score > 80

## Screenshots (if UI changes)
[Attach before/after screenshots]

## Related Issues
Fixes #123
```

### PR Checklist

Before submitting:

- [ ] Branch created from latest `main`
- [ ] All changes committed to feature branch
- [ ] Code follows project style
- [ ] Comments explain WHY, not WHAT
- [ ] Manual testing complete
- [ ] No console errors/warnings
- [ ] Accessibility verified
- [ ] Performance acceptable
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Ready for review

### Review Process

1. **Automated Checks**
   - Code lint passes
   - Build succeeds
   - Bundle size acceptable

2. **Code Review**
   - Architecture follows patterns
   - Code quality is good
   - Tests are thorough
   - Documentation is clear

3. **Approval**
   - Minimum 1 approval required
   - All feedback addressed
   - Ready to merge

---

## Architecture Guidelines

### Component Types

#### Container Components

```jsx
// ✅ Handle data fetching and state
export function Dashboard() {
  const { status, loading } = usePipelineStatus();

  if (loading) return <LoadingSpinner />;

  return <DashboardView status={status} />;
}
```

#### Presentational Components

```jsx
// ✅ Receive all data via props, no API calls
export function StatusBadge({ status, label }) {
  return (
    <div className={`badge badge-${status}`}>
      {label}
    </div>
  );
}
```

### Custom Hooks

```jsx
// ✅ Reusable logic
export function useFetch(url) {
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

### State Management

For simple state, use `useState`:

```jsx
const [count, setCount] = useState(0);
```

For complex state, use `useContext`:

```jsx
const { theme, setTheme } = useContext(ThemeContext);
```

Avoid adding Redux/Zustand unless necessary.

### API Integration

Always use `api.js` service:

```jsx
// ✅ Good: Use centralized API
const { data } = useFetch('/api/endpoint');

// ❌ Bad: Direct fetch in component
useEffect(() => {
  fetch('/api/endpoint')
    .then(res => res.json())
    .then(data => setData(data));
}, []);
```

---

## Common Tasks

### Add a New Component

```bash
# 1. Create component file
touch src/components/MyNewComponent.jsx

# 2. Write component
cat > src/components/MyNewComponent.jsx << 'EOF'
export function MyNewComponent() {
  return <div>Hello</div>;
}
EOF

# 3. Update barrel export
echo "export { MyNewComponent } from './MyNewComponent';" >> src/components/index.js

# 4. Test component
npm run dev

# 5. Commit
git add src/components/
git commit -m "feat: Add MyNewComponent"
```

### Update Dependencies

```bash
# Check for updates
npm outdated

# Update specific package
npm update package-name

# Update all packages
npm update

# Test build
npm run build

# Commit
git add package*.json
git commit -m "chore: Update dependencies"
```

### Fix Build Issues

```bash
# Clear cache
rm -rf node_modules dist

# Reinstall
npm install

# Rebuild
npm run build

# If still failing, check Vite config
cat vite.config.js
```

### Profile Performance

```bash
# Generate bundle analysis
npm run build

# Check bundle size
npm run build -- --sourcemap
ls -lh dist/assets/

# Use Chrome DevTools Performance tab
# 1. Open http://localhost:3000
# 2. Chrome DevTools → Performance
# 3. Record, interact, stop
# 4. Analyze timeline
```

---

## Troubleshooting

### Port 3000 Already in Use

```bash
# Use different port
npm run dev -- --port 3001

# Or kill process on port 3000
# macOS/Linux:
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

### Hot Reload Not Working

```bash
# Check vite.config.js
# Ensure HMR is configured:
export default {
  server: {
    hmr: {
      host: 'localhost',
      port: 3000,
    },
  },
};

# Restart dev server
npm run dev
```

### Build Size Increasing

```bash
# Analyze what's taking space
npm run build

# Check imports - avoid duplicate deps
# Look for:
# - Large libraries (use alternatives)
# - Unused dependencies (remove)
# - Unused code (tree-shake)

# Remove unused dependency
npm uninstall package-name
```

### API Endpoint Returns 404

```bash
# 1. Check URL is correct
console.log(import.meta.env.VITE_API_URL);

# 2. Verify backend is running
curl http://localhost:5000/api/status

# 3. Check CORS headers
curl -H "Origin: http://localhost:3000" \
  -X OPTIONS http://localhost:5000/api/status -v

# 4. Update environment variable if needed
VITE_API_URL=http://localhost:5000/api npm run dev
```

### Component Not Appearing

```bash
# 1. Check import statement
import { MyComponent } from './MyComponent';

# 2. Verify file path is correct
ls -la src/components/MyComponent.jsx

# 3. Check export statement in file
export function MyComponent() { ... }

# 4. Restart dev server
npm run dev
```

---

## Resources

### Documentation
- [React Docs](https://react.dev/)
- [Vite Docs](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Accessibility (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)

### Tools
- [VS Code](https://code.visualstudio.com/)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

### Learning
- [Atomic Design](https://atomicdesign.bradfrost.com/)
- [Component Patterns](https://patterns.dev/)
- [Web Accessibility](https://www.a11yproject.com/)

---

## Summary

**Key Points:**
1. Create feature branch (`feature/description`)
2. Follow code standards and naming conventions
3. Test thoroughly (functionality, keyboard, screen reader, responsive)
4. Write clear, meaningful commits
5. Update documentation
6. Create descriptive PR with checklist
7. Address feedback and merge

**Architecture:**
- Container + Presentational components
- Custom hooks for reusable logic
- Centralized API service
- Design tokens for consistency

---

## Questions?

- Check existing PRs for examples
- Review CONTRIBUTING.md again
- Ask team members for help
- Open an issue on GitHub

---

**Happy Contributing! 🚀**
