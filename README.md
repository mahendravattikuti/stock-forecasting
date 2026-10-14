# Stock Market Forecasting System

A research-grade, reproducible platform for predicting next-day stock closing prices and returns using multi-scale signal processing, novel market features, deep temporal networks with attention mechanisms, and advanced optimization.

## Overview

This system synthesizes cutting-edge time series analysis techniques to forecast daily stock prices with scientific rigor and interpretability. Key capabilities include:

- **Multi-source data acquisition** with automatic fallback mechanisms (IEX Cloud + yfinance)
- **Comprehensive data cleaning** with spike detection, missing value handling, and quality validation
- **Advanced feature engineering** across three tiers: basic returns, technical indicators, and market context
- **Signal processing decomposition** using Wavelet Transform, Singular Spectrum Analysis, and Kalman Filtering
- **Chronological train/validation/test splits** with strict data leakage prevention
- **Baseline model suite** (Random Walk, ARIMA, Linear/Ridge Regression, Historical Mean) for result contextualization
- **Reproducibility-first design** with comprehensive logging, configuration management, and artifact versioning

The system processes data through a 13-phase pipeline orchestration, generating cleaned datasets, feature manifests, baseline results, and detailed reports—all designed for scientific rigor and extensibility.

## Installation

### Prerequisites

- **Python 3.10+** (tested on 3.10.12)
- **pip** (Python package manager)
- **Git** (for version control)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd stock-forecasting-system
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API credentials:**
   
   The system requires an IEX Cloud API token for primary data acquisition. Set it as an environment variable:
   
   ```bash
   export IEX_CLOUD_TOKEN="your_api_token_here"
   ```
   
   On Windows:
   ```cmd
   set IEX_CLOUD_TOKEN=your_api_token_here
   ```
   
   You can obtain a token by registering at [IEX Cloud](https://iexcloud.io). The system automatically falls back to Yahoo Finance (yfinance) if IEX Cloud is unavailable.

5. **Verify installation:**
   ```bash
   python -c "import numpy, pandas, sklearn; print('Dependencies OK')"
   python -m pytest tests/ -v --tb=short  # Run test suite (optional)
   ```

## Quick Start

### Basic Usage

Run the complete 13-phase pipeline with default configuration:

```bash
python pipeline.py
```

This will:
1. Acquire daily OHLCV data for symbols in `master_config.json` (default: AAPL, MSFT, GOOGL, AMZN, TSLA)
2. Clean and validate the data
3. Engineer features across three tiers
4. Split data chronologically (70% train, 15% validation, 15% test)
5. Preprocess and scale features
6. Train baseline models
7. Generate comprehensive reports and artifacts

### Example: Custom Symbol List

Edit `master_config.json` to use a custom symbol list:

```json
{
  "symbols": {
    "list": ["AAPL", "MSFT", "JPMORGAN", "JNJ"],
    "max_portfolio_size": 100,
    "supported_exchanges": ["NYSE", "NASDAQ", "AMEX"]
  }
}
```

Then run:

```bash
python pipeline.py
```

### Example: Partial Pipeline Run (In Python)

For advanced usage, instantiate the pipeline directly:

```python
from pipeline import StockForecastingPipeline

# Initialize with custom config
pipeline = StockForecastingPipeline(config_path='master_config.json')

# Run full pipeline
results = pipeline.run(symbols=['AAPL', 'MSFT', 'GOOGL'])

# Access results
print(f"Symbols processed: {len(results['cleaned_data'])}")
print(f"Baseline results saved to: {results['baseline_results_path']}")
```

### Output Artifacts

After running the pipeline, check the `results/` directory for:

- **`cleaning_report.json`** - Data quality and cleaning actions per symbol
- **`validation_report.json`** - Quality assurance pass/fail status
- **`features_manifest.json`** - Feature definitions and computation metadata
- **`splits_metadata.json`** - Train/validation/test date ranges
- **`baseline_results.json`** - Evaluation metrics for all baseline models
- **`pipeline_report.md`** - Human-readable summary of execution
- **`logs/pipeline_*.log`** - Detailed execution logs with timestamps

## Architecture Overview

The system is organized as a modular 13-phase pipeline:

```
Phase 1:  Project Setup & Configuration
Phase 2:  Data Acquisition (IEX Cloud + yfinance fallback)
Phase 3:  Data Cleaning (missing values, spikes, validation)
Phase 4:  Data Quality Assurance (aggregated validation)
Phase 5:  Feature Engineering - Tier-1 (returns, normalized prices)
Phase 6:  Feature Engineering - Tier-2 (technical indicators)
Phase 7:  Feature Engineering - Tier-3 (market regimes, cross-asset)
Phase 8:  Signal Processing (Wavelet, SSA, Kalman Filtering)
Phase 9:  Data Splitting (chronological 70/15/15)
Phase 10: Preprocessing & Scaling (fit on train only)
Phase 11: Baseline Model Training (Random Walk, ARIMA, etc.)
Phase 12: Evaluation & Metrics (MAE, RMSE, directional accuracy, IC, Sharpe)
Phase 13: Reporting & Artifact Versioning
```

### Key Design Decisions

#### 1. **Chronological Integrity**
All data splits strictly follow chronological order (no shuffling) to prevent look-ahead bias. Training data is temporally before validation, which is before test data.

#### 2. **Reproducibility-First**
- All random seeds (NumPy, TensorFlow, Python) are fixed in configuration
- All preprocessing artifacts (scalers, Kalman parameters) are versioned and saved
- Configuration hashes enable exact experiment replication
- Full data lineage is tracked from raw input to model predictions

#### 3. **Data Leakage Prevention**
- Preprocessing artifacts (scalers, normalizers) are fit exclusively on training data
- No information from validation or test sets is used during preprocessing
- Rolling windows in feature computation use only historical data (strictly causal)
- Verification step explicitly checks for data leakage

#### 4. **Modular Feature Engineering**
Features are organized in three tiers for ablation studies:
- **Tier-1 (Always):** Simple returns, log returns, normalized prices/volumes
- **Tier-2 (Default):** Technical indicators (RSI, MACD, Bollinger, etc.)
- **Tier-3 (Optional):** Market regimes, cross-asset correlations
- **Signal Processing:** Advanced decompositions (Wavelet, SSA, Kalman)

Each feature module is independently testable and can be removed for ablation analysis.

#### 5. **Multi-Source Data with Fallback**
Primary data source is IEX Cloud (premium quality, consistent formatting). If unavailable, the system automatically falls back to Yahoo Finance. Both sources are validated before use.

#### 6. **Baseline-Centric Evaluation**
Deep learning improvements are always compared against multiple baselines (Random Walk, ARIMA, Linear/Ridge Regression, Historical Mean). This prevents spurious claims of model superiority.

## Folder Structure

```
stock-forecasting-system/
│
├── config/
│   ├── __init__.py
│   └── config_loader.py              # Configuration management (ConfigLoader)
│
├── preprocessing/
│   ├── data_acquisition/
│   │   ├── base_adapter.py           # Abstract DataAdapter interface
│   │   ├── iex_adapter.py            # IEX Cloud implementation
│   │   ├── yfinance_adapter.py       # Yahoo Finance implementation
│   │   └── acquisition_coordinator.py # Orchestration with fallback
│   │
│   ├── data_cleaning/
│   │   ├── detectors.py              # Missing value & spike detection
│   │   ├── correctors.py             # Data correction strategies
│   │   ├── validators.py             # OHLC & quality validation
│   │   ├── adjusters.py              # Stock split/dividend adjusters
│   │   └── cleaner.py                # Main cleaning orchestrator
│   │
│   └── reproducibility/
│       └── reproducibility_manager.py # Seed initialization & artifact versioning
│
├── features/
│   ├── tier1/
│   │   ├── returns.py                # Simple & log returns
│   │   └── normalized_prices.py      # Price & volume normalization
│   │
│   ├── tier2/
│   │   ├── technical_indicators.py   # RSI, MACD, Bollinger, etc.
│   │   ├── momentum.py               # Momentum indicators
│   │   ├── volatility.py             # Volatility measures
│   │   └── other_indicators.py       # Additional technical indicators
│   │
│   ├── tier3/
│   │   ├── regime.py                 # Market regime detection
│   │   └── cross_asset.py            # Relative strength, sector correlation
│   │
│   ├── signal_processing/
│   │   ├── wavelet_transform.py      # Wavelet decomposition
│   │   ├── ssa.py                    # Singular Spectrum Analysis
│   │   ├── kalman_filter.py          # Kalman smoothing
│   │   └── base.py                   # Base signal processing class
│   │
│   ├── feature_orchestrator.py        # Coordinates all feature computation
│   ├── feature_validator.py           # Validates features for NaN/leakage
│   └── base_features.py               # Abstract FeatureModule base class
│
├── baselines/
│   ├── base_model.py                 # Abstract BaselineModel interface
│   ├── random_walk.py                # Random Walk baseline
│   ├── arima_model.py                # ARIMA(1,1,1) implementation
│   ├── linear_regression.py          # Linear Regression baseline
│   ├── ridge_regression.py           # Ridge Regression with L2 regularization
│   └── historical_mean.py            # Historical Mean baseline
│
├── evaluation/
│   ├── metrics.py                    # MAE, RMSE, MAPE, Directional Accuracy, IC, Sharpe
│   ├── confidence_intervals.py       # Bootstrap confidence intervals
│   └── test_metrics.py               # Metric unit tests
│
├── optimization/
│   └── ijff_optimizer.py             # IJF-F (advanced metaheuristic) implementation
│
├── ablation/
│   ├── ablation_framework.py         # Ablation study orchestration
│   └── ablation_reporter.py          # Ablation result analysis & reporting
│
├── tests/                             # Comprehensive test suite (450+ tests)
│   ├── test_config.py
│   ├── test_data_acquisition.py
│   ├── test_data_cleaning.py
│   ├── test_features.py
│   ├── test_baselines.py
│   └── ... (more test modules)
│
├── pipeline.py                        # Main entry point (13-phase orchestrator)
├── master_config.json                 # Configuration template (all phases)
├── requirements.txt                   # Pinned package versions (25 packages)
│
├── results/                           # Output directory (created at runtime)
│   ├── cleaning_report.json
│   ├── validation_report.json
│   ├── features_manifest.json
│   ├── splits_metadata.json
│   ├── baseline_results.json
│   ├── pipeline_report.md
│   ├── visualizations/                # High-resolution PNG charts (300 DPI)
│   └── experiment_results/
│
├── logs/                              # Pipeline execution logs
│   └── pipeline_{timestamp}.log
│
├── reproducibility_artifacts/         # Versioned preprocessing artifacts
│   ├── v1_scalers.pkl
│   ├── v1_kalman_params.pkl
│   └── v1_config_hash.json
│
├── README.md                          # This file
├── CONTINUATION_GUIDE.md              # Status & next steps for team
├── TROUBLESHOOTING.md                 # Common issues & solutions
├── EXPERIMENTS.md                     # Guide to running ablations & experiments
└── .gitignore                         # Git configuration
```

## Data Sources & Configuration

### Supported Data Sources

1. **IEX Cloud (Primary)** - Premium quality, consistent formatting
   - ~10+ years of historical OHLCV data per symbol
   - Rate-limited at 100 requests/second
   - Requires API token (free tier available)

2. **Yahoo Finance (Fallback)** - Free, widely available
   - Automatic fallback if IEX Cloud unavailable
   - Covers most US-traded equities
   - No authentication required

### Supported Exchanges

- NYSE (New York Stock Exchange)
- NASDAQ
- AMEX (American Stock Exchange)

### Default Symbols

The system ships with a default portfolio:
- **AAPL** (Apple Inc., Technology)
- **MSFT** (Microsoft, Technology)
- **GOOGL** (Alphabet, Technology)
- **AMZN** (Amazon, Consumer Discretionary)
- **TSLA** (Tesla, Consumer Discretionary)

To modify, edit `master_config.json`:

```json
{
  "symbols": {
    "list": ["AAPL", "MSFT", "SPY", "QQQ"],
    "max_portfolio_size": 100
  }
}
```

## Feature Engineering Details

The system generates features across multiple tiers and decompositions:

### Tier-1 Features (Always Computed)
- Simple returns: `(Close_t - Close_{t-1}) / Close_{t-1}`
- Log returns: `log(Close_t / Close_{t-1})`
- Normalized close: `(Close_t - MA20) / STD20`
- Normalized volume: `(Volume_t) / MA_Vol20`

### Tier-2 Features (Technical Indicators)
- **Momentum:** 5-day, 20-day, 60-day momentum
- **Volatility:** 20-day rolling standard deviation of returns
- **RSI:** Relative Strength Index (14-day)
- **MACD:** Moving Average Convergence Divergence (12,26,9)
- **Bollinger Bands:** Price bands with 2 std deviations
- **Stochastic:** Momentum oscillator
- **ADX:** Average Directional Index (14-day)
- **ATR:** Average True Range (14-day)
- **OBV:** On-Balance Volume
- And more...

### Tier-3 Features (Market Context)
- **Market Regime:** Bullish, bearish, range-bound, high-volatility classification
- **Relative Strength:** Correlation with S&P 500 (60-day rolling)
- **Sector Correlation:** Correlation with sector ETF (60-day rolling)
- **Cross-Asset Signals:** Peer correlation matrix

### Signal Processing Features
- **Wavelet Decomposition:** Multi-scale decomposition (Daubechies db4)
- **Singular Spectrum Analysis:** Trend and seasonal components
- **Kalman Filtering:** Smoothed price estimates and uncertainty quantification

All features are computed with strict causality (no look-ahead bias) and saved in structured CSV/JSON formats.

## Baseline Models

The system includes five baseline models for result contextualization:

1. **Random Walk** - Predicts next return = today's return (null model)
2. **ARIMA(1,1,1)** - Autoregressive Integrated Moving Average
3. **Linear Regression** - Tier-1 features only
4. **Ridge Regression** - All features with L2 regularization (tuned on validation set)
5. **Historical Mean** - Predicts next return = historical average (from training data)

Baseline results are saved in `baseline_results.json` with metrics:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error)
- Directional Accuracy (% correct up/down predictions)
- Information Coefficient (Spearman rank correlation)
- Sharpe Ratio (risk-adjusted returns)

## Output Reports & Artifacts

After pipeline execution, the `results/` directory contains:

### Data Quality Reports
- **`cleaning_report.json`** - Per-symbol cleaning actions, completeness %, excluded symbols
- **`validation_report.json`** - Pass/fail status, summary statistics
- **`data_audit_trail.json`** - Detailed log of all transformations

### Feature Documentation
- **`features_manifest.json`** - Feature definitions, computation methods, tier assignments
- **`cross_asset_manifest.json`** - Cross-asset feature metadata

### Evaluation Results
- **`baseline_results.json`** - Metrics for all baseline models
- **`test_results.json`** - Final performance metrics on test set
- **`ablation_results.json`** - Feature importance via ablation studies

### Configuration & Reproducibility
- **`splits_metadata.json`** - Train/validation/test date ranges and cutoff dates
- **`data_lineage_graph.json`** - Dependency chain from raw data to predictions
- **`reproducibility_checklist.json`** - Verification that seeds, configs, and artifacts are saved

### Reports
- **`pipeline_report.md`** - Human-readable summary (data sources, symbols, metrics, warnings)
- **`model_card.md`** - Model documentation (intended use, limitations, recommendations)

### Visualizations
- **Data Quality Dashboard** (`results/visualizations/data_quality_dashboard.html`)
- **Feature Distribution Report** (`results/visualizations/feature_distribution.html`)
- **Baseline Comparison Charts** (`results/visualizations/baseline_comparison.png`)
- High-resolution PNG exports (300 DPI for publication)

## Configuration Management

All configuration is controlled via `master_config.json`. Key sections:

```json
{
  "pipeline_metadata": {
    "execution_timestamp": "ISO 8601 timestamp",
    "pipeline_version": "1.0",
    "stage": "Stage_1_DataCleaning_FeatureEngineering"
  },
  
  "random_seeds": {
    "numpy_seed": 42,
    "random_seed": 42,
    "tensorflow_seed": 42,
    "documentation": "For reproducibility"
  },
  
  "data_acquisition": {
    "primary_source": "iex_cloud",
    "fallback_source": "yfinance",
    "lookback_years": 10,
    "min_trading_days": 2500
  },
  
  "feature_engineering": {
    "tier1_enabled": true,
    "tier2_enabled": true,
    "tier3_enabled": true,
    "signal_processing_enabled": false
  },
  
  "data_splitting": {
    "methodology": "chronological_70_15_15",
    "train_ratio": 0.70,
    "val_ratio": 0.15,
    "test_ratio": 0.15
  },
  
  "baseline_models": {
    "random_walk": {"enabled": true},
    "arima_111": {"enabled": true},
    "linear_regression": {"enabled": true},
    "ridge_regression": {"enabled": true},
    "historical_mean": {"enabled": true}
  }
}
```

## Reproducibility & Scientific Rigor

The system is designed with reproducibility at its core:

1. **Fixed Random Seeds** - All sources (NumPy, Python random, TensorFlow) seeded before any stochastic operations
2. **Configuration Hashing** - Experiment IDs linked to configuration hashes for audit trails
3. **Artifact Versioning** - All preprocessing artifacts (scalers, Kalman params) saved with version tags
4. **Data Lineage Tracking** - Full dependency graph saved (raw data → cleaned → features → splits → models)
5. **Leakage Detection** - Explicit verification that validation/test data are not used during preprocessing
6. **Comprehensive Logging** - All operations logged to both console and timestamped files in JSON format

To reproduce an experiment exactly:
1. Save the configuration (`master_config.json`)
2. Save all preprocessing artifacts from `reproducibility_artifacts/`
3. Retrieve the exact same raw data (or use cached CSV files)
4. Re-run with identical configuration

## Testing

The project includes a comprehensive test suite with 450+ tests covering:

- **Data Acquisition:** Adapter implementations, fallback logic, retry mechanisms
- **Data Cleaning:** Spike detection, missing value handling, validation rules
- **Feature Engineering:** Tier-1/2/3 feature calculations, signal processing decompositions
- **Baseline Models:** ARIMA fitting, scaling, prediction correctness
- **Evaluation Metrics:** MAE/RMSE/IC/Sharpe calculations
- **Data Splitting:** Chronological integrity, no leakage

Run tests:

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_features.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Troubleshooting

### Common Issues

**Issue: `IEX_CLOUD_TOKEN not found`**
- Set environment variable: `export IEX_CLOUD_TOKEN="your_token"`
- Verify: `echo $IEX_CLOUD_TOKEN`

**Issue: `No module named 'pandas'`**
- Reinstall dependencies: `pip install -r requirements.txt`
- Activate virtual environment: `source .venv/bin/activate`

**Issue: `Insufficient data for symbol XXXX`**
- Check TROUBLESHOOTING.md for symbol-specific data availability issues
- Try alternative symbols or extend lookback period in config

**Issue: `Data leakage detected during verification`**
- Check that preprocessing artifacts were fit on training data only
- Verify splits_metadata.json shows correct date ranges
- See TROUBLESHOOTING.md for detailed diagnostics

For more troubleshooting guidance, refer to **TROUBLESHOOTING.md**.

## Next Steps & Development

### Current Status
- **Phase 1-4:** Completed (Setup, data acquisition, cleaning, QA)
- **Phase 5-8:** In progress (Feature engineering & signal processing)
- **Phase 9-13:** Planned (Splitting, baselines, evaluation, reporting)

### For Continuing Development
Refer to **CONTINUATION_GUIDE.md** for:
- Current implementation status
- Completed vs. in-progress tasks
- Next priority items
- Architecture decisions & rationale

### For Running Experiments
Refer to **EXPERIMENTS.md** for:
- How to run ablation studies
- Comparing feature contributions
- Interpreting results
- Publishing-ready output formats

## Citation & References

This system implements research-grade techniques from:
- Wavelet decomposition for multi-scale analysis
- Singular Spectrum Analysis for trend/seasonal separation
- Kalman Filtering for state-space smoothing
- Advanced feature engineering for market microstructure
- Attention mechanisms for interpretable deep learning
- IJF-F optimization for hyperparameter tuning

Full references available in the design documentation.

## License

[To be specified by project]

## Support & Contact

For questions or issues:
1. Check **TROUBLESHOOTING.md** for common problems
2. Review **EXPERIMENTS.md** for usage examples
3. Consult **CONTINUATION_GUIDE.md** for architecture details
4. Review docstrings in Python modules (NumPy/Google style)

---

**Last Updated:** 2024-01-19  
**Status:** Stage 1 - Data Cleaning & Feature Engineering (450+ tests passing)
