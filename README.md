# Stock Forecasting System

## Regime-Aware Multi-Scale Deep Stock Forecasting with WT, SSA, Kalman Filtering, Novel Market Attributes, Attention, and IJF-F Optimization

A comprehensive, research-grade stock market forecasting system combining multi-scale signal processing, novel market features, deep learning, and advanced optimization.

### 🎯 Project Goals

Develop a reproducible stock price forecasting system that:
- Predicts next-day closing prices and returns
- Combines multi-scale signal decomposition (Wavelet, SSA, Kalman)
- Incorporates market context (regime awareness, cross-asset relationships)
- Uses attention-based deep temporal networks
- Implements systematic ablation studies
- Maintains strict data integrity (no leakage)
- Provides full reproducibility

### ✨ Key Features

#### Data Pipeline
- **Multi-source data acquisition** (IEX Cloud + yfinance fallback)
- **Robust data cleaning** (missing value handling, spike detection, OHLC validation)
- **Stock split/dividend adjustment**
- **Comprehensive data quality validation**

#### Feature Engineering
- **Tier-1 Features:** Returns, normalized prices/volumes
- **Tier-2 Features:** 10+ technical indicators (RSI, MACD, Bollinger, ATR, ADX, OBV, etc.)
- **Tier-3 Features:** Market regime, relative strength, sector correlation
- **Signal Processing:** Wavelet Transform, Singular Spectrum Analysis, Kalman Filtering
- **Cross-Asset Features:** Market context, sector relationships

#### Deep Learning
- **Temporal DCNN** architecture with skip connections
- **Attention mechanisms** for interpretability
- **Configurable model architecture**

#### Optimization
- **IJF-F metaheuristic** optimization
- **Baseline models** for comparison (Random Walk, ARIMA, Linear/Ridge Regression)
- **Ablation studies** to measure feature contributions

#### Reproducibility
- Fixed random seeds (numpy, random, TensorFlow)
- Configuration management
- Artifact versioning
- Detailed audit trails
- Experiment tracking

### 📊 Project Structure

```
stock-forecasting/
├── config/                    # Configuration management
│   └── config_loader.py
├── preprocessing/             # Data pipeline
│   ├── data_acquisition/      # Data fetching (IEX, yfinance)
│   └── data_cleaning/         # Cleaning & validation (IN PROGRESS)
├── features/                  # Feature engineering
│   ├── tier1/                 # Basic features
│   ├── tier2/                 # Technical indicators
│   ├── tier3/                 # Market context
│   ├── signal_processing/     # Wavelet, SSA, Kalman
│   └── cross_asset/           # Cross-market features
├── baselines/                 # Baseline models
├── models/                    # Deep learning models
├── evaluation/                # Metrics & validation
├── ablation/                  # Ablation studies
├── reporting/                 # Reports & visualizations
├── utils/                     # Utilities (logging, reproducibility)
├── .kiro/specs/               # Research specifications
│   └── stock-forecasting-system/
│       ├── requirements.md    # Detailed requirements
│       ├── design.md          # Technical design
│       └── tasks.md           # Implementation tasks
├── master_config.json         # Pipeline configuration
├── requirements.txt           # Python dependencies
└── results/                   # Output directory
```

### 🚀 Quick Start

#### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/stock-forecasting.git
cd stock-forecasting

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configuration

Edit `master_config.json` to set:
- Stock symbols
- Date ranges
- Feature selections
- Model parameters
- IEX Cloud API token (optional, fallback to yfinance)

#### Run Pipeline

```bash
# Run full pipeline
python pipeline.py

# Or test components
from preprocessing.data_acquisition import YFinanceAdapter
adapter = YFinanceAdapter()
df = adapter.fetch('AAPL', '2022-01-01', '2024-01-19')
```

### 📋 Development Status

#### ✅ Completed (28%)
- Phase 1: Project Setup & Configuration
- Phase 2: Data Acquisition (IEX + yfinance)
- Phase 3: Data Cleaning (partial - detectors & validators)

#### 🔄 In Progress
- Phase 3: Data Cleaning (correctors & orchestrator)
- Phase 4: Data Quality Validation

#### 📝 Planned
- Phase 5-10: Feature Engineering
- Phase 11-18: Model Training & Integration
- Phase 19-20: Documentation & Testing

### 📚 Documentation

- **requirements.md** - Detailed functional and non-functional requirements
- **design.md** - Technical architecture and component specifications
- **tasks.md** - Implementation task breakdown with effort estimates
- **IMPLEMENTATION_PROGRESS.md** - Current implementation status
- **CONTINUATION_GUIDE.md** - Guide for continuing development

### 🧪 Testing

Run component tests:

```bash
# Test data acquisition
python -m preprocessing.data_acquisition.test_acquisition

# Test data cleaning (once implemented)
python -m preprocessing.data_cleaning.test_cleaning
```

### 📊 Datasets

- **Primary:** Daily OHLCV stock market data
- **Source:** IEX Cloud (primary) or Yahoo Finance (fallback)
- **Coverage:** 10+ years of historical data (configurable)
- **Symbols:** S&P 500 constituents (configurable)

### 🔒 Data Integrity

**Strict prevention of data leakage:**
- Chronological train/validation/test splits (70%/15%/15%)
- All preprocessing fitted on training data only
- No future information in rolling calculations
- Temporal integrity verified

### 📈 Evaluation Metrics

- **MAE, RMSE, MAPE** - Price prediction accuracy
- **Directional Accuracy** - Up/down prediction accuracy
- **Sharpe Ratio** - Risk-adjusted performance
- **Information Coefficient** - Ranking ability
- **95% Confidence Intervals** - Via bootstrapping (1,000 resamples)

### 🛠️ Key Technologies

- **Data:** pandas, numpy, scipy
- **ML:** scikit-learn, TensorFlow
- **Signal Processing:** PyWavelets
- **Data Acquisition:** yfinance, requests
- **Testing:** pytest, hypothesis
- **Visualization:** matplotlib, plotly

### 📝 Configuration

All parameters configurable in `master_config.json`:

```json
{
  "data_acquisition": {
    "primary_source": "iex_cloud",
    "fallback_source": "yfinance",
    "lookback_years": 10
  },
  "feature_engineering": {
    "tier1_enabled": true,
    "tier2_enabled": true,
    "tier3_enabled": true,
    "signal_processing_enabled": false
  },
  "data_splitting": {
    "train_ratio": 0.70,
    "val_ratio": 0.15,
    "test_ratio": 0.15
  }
}
```

### 🔍 Reproducibility

Every experiment includes:
- Fixed random seeds (numpy, random, TensorFlow)
- Saved configuration
- Artifact versioning
- Audit trails
- Experiment metadata

### 🤝 Contributing

This is a research project. Contributions welcome for:
- Feature engineering improvements
- Model architecture enhancements
- Performance optimizations
- Documentation

### 📄 License

MIT License - See LICENSE file for details

### 📖 Citation

If you use this system in research, please cite:

```bibtex
@software{stock_forecasting_2024,
  title={Stock Forecasting System},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/stock-forecasting}
}
```

### 🔗 References

**Specification Documents:**
- `requirements.md` - Full requirements
- `design.md` - Technical design

**Progress Tracking:**
- `IMPLEMENTATION_PROGRESS.md`
- `PHASE2_COMPLETION_SUMMARY.md`
- `PHASE3_PROGRESS.md`
- `CONTINUATION_GUIDE.md`

### 📞 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Status:** Stage 1 Implementation (28% Complete)  
**Last Updated:** 2024-01-19  
**Python Version:** 3.10+
