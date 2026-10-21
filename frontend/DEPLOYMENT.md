# Deployment Guide

**Version:** 1.0  
**Last Updated:** October 21, 2026  
**Status:** Production Ready  

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Build](#local-build)
3. [Production Build](#production-build)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Strategies](#deployment-strategies)
6. [Server Setup](#server-setup)
7. [Security](#security)
8. [Performance Optimization](#performance-optimization)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [Rollback Procedures](#rollback-procedures)
11. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

- [ ] All 7 phases committed to git
- [ ] All tests passing (manual E2E procedures)
- [ ] No console errors/warnings
- [ ] Performance metrics acceptable (bundle size, LCP, CLS)
- [ ] Accessibility audit complete (85-90% WCAG 2.1 AA)
- [ ] API endpoints tested and working
- [ ] Backend server confirmed running
- [ ] Environment variables configured
- [ ] Security review completed
- [ ] Deployment credentials set up

---

## Local Build

### Prerequisites

```bash
# Node.js 16+
node --version

# npm 8+
npm --version
```

### Build Steps

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Create production build
npm run build

# Output will be in frontend/dist/
```

### Build Output

```
frontend/dist/
├── index.html       # Entry point (25 KB)
├── assets/
│   ├── index-*.js   # Main bundle (86.89 KB → 22.38 KB gzip)
│   ├── index-*.css  # Styles (46.01 KB → 8.23 KB gzip)
│   └── ...          # Other assets
└── favicon.ico      # Favicon
```

### Verify Build

```bash
# Check build size
ls -lh frontend/dist/assets/

# Test locally before deployment
npx serve frontend/dist
# Open http://localhost:3000
```

---

## Production Build

### Build Optimization

The production build includes:

1. **Minification** - Code minified and uglified
2. **Tree Shaking** - Unused code removed
3. **Code Splitting** - Vendor code separated
4. **Lazy Loading** - Components loaded on demand
5. **Source Maps** - Optional for debugging

### Building with Source Maps (for debugging)

```bash
# Production build with source maps
npm run build -- --sourcemap
```

### Building with Environment Variables

```bash
# Set environment before build
VITE_API_URL=https://api.example.com npm run build

# Or in .env.production
VITE_API_URL=https://api.example.com
VITE_LOG_LEVEL=error
```

---

## Environment Configuration

### Environment Variables

Create `.env.production` in frontend directory:

```bash
# Frontend API endpoint
VITE_API_URL=https://api.example.com/api

# Logging level (error, warn, info, debug)
VITE_LOG_LEVEL=error

# Enable/disable features
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_TELEMETRY=false
```

### Using Environment Variables in Code

```javascript
// src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
const LOG_LEVEL = import.meta.env.VITE_LOG_LEVEL || 'info';
```

### Frontend Configuration at Runtime

If you need to change configuration without rebuilding:

1. Create a `config.json` file served with the app
2. Load it on app startup
3. Update components to use runtime config

```javascript
// Load config at runtime
useEffect(() => {
  fetch('/config.json')
    .then(res => res.json())
    .then(config => {
      window.APP_CONFIG = config;
    });
}, []);
```

---

## Deployment Strategies

### Strategy 1: Static Hosting (Recommended)

Deploy `frontend/dist/` to static hosting (simplest, fastest).

#### Netlify

1. **Connect Repository**
   ```bash
   # Install Netlify CLI
   npm install -g netlify-cli
   
   # Connect to repository
   netlify connect
   ```

2. **Configure Build Settings**
   ```
   Build command: npm run build
   Publish directory: frontend/dist
   ```

3. **Deploy**
   ```bash
   netlify deploy --prod
   ```

#### Vercel

1. **Connect Repository**
   - Go to vercel.com
   - Import GitHub repository

2. **Configure**
   ```
   Framework: Vite
   Root directory: frontend
   Build command: npm run build
   Output directory: dist
   ```

3. **Deploy**
   - Vercel auto-deploys on git push

#### AWS S3 + CloudFront

1. **Build**
   ```bash
   npm run build
   ```

2. **Upload to S3**
   ```bash
   aws s3 sync frontend/dist/ s3://your-bucket-name/
   ```

3. **Create CloudFront Distribution**
   - Set origin to S3 bucket
   - Configure cache settings
   - Deploy

4. **Configure Routing**
   - Route all requests to index.html for SPA routing

### Strategy 2: Docker Container

Deploy frontend in Docker container with Node server.

#### Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run static files
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/frontend/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

#### Build and Run

```bash
# Build Docker image
docker build -t stock-optimizer-frontend .

# Run container
docker run -p 3000:3000 stock-optimizer-frontend

# Deploy to Docker registry
docker tag stock-optimizer-frontend myregistry/stock-optimizer-frontend:latest
docker push myregistry/stock-optimizer-frontend:latest
```

#### Docker Compose (with Backend)

```yaml
version: '3.8'

services:
  frontend:
    image: stock-optimizer-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://backend:5000/api
    depends_on:
      - backend

  backend:
    image: stock-optimizer-backend:latest
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
```

### Strategy 3: Traditional Server (Node.js)

Deploy with Express server (more control).

#### Express Server

```javascript
// server.js
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();

// Serve static files
app.use(express.static(path.join(__dirname, 'dist')));

// SPA routing - serve index.html for all routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist/index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

#### Run Server

```bash
# Install dependencies
npm install express

# Start server
node server.js

# Or with PM2 for process management
npm install -g pm2
pm2 start server.js --name "stock-optimizer-frontend"
pm2 startup
pm2 save
```

---

## Server Setup

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/stock-optimizer

upstream backend {
  server localhost:5000;
}

server {
  listen 80;
  server_name example.com www.example.com;

  # Redirect HTTP to HTTPS
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  server_name example.com www.example.com;

  # SSL certificates (use Let's Encrypt)
  ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

  # Frontend serving
  location / {
    root /var/www/stock-optimizer/frontend/dist;
    try_files $uri $uri/ /index.html;
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
      expires 1y;
      add_header Cache-Control "public, immutable";
    }
    
    # No cache for HTML
    location ~* \.html$ {
      expires -1;
      add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
  }

  # Backend proxy
  location /api/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
  }

  # Gzip compression
  gzip on;
  gzip_types text/plain text/css text/javascript application/json application/javascript;
  gzip_min_length 1000;
  gzip_comp_level 6;
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/stock-optimizer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Security

### Content Security Policy (CSP)

Add CSP header to prevent XSS:

```nginx
# In Nginx config
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
```

### HTTPS/SSL

Use Let's Encrypt for free SSL certificates:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d example.com

# Auto-renew
sudo systemctl enable certbot.timer
```

### CORS Configuration

```javascript
// Backend cors setup
from flask_cors import CORS

app = Flask(__name__)

# Only allow specific origins in production
CORS(app, origins=[
  'https://example.com',
  'https://www.example.com'
])
```

### Environment Secrets

Never commit secrets to git:

```bash
# .gitignore
.env
.env.production
.env.local
```

Use environment variables for sensitive data:

```javascript
// Never hardcode API keys
const API_KEY = process.env.VITE_API_KEY;
```

---

## Performance Optimization

### Caching Strategies

#### Browser Caching (Nginx)

```nginx
# Long cache for assets with hash
location ~* \.(js|css)$ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

# Short/no cache for HTML
location ~* \.html$ {
  expires -1;
  add_header Cache-Control "no-cache, must-revalidate";
}
```

#### CDN Caching

Use a CDN to cache static assets globally:

- Cloudflare
- AWS CloudFront
- KeyCDN

### Image Optimization

```html
<!-- Use modern image formats -->
<picture>
  <source srcset="image.webp" type="image/webp">
  <source srcset="image.jpg" type="image/jpeg">
  <img src="image.jpg" alt="Description">
</picture>
```

### Bundle Analysis

```bash
# Analyze bundle size
npm install -g vite-bundle-visualizer

# Check what's taking space
npm run build -- --outDir dist --reportCompressedSize
```

### Lighthouse Audit

```bash
# Run Lighthouse locally
npm install -g @lhci/cli@latest

# Generate report
lighthouse https://example.com --output=html
```

---

## Monitoring & Maintenance

### Uptime Monitoring

Use services like:

- **Pingdom** - Monitors uptime and alerts
- **Better Stack** - Incident management
- **StatusPage.io** - Status page for users

### Error Tracking

Use services like:

- **Sentry** - JavaScript error tracking
- **LogRocket** - Session replay and debugging

### Analytics

Track user behavior:

```javascript
// src/analytics.js
export function trackEvent(name, data) {
  if (window.gtag) {
    gtag.event(name, data);
  }
}
```

### Logs

Centralize logs for debugging:

- **CloudWatch** (AWS)
- **Stackdriver** (Google Cloud)
- **ELK Stack** (Self-hosted)

---

## Rollback Procedures

### Immediate Rollback

If issues occur after deployment:

#### Using Nginx

```bash
# Keep previous versions
ls -la /var/www/stock-optimizer/releases/

# Symlink to previous version
sudo ln -snf /var/www/stock-optimizer/releases/v1.0 /var/www/stock-optimizer/current

# Reload Nginx
sudo systemctl reload nginx
```

#### Using Git

```bash
# Revert to previous version
git revert HEAD
npm run build
npm run deploy
```

#### Using Docker

```bash
# Tag previous version
docker tag myregistry/stock-optimizer-frontend:v1.1 myregistry/stock-optimizer-frontend:latest

# Deploy previous version
docker pull myregistry/stock-optimizer-frontend:latest
docker run -p 3000:3000 myregistry/stock-optimizer-frontend:latest
```

### Version Management

Keep version file:

```json
// frontend/public/version.json
{
  "version": "1.0.0",
  "build": "20261021",
  "timestamp": "2026-10-21T14:30:00Z"
}
```

Check version on load:

```javascript
// src/App.jsx
useEffect(() => {
  fetch('/version.json')
    .then(res => res.json())
    .then(data => {
      console.log('App version:', data.version);
    });
}, []);
```

---

## Troubleshooting

### Build Fails

```bash
# Clear cache and node_modules
rm -rf node_modules dist
npm install
npm run build
```

### API Connection Issues

```javascript
// Add debugging
console.log('API URL:', import.meta.env.VITE_API_URL);

// Check CORS headers
curl -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS https://api.example.com/api/status -v
```

### High Bundle Size

```bash
# Analyze what's included
npm install --save-dev vite-plugin-visualizer

# See size breakdown
npm run build
```

### Slow Page Load

```bash
# Check with Lighthouse
lighthouse https://example.com

# Measure performance
npm install --save-dev web-vitals

// In App.jsx
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);
```

### White Screen After Deploy

1. Check browser console for errors
2. Verify API_BASE_URL is correct
3. Check backend server is running
4. Clear browser cache (Ctrl+Shift+Delete)

---

## Deployment Checklist

Before each deployment:

- [ ] All tests passing
- [ ] Git branch up-to-date with main
- [ ] No uncommitted changes
- [ ] Environment variables configured
- [ ] Backend API running
- [ ] Build completes successfully
- [ ] Bundle size acceptable
- [ ] No console errors/warnings
- [ ] Lighthouse score > 80
- [ ] Accessibility audit passing
- [ ] Deploy to staging first
- [ ] Test on staging
- [ ] Get approval from team
- [ ] Deploy to production
- [ ] Monitor for errors

---

## Post-Deployment Steps

1. **Verify Deployment**
   - Check app loads without errors
   - Test main workflows
   - Monitor error tracking service

2. **Update Documentation**
   - Update version number
   - Document any deployment issues
   - Add release notes

3. **Notify Team**
   - Send deployment summary
   - Include version and changes
   - Provide rollback instructions

4. **Monitor**
   - Watch error rate
   - Check performance metrics
   - Monitor user feedback

---

## Summary

Deployment involves:

1. **Build** - Create production bundle
2. **Configure** - Set environment variables
3. **Deploy** - Upload to hosting service
4. **Verify** - Test deployed application
5. **Monitor** - Track performance and errors

Choose deployment strategy based on:

- **Static Hosting** (Netlify/Vercel) - Simplest, recommended
- **Docker** - Better control, scalable
- **Traditional Server** - Full control, more maintenance

---

**Next Steps:** See ACCESSIBILITY.md for WCAG compliance details.
