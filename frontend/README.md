# Stock Optimizer - Frontend

Modern React-based web interface for the Stock Market Forecasting System.

## Features

- **Dashboard** - Real-time pipeline status and performance metrics
- **Data Acquisition** - Configure and run data pipeline with live logs
- **Model Results** - View baseline model performance and feature importance
- **Configuration** - Manage pipeline settings and reproducibility parameters
- **Interactive Charts** - Visualize predictions, metrics, and comparisons

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Recharts** - Interactive charts
- **Lucide Icons** - Icon library
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

The app will open at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Output will be in `frontend/dist/`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Navigation.jsx      # Top navigation bar
│   │   ├── Dashboard.jsx       # Dashboard tab
│   │   ├── DataAcquisition.jsx # Data pipeline control
│   │   ├── ModelResults.jsx    # Model performance
│   │   └── Configuration.jsx   # Settings management
│   ├── App.jsx                 # Main app component
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
├── index.html                  # HTML template
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
├── postcss.config.js           # PostCSS configuration
└── package.json                # Dependencies

```

## API Integration

The frontend communicates with the backend via:

```
GET  /api/status              - Pipeline status
POST /api/run-pipeline        - Start pipeline execution
GET  /api/results             - Get latest results
POST /api/config              - Update configuration
GET  /api/logs                - Stream execution logs
```

See `../api_server.py` for backend implementation.

## Features

### Dashboard Tab
- Real-time pipeline status indicator
- Key metrics (symbols processed, data points, features, models)
- Price prediction vs actual comparison
- Baseline model performance comparison

### Data Acquisition Tab
- Configure data source (Mock/IEX/Yahoo Finance)
- Set lookback period and symbols
- Run/stop pipeline with live logs
- Monitor data quality metrics

### Model Results Tab
- Best model ranking (Ridge Regression, ARIMA, etc.)
- Performance metrics (MAE, RMSE, directional accuracy)
- Feature importance analysis by tier
- Detailed evaluation statistics

### Configuration Tab
- Data acquisition settings
- Train/val/test split ratios
- Feature tier toggles
- Reproducibility parameters
- JSON configuration preview

## Styling

Using Tailwind CSS utility classes with custom color scheme:
- **Primary:** Blue (#0066cc, #1e40af)
- **Success:** Green (#22c55e)
- **Warning:** Orange (#f97316)
- **Error:** Red (#ef4444)
- **Background:** Slate (#0f172a, #1e293b, #334155)

## Performance

- Code splitting with Recharts and vendor bundle separation
- Lazy loading of components
- Minified production builds (~150KB gzipped)
- Fast refresh during development

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
VITE_API_URL=http://localhost:5000/api
VITE_LOG_LEVEL=debug
```

## Troubleshooting

### Port 3000 already in use
```bash
npm run dev -- --port 3001
```

### Proxy not connecting to backend
- Ensure backend is running on `localhost:5000`
- Check `vite.config.js` proxy configuration
- Verify no firewall blocking localhost connections

### Styles not loading
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Rebuild Tailwind: `npm run build`

## Future Enhancements

- [ ] Real-time data streaming (WebSocket)
- [ ] Advanced chart customization
- [ ] Export reports to PDF/Excel
- [ ] Backtesting visualization
- [ ] Portfolio optimization UI
- [ ] Market comparison tools
- [ ] Model fine-tuning interface

## Contributing

1. Create a branch from `main`
2. Make changes to components in `src/`
3. Run `npm run lint` to check code
4. Test in dev server with `npm run dev`
5. Submit PR with description of changes

## License

MIT

---

**Frontend Status:** ✅ Ready for Development  
**Last Updated:** October 14, 2026
