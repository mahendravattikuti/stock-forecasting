# Data Guide - Stock Market Forecasting System

A comprehensive technical guide to data acquisition, cleaning, validation, and feature engineering in the Stock Market Forecasting System.

**Audience:** Data engineers, ML practitioners, and research scientists who need to understand or extend the data pipeline.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Sources](#data-sources)
3. [Data Acquisition Process](#data-acquisition-process)
4. [Data Cleaning Procedures](#data-cleaning-procedures)
5. [Data Quality Validation](#data-quality-validation)
6. [Feature Engineering](#feature-engineering)
7. [Output Data Formats](#output-data-formats)
8. [Adding New Data Sources](#adding-new-data-sources)
9. [Data Quality Expectations](#data-quality-expectations)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting Data Issues](#troubleshooting-data-issues)

---

## Overview

The Stock Market Forecasting System acquires daily OHLCV (Open, High, Low, Close, Volume) data, applies rigorous cleaning procedures, engineers features across three tiers, and produces validated datasets for model training.

### Data Pipeline Architecture

```
Raw Data Sources
    ↓
(IEX Cloud API | Yahoo Finance API)
    ↓
Data Acquisition Layer
    ↓ (with fallback strategy)
Raw OHLCV CSVs
    ↓
Data Cleaning Layer
    ↓ (missing values, spikes, OHLC validation, splits/dividends)
Cleaned OHLCV CSVs + Cleaning Reports
    ↓
Data Quality Validation
    ↓ (completeness, statistical checks, exclusion)
Quality-Assured Symbol Set
    ↓
Feature Engineering Layer
    ↓ (Tier-1, Tier-2, Tier-3, signal processing)
Engineered Features + Feature Manifests
    ↓
Chronological Data Splitting
    ↓ (70% train / 15% validation / 15% test)
Train/Validation/Test Splits
    ↓
Preprocessing & Artifact Management
    ↓ (scaling on training only)
Model-Ready Data + Preprocessing Artifacts
```

### Data Quality Assurance Gates

The pipeline includes multiple quality checkpoints:

1. **Acquisition Gate:** Minimum 2,500 trading days per symbol
2. **Cleaning Gate:** No persistent gaps, acceptable spike/correction rates
3. **Quality Gate:** ≥2,500 trading days, ≥95% completeness, valid OHLC relationships
4. **Feature Gate:** No NaN/infinite values (except expected lags), no look-ahead bias
5. **Split Gate:** Temporal integrity (train_end < val_start < test_start)
6. **Leakage Gate:** Scaler fit on training data only, artifacts versioned

---

## Data Sources

### 1. Primary Source: IEX Cloud

**Overview:**
IEX Cloud is a premium financial data provider offering high-quality, consistently formatted market data.

**Endpoint:**
```
https://api.iexcloud.io/stable/stock/{symbol}/chart/max
```

**Authentication:**
```bash
export IEX_CLOUD_TOKEN="your_api_token_here"
```

**Data Coverage:**
- Daily OHLCV data for US-traded equities
- 5+ years minimum (10+ years typical)
- Covers NYSE, NASDAQ, AMEX
- Adjustment factors pre-applied (splits, dividends)

**Rate Limiting:**
- 100 requests/second (sandbox tier)
- Exponential backoff implemented (1s, 2s, 4s)
- Max 3 retry attempts

**Advantages:**
- Consistent formatting across symbols
- Pre-adjusted for splits/dividends
- High data quality and completeness
- Reliable uptime

**Configuration in `master_config.json`:**
```json
{
  "data_acquisition": {
    "primary_source": "iex_cloud",
    "iex_api_token": "${IEX_CLOUD_TOKEN}",
    "retry_attempts": 3,
    "retry_backoff_factor": 2,
    "timeout_seconds": 30
  }
}
```

**Obtaining an API Token:**
1. Register at https://iexcloud.io (free tier available)
2. Navigate to Console → Tokens
3. Copy your token
4. Set environment: `export IEX_CLOUD_TOKEN="your_token"`

**Cost:**
- Free tier: Limited API calls (sufficient for development)
- Paid tier: Unlimited calls (recommended for production)

---

### 2. Fallback Source: Yahoo Finance (yfinance)

**Overview:**
Yahoo Finance is a freely available fallback when IEX Cloud is unavailable.

**Implementation:**
- Uses `yfinance` Python library
- Wraps Yahoo Finance API
- No authentication required

**Data Coverage:**
- Daily OHLCV for most US-traded equities
- Typically 5+ years available
- Coverage varies by symbol

**Advantages:**
- Free and no authentication required
- Automatic fallback when IEX Cloud fails
- Wide symbol coverage
- Useful for development without API token

**Limitations:**
- Occasional data quality issues
- Slower than IEX Cloud
- Less consistent formatting
- Rate limiting unclear (conservative approach recommended)

**Configuration in `master_config.json`:**
```json
{
  "data_acquisition": {
    "fallback_source": "yfinance"
  }
}
```

**Installation:**
```bash
pip install yfinance
```

**Usage Example:**
```python
import yfinance as yf

# Download data for symbol
data = yf.download('AAPL', start='2014-01-01', end='2024-01-19')
print(data.head())
# Columns: Open, High, Low, Close, Volume, Adj Close
```

---

### 3. Supported Exchanges

The system validates that all symbols trade on supported exchanges:

- **NYSE** (New York Stock Exchange)
- **NASDAQ** (National Association of Securities Dealers Automated Quotations)
- **AMEX** (American Stock Exchange / NYSE American)

Exchange validation uses the symbol registry (`symbols_registry.csv`):

```csv
Symbol,CompanyName,Sector,Exchange,FirstTradeDate,LastTradeDate,Status
AAPL,Apple Inc.,Technology,NASDAQ,1997-11-28,2024-01-19,ACTIVE
MSFT,Microsoft Corporation,Technology,NASDAQ,1986-03-13,2024-01-19,ACTIVE
JPM,JPMorgan Chase & Co.,Financials,NYSE,1968-05-14,2024-01-19,ACTIVE
```

---

### 4. Data Minimum Requirements

**Per-Symbol Requirements:**
- ≥2,500 trading days of continuous data
- Covers approximately 10+ years of daily trading (US market has ~252 trading days/year)
- Must have valid OHLCV data (non-null, non-zero, positive prices/volume)
- No persistent gaps (max 2 consecutive missing days that can be forward-filled)

**System-Level Requirements:**
- At least 1 symbol with valid data (recommended: 5+)
- Symbols should span multiple sectors for diversification
- Include major benchmarks (e.g., SPY for market regime)

---

## Data Acquisition Process

### 1. Acquisition Workflow

**Step 1: Symbol Validation**
```python
# Check symbol exists in registry and is active
registry = SymbolRegistry(config)
symbol = registry.validate_symbol('AAPL')
# Returns: Symbol object with metadata
# Raises: ValueError if symbol invalid or inactive
```

**Step 2: Primary Source Attempt (IEX Cloud)**
```python
# Initialize adapter with API token
iex_adapter = IEXAdapter(api_token=config['iex_api_token'])

# Fetch data with automatic retry
df = iex_adapter.fetch(
    symbol='AAPL',
    start_date='2014-01-01',
    end_date='2024-01-19'
)
# Returns: DataFrame with [Date, Open, High, Low, Close, Volume]
# Raises: NetworkError after 3 retry attempts
```

**Step 3: Fallback Attempt (Yahoo Finance)**
```python
# If IEX fails, try yfinance
if iex_failed:
    yfinance_adapter = YFinanceAdapter()
    df = yfinance_adapter.fetch(
        symbol='AAPL',
        start_date='2014-01-01',
        end_date='2024-01-19'
    )
```

**Step 4: Data Validation**
```python
# Validate response format and content
is_valid = adapter.validate_response(df)
# Checks:
# - Required columns present: [Date, Open, High, Low, Close, Volume]
# - No completely null columns
# - Data types correct (dates, floats)
# - At least 1 row of data
# Returns: bool (True if valid, False otherwise)
```

**Step 5: Minimum Data Check**
```python
# Verify symbol has sufficient history
trading_days = len(df)
if trading_days < config['min_trading_days']:  # 2500
    raise InsufficientDataError(
        f"{symbol}: {trading_days} days, need {config['min_trading_days']}"
    )
```

### 2. Acquisition Coordinator with Fallback

The `AcquisitionCoordinator` class orchestrates the entire process:

```python
from preprocessing.data_acquisition import AcquisitionCoordinator

# Initialize
coordinator = AcquisitionCoordinator(
    primary_adapter=iex_adapter,
    fallback_adapter=yfinance_adapter,
    config=config
)

# Fetch data with automatic fallback
try:
    df = coordinator.fetch_with_fallback(
        symbol='AAPL',
        start_date='2014-01-01',
        end_date='2024-01-19'
    )
except Exception as e:
    print(f"All sources failed: {e}")
    # Symbol will be excluded from further processing
```

**Fallback Triggering:**

| Condition | Action |
|-----------|--------|
| Primary success | Use primary data, skip fallback |
| Primary network error | Retry with backoff, then try fallback |
| Primary invalid token | Use fallback immediately |
| Primary timeout | After 3 retries, use fallback |
| Primary insufficient data | Use fallback to get more data |
| Both sources fail | Exclude symbol, log reason |

### 3. Error Handling

**Exponential Backoff Strategy:**
```
Attempt 1: wait 1 second
Attempt 2: wait 2 seconds
Attempt 3: wait 4 seconds
All failed: switch to fallback or exclude
```

**Logging:**
```
2024-01-19 10:30:45 INFO  Acquiring data for AAPL from IEX Cloud
2024-01-19 10:30:46 DEBUG  Request: symbol=AAPL, range=max, timeout=30s
2024-01-19 10:30:47 INFO  Received 2523 trading days (2002-01-02 to 2024-01-19)
2024-01-19 10:30:47 DEBUG  Data validation: OHLCV complete, no NaN values
2024-01-19 10:30:47 INFO  AAPL acquisition complete: success
```

### 4. Configuration

**Key Configuration Parameters:**

```json
{
  "data_acquisition": {
    "primary_source": "iex_cloud",
    "fallback_source": "yfinance",
    "iex_api_token": "${IEX_CLOUD_TOKEN}",
    "lookback_years": 10,
    "min_trading_days": 2500,
    "retry_attempts": 3,
    "retry_backoff_factor": 2,
    "timeout_seconds": 30
  }
}
```

**Configuration Details:**
- `lookback_years`: Years to fetch (default: 10)
- `min_trading_days`: Minimum acceptable history (default: 2500)
- `retry_attempts`: Max retries per source (default: 3)
- `retry_backoff_factor`: Exponential backoff multiplier (default: 2)
- `timeout_seconds`: Request timeout in seconds (default: 30)

---

## Data Cleaning Procedures

Data cleaning transforms raw OHLCV into validated, consistent time series ready for analysis.

### 1. Missing Value Detection and Handling

**Detection:**
```python
# Identify missing values
detector = MissingValueDetector(config)

# Find NaN, null, zero, or negative values
missing = detector.detect_anomalies(df)
# Returns: List of (date, field, anomaly_type)
# Examples:
# - (2020-03-16, Close, NaN)
# - (2015-02-12, Volume, 0)
# - (1999-04-01, High, -5.50)

# Find consecutive missing trading days
gaps = detector.detect_gaps(df)
# Returns: List of DateRange objects
# Example: DateRange(start=2020-03-16, end=2020-03-17, consecutive_days=2)
```

**Gap Classification:**
```
Gap Type             | Consecutive Days | Action
--------------------|------------------|------------------
Micro-gap            | 1-2 days         | Forward-fill
Regular gap          | 3-5 days         | Mark unfillable
Extended gap         | 5+ days          | Exclude date range
Weekend/holiday      | 1-3 days (expected) | Forward-fill
Market closure       | Several days     | Check legitimacy
Data quality issue   | Variable         | Flag for review
```

**Forward-Fill Strategy:**

For OHLC prices (up to 2 consecutive days):
```python
# Forward-fill OHLC with previous day's values
for col in ['Open', 'High', 'Low', 'Close']:
    df[col] = df[col].fillna(method='ffill', limit=2)
    # Fills forward-fill up to 2 days

# Volume: fill with median or forward-fill
df['Volume'] = df['Volume'].fillna(
    method='ffill', limit=2  # or use rolling median
)
```

**Beyond 2 Days:**
```python
# Mark as unfillable and exclude
if gap > 2:
    unfillable_ranges.append((start_date, end_date))
    # Exclude this date range from further processing
    df = df[(df.index < start_date) | (df.index >= end_date)]
```

**Logging:**
```json
{
  "forward_fills": {
    "count": 2,
    "fills": [
      {
        "date_range": ["2020-03-16", "2020-03-17"],
        "field": "Close",
        "reason": "consecutive_missing_values",
        "action": "forward_fill"
      }
    ]
  },
  "unfillable_gaps": {
    "count": 1,
    "gaps": [
      {
        "start_date": "2001-09-11",
        "end_date": "2001-09-13",
        "consecutive_days": 3,
        "reason": "market_closure",
        "action": "exclude_date_range"
      }
    ]
  }
}
```

---

### 2. Spike Detection and Removal

**Detection Algorithm:**
```python
detector = SpikeDetector(config)

# Calculate daily returns
returns = (df['Close'] / df['Close'].shift(1)) - 1

# Identify spikes (±20% threshold by default)
spikes = detector.detect_spikes(df, threshold=0.20)
# Returns: List of Spike objects
# Example:
# Spike(date=2014-04-23, return=0.245, severity=HIGH, confidence=LOW)
```

**Verification Process:**

For each spike, attempt verification from multiple sources:
```python
spike_date = '2014-04-23'
spike_return = 0.245  # 24.5%

# Check across available sources
sources_confirming = 0
for adapter in [iex_adapter, yfinance_adapter]:
    try:
        external_data = adapter.fetch(symbol, spike_date, spike_date)
        external_return = calculate_return(external_data)
        if abs(external_return - spike_return) < 0.01:  # Match within 1%
            sources_confirming += 1
    except:
        pass

# Decision
if sources_confirming >= 3:
    # Spike is legitimate (real market event)
    action = "ACCEPT"
else:
    # Spike is suspicious (potential data error)
    action = "REMOVE_OR_INTERPOLATE"
```

**Removal Strategy: Linear Interpolation**

```python
# Replace spike with interpolated value
# Using neighboring non-spike prices
before = df.loc[df.index[idx-1], 'Close']
after = df.loc[df.index[idx+1], 'Close']
interpolated = (before + after) / 2

df.loc[df.index[idx], 'Close'] = interpolated
# Also adjust High/Low to maintain OHLC relationships
```

**Spike Logging:**
```json
{
  "spike_removals": {
    "count": 1,
    "spikes": [
      {
        "date": "2014-04-23",
        "daily_return": 0.245,
        "threshold": 0.20,
        "sources_confirming": 1,
        "min_sources_required": 3,
        "confidence": "low",
        "action": "linear_interpolation",
        "interpolated_price": 105.25,
        "reason": "insufficient_confirmation"
      }
    ]
  }
}
```

---

### 3. OHLC Relationship Validation and Correction

**Validation Rules:**

For each bar, must satisfy:
```
High >= Close >= Low >= Open
```

**Detection:**
```python
validator = OHLCValidator(config)

# Check relationships
violations = validator.validate_relationships(df)
# Returns: List of Violation objects

# Examples of violations:
# - Close (104.50) > High (103.00)
# - Low (97.00) > Open (96.50)
# - Open (100.00) > Close (99.50) but High (98.00) (inconsistent)
```

**Correction Strategies:**

**Option 1: Linear Interpolation**
```python
if violation == 'Close > High':
    # Adjust high upward to >= close
    df.loc[idx, 'High'] = max(df.loc[idx, 'High'], df.loc[idx, 'Close'])

if violation == 'Low < Close' (impossible):
    # This means Low is somehow below Close (shouldn't happen with correct order)
    # Recompute low from neighborhood
    neighbor_low = min(
        df.loc[idx-1:idx+1, 'Low'].values
    )
    df.loc[idx, 'Low'] = neighbor_low
```

**Option 2: Exclusion**
```python
if correction_method == 'exclude':
    df = df.drop(idx)
    # Remove bar entirely if correction not possible
```

**Validation and Logging:**
```json
{
  "ohlc_corrections": {
    "count": 3,
    "violations": [
      {
        "date": "2008-10-24",
        "violation_type": "Close > High",
        "values_before": {
          "Open": 100.25,
          "High": 105.00,
          "Low": 99.50,
          "Close": 105.50
        },
        "values_after": {
          "Open": 100.25,
          "High": 105.50,
          "Low": 99.50,
          "Close": 105.50
        },
        "action": "correction",
        "method": "linear_interpolation"
      }
    ]
  }
}
```

---

### 4. Stock Split and Dividend Adjustment

**Purpose:**
Historical prices must be adjusted for corporate actions (splits, dividends) so returns are calculated correctly.

**Detection:**
```python
adjuster = SplitDividendAdjuster(config)

# Query adjustment factors from data source
adjustments = adjuster.detect_adjustments(symbol)
# Returns: List of Adjustment objects
# Example:
# Adjustment(date=2014-06-09, type='split', factor=7.0, description='7:1 stock split')
# Adjustment(date=2024-01-16, type='dividend', factor=1.0024, description='$0.24 dividend')
```

**Adjustment Application:**

```python
# Apply adjustment factor to all historical prices
adjustment_date = '2014-06-09'
adjustment_factor = 7.0  # 7:1 split

# Adjust prices BEFORE split date
mask = df.index < adjustment_date
df.loc[mask, ['Open', 'High', 'Low', 'Close']] /= adjustment_factor
# df.loc[mask, 'Volume'] *= adjustment_factor  # Volume increases

# After: prices reduced by factor, volume increased
# This maintains correct return calculations
```

**Adjustment Logging:**
```json
{
  "split_adjustments": {
    "count": 1,
    "adjustments": [
      {
        "date": "2014-06-09",
        "type": "stock split",
        "description": "7:1 stock split",
        "factor": 7.0,
        "prices_adjusted": true,
        "volume_adjusted": true,
        "rows_affected": 2523,
        "note": "All prices before split date divided by 7"
      }
    ]
  }
}
```

---

### 5. Volume Validation and Handling

**Validation Rules:**
- Volume > 0 for all trading days
- No negative volume
- Volume consistency (no unexplained extreme jumps)

**Handling:**
```python
# Check for zero or negative volume
zero_volume_dates = df[df['Volume'] <= 0].index

if len(zero_volume_dates) > 0:
    for date in zero_volume_dates:
        # Option 1: Forward-fill from previous valid volume
        prev_valid = df.loc[:date, 'Volume'][df.loc[:date, 'Volume'] > 0].iloc[-1]
        df.loc[date, 'Volume'] = prev_valid
        
        # Option 2: Use median of surrounding 10 trading days
        # window = df.loc[date-5:date+5, 'Volume']
        # df.loc[date, 'Volume'] = window.median()
```

---

### 6. Complete Cleaning Pipeline

```python
from preprocessing.data_cleaning import DataCleaner

# Initialize cleaner
cleaner = DataCleaner(config)

# Clean single symbol
cleaned_df, cleaning_report = cleaner.clean_symbol('AAPL', raw_df)

# Result: (cleaned_df, CleaningReport object)
# cleaned_df: DataFrame with all corrections applied
# cleaning_report: Detailed JSON report of all actions
```

**Cleaning Report Output** (`cleaning_report.json`):

```json
{
  "symbol": "AAPL",
  "report_timestamp": "2024-01-19T10:30:00Z",
  "raw_data_stats": {
    "total_rows": 2525,
    "date_range": ["2002-01-02", "2024-01-19"],
    "missing_values": 5,
    "zero_volumes": 0,
    "ohlc_violations": 2
  },
  "cleaning_actions": {
    "forward_fills": {
      "count": 2,
      "date_ranges": [
        {
          "start": "2020-03-16",
          "end": "2020-03-17",
          "reason": "holiday_closure"
        }
      ]
    },
    "spike_removals": {
      "count": 1,
      "spikes": [...]
    },
    "ohlc_corrections": {
      "count": 3,
      "violations": [...]
    },
    "split_adjustments": {
      "count": 1,
      "adjustments": [...]
    }
  },
  "cleaned_data_stats": {
    "total_rows_retained": 2520,
    "date_range": ["2002-01-02", "2024-01-19"],
    "missing_values": 0,
    "rows_excluded": 5,
    "completeness_percent": 99.8
  },
  "validation_checks": {
    "ohlc_relationships": {
      "pass": true,
      "violations_found": 0,
      "percent_valid": 100.0
    },
    "volume_positive": {
      "pass": true,
      "zero_volume_count": 0
    },
    "min_trading_days": {
      "pass": true,
      "days_count": 2520,
      "required": 2500
    },
    "price_statistics": {
      "close_min": 0.01,
      "close_max": 199.62,
      "close_mean": 47.28,
      "close_std": 52.13,
      "volume_mean": 45234567,
      "volume_std": 12345678
    }
  },
  "quality_assessment": "PASS",
  "notes": "AAPL data quality excellent; minimal cleaning required"
}
```

---

## Data Quality Validation

### 1. Quality Validation Criteria

**Criterion 1: Minimum Trading Days**
```
Requirement: ≥2,500 trading days (~10+ years)
Check: len(cleaned_df) >= 2500
Action if failed: Exclude symbol with reason 'insufficient_data'
```

**Criterion 2: Completeness**
```
Requirement: ≥95% of trading days have valid data
Check: (total_rows - missing_rows) / total_rows >= 0.95
Action if failed: Exclude symbol with reason 'incomplete_data'
```

**Criterion 3: OHLC Relationships**
```
Requirement: High >= Close >= Low >= Open for ≥99% of bars
Check: violations / total_rows < 0.01
Action if failed: Exclude symbol with reason 'ohlc_violations'
```

**Criterion 4: Price Statistics**
```
Requirement: Valid min/max/mean/std (no NaN, inf, or invalid ranges)
Check: All statistics are finite and reasonable
Action if failed: Exclude symbol with reason 'invalid_statistics'
```

**Criterion 5: Multi-Day Price Stasis**
```
Requirement: No 5+ consecutive days with identical close price
Check: max(consecutive_unchanged_closes) < 5
Action if failed: Flag for review (potential delisting/halt)
```

### 2. Validation Report

```python
from preprocessing.validators import DataQualityValidator

# Validate all symbols
validator = DataQualityValidator(config)

validation_results = validator.validate_all_symbols(cleaned_symbols)
# Returns: dict of {symbol: validation_result}

# Example result:
# {
#   'AAPL': {'pass': True, 'reasons': []},
#   'BADSTOCK': {'pass': False, 'reasons': ['insufficient_data', 'ohlc_violations']}
# }
```

**Validation Report Output** (`validation_report.json`):

```json
{
  "validation_timestamp": "2024-01-19T11:00:00Z",
  "total_symbols_validated": 500,
  "symbols_passed": 495,
  "symbols_excluded": 5,
  "excluded_reasons": {
    "insufficient_data": 2,
    "ohlc_violations": 1,
    "invalid_statistics": 1,
    "multi_day_stasis": 1
  },
  "passing_symbols": ["AAPL", "MSFT", "GOOGL", ...],
  "excluded_symbols": [
    {
      "symbol": "BADSTOCK",
      "reason": "insufficient_data",
      "trading_days": 1800,
      "required": 2500
    }
  ],
  "overall_assessment": "PASS",
  "statistics": {
    "completeness_avg": 99.2,
    "completeness_min": 97.1,
    "ohlc_validity_avg": 99.8,
    "ohlc_validity_min": 98.5
  }
}
```

### 3. Symbol Exclusion Management

```python
from preprocessing.validators import SymbolExclusionManager

# Track exclusions
exclusion_mgr = SymbolExclusionManager(config)

# Add exclusion
exclusion_mgr.exclude_symbol(
    symbol='BADSTOCK',
    reason='insufficient_data',
    details={'trading_days': 1800, 'required': 2500}
)

# Get excluded symbols
excluded = exclusion_mgr.get_excluded_symbols()
# Returns: List of excluded symbol objects

# Generate exclusion summary
summary = exclusion_mgr.generate_exclusion_summary()
# Output: exclusion_summary.json
```

---

## Feature Engineering

### 1. Feature Organization

Features are organized in **four tiers** based on priority and complexity:

**Tier-1 Features (ALWAYS COMPUTED):**
- Basic returns and normalized prices
- Required for all downstream features
- Examples: simple_return, log_return, normalized_close, normalized_volume

**Tier-2 Features (ENABLED BY DEFAULT):**
- Technical indicators
- Medium complexity, well-established
- Examples: RSI, MACD, Bollinger Bands, Momentum, Volatility

**Tier-3 Features (OPTIONAL, FOR ABLATION):**
- Market regime and cross-asset context
- Advanced, higher computational cost
- Examples: market_regime, relative_strength_vs_spy, sector_correlation

**Signal Processing Features (OPTIONAL, AFTER ADVANCED IMPLEMENTATIONS):**
- Wavelet decomposition, SSA, Kalman Filtering
- Very advanced signal processing
- Examples: wavelet_energy_coef1, ssa_trend, kalman_smoothed_price

### 2. Tier-1 Features: Returns and Normalized Prices

```python
from features.tier1 import ReturnsFeature, NormalizedPricesFeature

# Simple and log returns
returns_feature = ReturnsFeature()
features = returns_feature.compute(df)
# Output: DataFrame with columns [simple_return, log_return]

# Normalized prices and volume
normalized_feature = NormalizedPricesFeature()
features = normalized_feature.compute(df)
# Output: DataFrame with columns [norm_close_20, norm_volume_20]
```

**Tier-1 Formulas:**

| Feature | Formula | Lookback | Output |
|---------|---------|----------|--------|
| Simple Return | (Close_t - Close_{t-1}) / Close_{t-1} | 1 day | simple_return |
| Log Return | log(Close_t / Close_{t-1}) | 1 day | log_return |
| Norm Close | (Close_t - MA20) / STD20 | 20 days | norm_close_20 |
| Norm Volume | Volume_t / MA_Vol20 | 20 days | norm_volume_20 |

**Example Computation:**
```python
# Simple return for day t
close_t = 150.00
close_t_minus_1 = 147.50
simple_return_t = (150.00 - 147.50) / 147.50 = 0.0169  # 1.69%

# Log return for day t
log_return_t = log(150.00 / 147.50) = 0.0168  # 1.68%

# Normalized close (with 20-day MA and STD)
# MA20 = 148.50, STD20 = 2.50
norm_close_t = (150.00 - 148.50) / 2.50 = 0.60
```

---

### 3. Tier-2 Features: Technical Indicators

```python
from features.tier2 import (
    RSIFeature, MACDFeature, BollingerBandsFeature,
    StochasticFeature, ATRFeature, ADXFeature,
    OBVFeature, MomentumFeature, VolatilityFeature
)

# RSI(14)
rsi_feature = RSIFeature(period=14)
features = rsi_feature.compute(df)
# Output: DataFrame with column [rsi_14]

# MACD(12,26,9)
macd_feature = MACDFeature(fast=12, slow=26, signal=9)
features = macd_feature.compute(df)
# Output: DataFrame with columns [macd_line, macd_signal, macd_histogram]
```

**Tier-2 Indicators:**

| Indicator | Lookback | Formula | Output |
|-----------|----------|---------|--------|
| **RSI(14)** | 14 days | 100 - (100/(1+RS)), RS=AvgGain/AvgLoss | rsi_14 |
| **MACD** | 35 days | EMA12 - EMA26, with signal line | macd_line, macd_signal, macd_histogram |
| **Bollinger(20,2)** | 20 days | SMA ± 2×STD | bb_upper, bb_middle, bb_lower, bb_width |
| **Stochastic(14)** | 14 days | 100 × (Close - Low14) / (High14 - Low14) | stoch_k, stoch_d |
| **ATR(14)** | 14 days | SMA of True Range | atr_14 |
| **ADX(14)** | 14 days | +DI vs -DI directional index | adx_14 |
| **OBV** | Cumulative | Volume added/subtracted based on close direction | obv, obv_ma20 |
| **Momentum** | 5, 20, 60 | Close_t / Close_{t-period} - 1 | momentum_5, momentum_20, momentum_60 |
| **Volatility** | 20 days | Rolling STD of returns | volatility_20 |

---

### 4. Tier-3 Features: Market Context

```python
from features.tier3 import (
    MarketRegimeFeature, RelativeStrengthFeature
)

# Market regime classification
regime_feature = MarketRegimeFeature(lookback=60)
features = regime_feature.compute(df)
# Output: DataFrame with column [regime] (values: 0, 1, 2, 3)

# Relative strength vs S&P 500
relative_strength = RelativeStrengthFeature(lookback=60)
features = relative_strength.compute(df, market_data=spy_data)
# Output: DataFrame with column [relative_strength_60]
```

**Market Regime Encoding:**
```
0 = Bearish (negative trend, low volatility)
1 = Sideways (low trend, low volatility)
2 = Bullish (positive trend, low volatility)
3 = High-Volatility (any trend, high volatility)
```

---

### 5. Signal Processing Features (Optional)

```python
from features.signal_processing import (
    WaveletTransformFeature, SSAFeature, KalmanFilterFeature
)

# Wavelet decomposition
wavelet_feature = WaveletTransformFeature(wavelet='db4', levels=3)
features = wavelet_feature.compute(df)
# Output: DataFrame with columns [wavelet_ca_energy, wavelet_cd1_energy, ...]

# Singular Spectrum Analysis
ssa_feature = SSAFeature(embedding_dim=60)
features = ssa_feature.compute(df)
# Output: DataFrame with columns [ssa_trend, ssa_seasonal, ssa_residual]

# Kalman Filtering (fit on training data only!)
kalman_feature = KalmanFilterFeature()
train_fitted = kalman_feature.compute(df_train, fit_data=df_train)
test_fitted = kalman_feature.compute(df_test)  # Don't refit
# Output: DataFrame with columns [kalman_smoothed_price, kalman_uncertainty]
```

---

### 6. Feature Orchestration

```python
from features import FeatureOrchestrator

# Initialize orchestrator
orchestrator = FeatureOrchestrator(
    config={
        'tier1_enabled': True,
        'tier2_enabled': True,
        'tier3_enabled': False,
        'signal_processing_enabled': False
    }
)

# Compute all features for symbol
features_df, manifest = orchestrator.compute_all_features(
    symbol='AAPL',
    ohlcv_df=cleaned_data,
    market_context_df=market_data  # Optional, for Tier-3
)

# Result:
# features_df: DataFrame with all computed features, aligned by date
# manifest: Feature manifest documenting all computations
```

---

### 7. Feature Causality and Look-Ahead Bias Prevention

**Critical Principle:** All features must use only historical data (strictly causal).

**Examples of CORRECT (no look-ahead):**
```python
# ✓ Correct: Use only past data
sma_20 = df['Close'].shift(1).rolling(20).mean()  # Uses days t-20 to t-1

# ✓ Correct: Calculate return between past days
returns = df['Close'].shift(1) / df['Close'].shift(2) - 1  # t-1 vs t-2

# ✓ Correct: Wavelet on historical data
from pywt import wavedec
wavelet_coef = wavedec(df['Close'].iloc[:t], 'db4')  # Only up to day t
```

**Examples of INCORRECT (has look-ahead):**
```python
# ✗ Wrong: Uses current and future data
sma_20 = df['Close'].rolling(20).mean()  # WRONG: Includes current and future prices

# ✗ Wrong: Uses future day's price
returns = df['Close'] / df['Close'].shift(-1) - 1  # WRONG: Uses tomorrow's price

# ✗ Wrong: Calculates rolling metric including future
volatility = df['Close'].rolling(20).std()  # WRONG: Includes future returns
```

**Causality Validation:**
```python
# Feature validator checks for look-ahead bias
validator = FeatureValidator()
is_valid, errors = validator.validate_features(features_df, config)

if not is_valid:
    print(f"Causality violations detected: {errors}")
    # Example error: "volatility_20 uses future data (rolling window includes t+1 to t+20)"
```

---

### 8. Feature Manifest Output

**features_manifest.json:**
```json
{
  "symbol": "AAPL",
  "manifest_timestamp": "2024-01-19T10:30:00Z",
  "features": [
    {
      "name": "simple_return",
      "tier": 1,
      "description": "(Close_t - Close_{t-1}) / Close_{t-1}",
      "lookback_period": 1,
      "computation_method": "pct_change",
      "causality_verified": true,
      "expected_nan_count": 1
    },
    {
      "name": "rsi_14",
      "tier": 2,
      "description": "Relative Strength Index with 14-day period",
      "lookback_period": 14,
      "computation_method": "talib.RSI(14)",
      "causality_verified": true,
      "expected_nan_count": 14
    }
  ],
  "data_quality": {
    "total_features": 35,
    "total_columns_in_output": 35,
    "nan_counts": {
      "simple_return": 1,
      "log_return": 1,
      "rsi_14": 14,
      "macd_line": 35
    },
    "infinite_values_found": false,
    "causality_warnings": [],
    "leakage_detected": false
  }
}
```

---

## Output Data Formats

### 1. Cleaned OHLCV CSV

**Location:** `results/cleaned_data/{symbol}.csv`

**Format:**
```csv
Date,Open,High,Low,Close,Volume,AdjClose
2002-01-02,53.25,54.50,53.00,53.50,1234567,14.83
2002-01-03,53.50,54.75,53.50,54.00,1567890,14.99
2002-01-04,54.00,54.25,53.75,54.20,1456789,15.04
...
2024-01-19,195.00,198.50,194.75,197.62,34567890,197.62
```

**Column Definitions:**
- **Date:** Trading date (YYYY-MM-DD)
- **Open:** Opening price
- **High:** Highest price during day
- **Low:** Lowest price during day
- **Close:** Closing price
- **Volume:** Number of shares traded
- **AdjClose:** Adjusted close price (for splits/dividends)

---

### 2. Feature CSV

**Location:** `results/features/{symbol}_features.csv`

**Format:**
```csv
Date,simple_return,log_return,norm_close_20,norm_volume_20,rsi_14,macd_line,bollinger_width,momentum_20
2002-01-02,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN
2002-01-03,0.0094,0.0093,-0.25,0.89,NaN,NaN,NaN,NaN
...
2024-01-19,0.0123,0.0122,0.45,1.12,65.4,2.15,5.23,0.0234
```

**Data Types:**
- Date: string (YYYY-MM-DD)
- All other columns: float64 (may contain NaN)

---

### 3. Cleaning Report

**Location:** `results/cleaning_reports/{symbol}_cleaning_report.json`

Structure described in [Data Cleaning Procedures](#data-cleaning-procedures) section.

---

### 4. Feature Manifest

**Location:** `results/features_manifests/{symbol}_features_manifest.json`

Structure described in [Feature Engineering](#feature-engineering) section.

---

### 5. Splits Metadata

**Location:** `results/splits_metadata/split_metadata.json`

```json
{
  "metadata_timestamp": "2024-01-19T11:00:00Z",
  "split_methodology": "chronological_70_15_15",
  "date_ranges": {
    "train": {"start_date": "2002-01-02", "end_date": "2019-01-31"},
    "validation": {"start_date": "2019-02-01", "end_date": "2021-08-31"},
    "test": {"start_date": "2021-09-01", "end_date": "2024-01-19"}
  },
  "splits": {
    "train_rows": 4388,
    "val_rows": 941,
    "test_rows": 941,
    "total_rows": 6270
  },
  "temporal_integrity_verified": true,
  "overlap_detected": false
}
```

---

### 6. Data Audit Trail

**Location:** `results/data_audit_trail.json`

```json
{
  "audit_timestamp": "2024-01-19T11:00:00Z",
  "total_symbols_processed": 5,
  "symbols_passed": 5,
  "symbols_excluded": 0,
  "aggregate_statistics": {
    "total_rows_before": 12600,
    "total_rows_after": 12575,
    "rows_removed_percent": 0.20,
    "forward_fills_total": 10,
    "spikes_removed": 2,
    "ohlc_corrections": 5,
    "split_adjustments": 0
  },
  "transformation_log": [
    {
      "timestamp": "2024-01-19T10:30:15Z",
      "symbol": "AAPL",
      "transformation": "forward_fill",
      "date_range": ["2020-03-16", "2020-03-17"],
      "reason": "holiday_closure",
      "rows_affected": 2
    }
  ]
}
```

---

## Adding New Data Sources

### 1. Implementing a Custom Data Adapter

**Step 1: Create Adapter Class**

```python
# preprocessing/data_acquisition/custom_adapter.py
from preprocessing.data_acquisition.base_adapter import DataAdapter
import pandas as pd

class CustomAdapter(DataAdapter):
    """Adapter for custom data source (e.g., Alpha Vantage, Finnhub, Polygon.io)"""
    
    def __init__(self, api_token: str, config: dict = None):
        """
        Initialize adapter.
        
        Args:
            api_token: Authentication token for API
            config: Configuration dict with timeout, retry, etc.
        """
        self.api_token = api_token
        self.base_url = "https://api.custom.io/v1"
        self.timeout = config.get('timeout_seconds', 30) if config else 30
        self.retry_count = config.get('retry_attempts', 3) if config else 3
    
    def fetch(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch OHLCV data for symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with columns [Date, Open, High, Low, Close, Volume]
        
        Raises:
            NetworkError: If fetch fails after retries
            DataFormatError: If response format is invalid
        """
        import requests
        from datetime import datetime
        import time
        
        url = f"{self.base_url}/stock/{symbol}/historical"
        params = {
            'from': start_date,
            'to': end_date,
            'token': self.api_token
        }
        
        # Retry logic
        for attempt in range(self.retry_count):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                # Transform to standard format
                df = self._parse_response(data)
                return df
                
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt  # Exponential backoff
                if attempt < self.retry_count - 1:
                    print(f"Attempt {attempt+1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise NetworkError(f"Failed to fetch {symbol} after {self.retry_count} attempts: {e}")
    
    def validate_response(self, df: pd.DataFrame) -> bool:
        """
        Validate that response has correct format.
        
        Args:
            df: DataFrame to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check columns exist
        if not all(col in df.columns for col in required_columns):
            return False
        
        # Check no completely null columns
        if df[required_columns].isna().all().any():
            return False
        
        # Check data types
        df_numeric = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        if not all(df_numeric.dtypes == 'float64'):
            return False
        
        # Check at least 1 row
        if len(df) < 1:
            return False
        
        return True
    
    def _parse_response(self, data: dict) -> pd.DataFrame:
        """Parse API response into standard DataFrame format."""
        # Transform raw API response to DataFrame
        # This is custom depending on API format
        
        records = data['data']  # Adjust based on API structure
        df = pd.DataFrame(records)
        
        # Ensure columns are correct
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Convert date to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        
        return df
```

**Step 2: Register Adapter in Configuration**

```json
{
  "data_acquisition": {
    "primary_source": "custom",
    "fallback_source": "yfinance",
    "custom_api_token": "${CUSTOM_API_TOKEN}",
    "custom_adapter_class": "preprocessing.data_acquisition.custom_adapter.CustomAdapter"
  }
}
```

**Step 3: Update Acquisition Coordinator**

```python
# preprocessing/data_acquisition/acquisition_coordinator.py
from preprocessing.data_acquisition.custom_adapter import CustomAdapter

class AcquisitionCoordinator:
    def __init__(self, config):
        if config['data_acquisition']['primary_source'] == 'custom':
            self.primary = CustomAdapter(
                api_token=config['data_acquisition']['custom_api_token'],
                config=config['data_acquisition']
            )
        # ... other sources
```

**Step 4: Test Adapter**

```python
# Test custom adapter
from preprocessing.data_acquisition.custom_adapter import CustomAdapter

adapter = CustomAdapter(api_token='your_token', config={'timeout_seconds': 30})

# Fetch data
df = adapter.fetch('AAPL', '2014-01-01', '2024-01-19')

# Validate
is_valid = adapter.validate_response(df)
print(f"Valid: {is_valid}, Rows: {len(df)}")
```

### 2. Data Source Comparison

| Feature | IEX Cloud | Yahoo Finance | Custom (Template) |
|---------|-----------|----------------|------------------|
| Cost | Paid (free tier) | Free | Varies |
| Coverage | Extensive (US stocks) | Extensive | Varies |
| Quality | High | Medium | Varies |
| Rate Limit | 100 req/sec | Unclear | Varies |
| Adjustment | Pre-applied | Pre-applied | Varies |
| Setup Difficulty | Low (token) | Very Low | Medium |
| Fallback | yfinance | None | User-defined |

---

## Data Quality Expectations

### 1. Quantitative Thresholds

| Metric | Threshold | Impact |
|--------|-----------|--------|
| Minimum trading days | ≥2,500 (~10 years) | Symbol excluded if below |
| Completeness | ≥95% of trading days | Warning if below |
| OHLC validity | ≥99% of bars correct | Warning if below |
| Volume positive | 100% of bars | Bar excluded if violated |
| Max forward-fill gap | 2 consecutive days | Gap beyond 2 days excluded |
| Price stasis | No 5+ unchanged closes | Flag for review if detected |
| Spike confirmation | ≥3 independent sources | Spike removed if <3 sources agree |

### 2. Expected Distribution

**Close Prices:**
- Roughly log-normal distribution
- Mean and std vary by symbol
- Should not have extreme outliers after spike removal

**Returns:**
- Approximately normal distribution (especially log returns)
- Mean near 0% per day (~0.04% for S&P 500)
- Std dev ~1-2% per day for large-cap stocks

**Volume:**
- Typically right-skewed (occasional high-volume days)
- Should have no zero or negative values after cleaning
- Variation expected around corporate events, earnings, market crises

### 3. Quality Flags

**Green (Acceptable):**
- ≥2,500 trading days
- No persistent gaps
- <1% OHLC violations
- No suspicious multi-day stasis
- <5% rows removed during cleaning

**Yellow (Review Needed):**
- 2,000-2,500 trading days (near threshold)
- 1-5% OHLC violations
- 5-10% rows removed
- Occasional gaps despite forward-filling

**Red (Exclude):**
- <2,000 trading days
- >10% rows removed
- >5% OHLC violations
- Multi-day price stasis detected
- Failed validation checks

---

## Performance Considerations

### 1. Data Acquisition Time

**Typical Performance:**
- Single symbol: ~2 seconds (IEX) or ~1 second (yfinance)
- 100 symbols: ~3-5 minutes (serial) or ~1-2 minutes (parallel)

**Bottlenecks:**
- Network latency to API servers
- Rate limiting (IEX Cloud: 100 req/sec)
- Response parsing and validation

**Optimization:**
- Implement request batching (if API supports)
- Cache raw data locally
- Parallel fetches (asyncio/threading)
- Use fallback source for timeouts

### 2. Data Cleaning Time

**Typical Performance:**
- Single symbol: ~50 ms
- 100 symbols: ~5 seconds

**Bottlenecks:**
- Missing value detection (O(n))
- Spike detection (O(n))
- OHLC validation (O(n))

**Optimization:**
- Vectorize operations (NumPy, pandas)
- Parallel processing by symbol
- Cache cleaned data

### 3. Feature Engineering Time

**Typical Performance (Tier-1 only):**
- Single symbol: ~10 ms
- 100 symbols: ~1 second

**Typical Performance (Tier-1 + Tier-2):**
- Single symbol: ~50 ms
- 100 symbols: ~5 seconds

**With Signal Processing:**
- Add ~100-200 ms per symbol

**Optimization:**
- Use NumPy for vectorized calculations
- Cache rolling window calculations
- Parallel by symbol
- Consider Numba JIT compilation for complex calculations

### 4. Memory Usage

**Typical Memory (per symbol):**
- Raw data: ~200 KB (10 years of daily OHLCV)
- Cleaned data: ~200 KB (same)
- Tier-1 features: ~600 KB (35 columns)
- Tier-1+2 features: ~2 MB (80+ columns)

**For 100 symbols:**
- Tier-1+2 features: ~200 MB
- With artifacts: ~400 MB total

**Optimization:**
- Use dtype optimization (int32 vs int64)
- Stream processing (don't load all symbols at once)
- Delete intermediate DataFrames
- Use generators for large datasets

### 5. Scalability Estimates

| Portfolio Size | Acquisition Time | Cleaning Time | Features Time | Total |
|---|---|---|---|---|
| 10 symbols | 30 s | 0.5 s | 1 s | ~32 s |
| 50 symbols | 2.5 min | 2.5 s | 5 s | ~2.5 min |
| 100 symbols | 5 min | 5 s | 10 s | ~5 min |
| 500 symbols | 25 min | 25 s | 50 s | ~25 min |
| 1000 symbols | 50 min | 50 s | 100 s | ~50 min |

*Estimates assume serial processing; parallel can be 4-8x faster on multi-core systems.*

---

## Troubleshooting Data Issues

### Common Issue 1: "Insufficient Data" Error

**Symptom:** `InsufficientDataError: SYMBOL has 1800 trading days, need 2500`

**Root Causes:**
1. Symbol recently IPO'd
2. Symbol delisted or merged
3. Data source incomplete
4. Date range too narrow

**Solutions:**
1. Extend start date: Edit `lookback_years` in config
2. Lower threshold (not recommended): Set `min_trading_days: 1500`
3. Use different data source (if available)
4. Exclude symbol from analysis

**Command to Check:**
```bash
python -c "import yfinance as yf; d = yf.download('SYMBOL', start='2014-01-01'); print(f'Days: {len(d)}')"
```

---

### Common Issue 2: "Data Quality Too Poor"

**Symptom:** `Symbol SYMBOL excluded: data quality failed multiple checks`

**Root Causes:**
1. Too many gaps (missing data)
2. Too many OHLC violations
3. Invalid price ranges
4. Suspicious patterns (halts, delistings)

**Solutions:**
1. Relax thresholds: Increase `max_forward_fill_days` in config
2. Review cleaning report: `cat results/cleaning_reports/SYMBOL_cleaning_report.json`
3. Check if symbol should be excluded
4. Use alternative data source

**Debug Command:**
```bash
cat results/cleaning_reports/SYMBOL_cleaning_report.json | jq '.cleaned_data_stats, .quality_assessment'
```

---

### Common Issue 3: NaN in Features

**Symptom:** First N rows of features are NaN

**Root Cause (Expected):** Technical indicators have lookback requirements

**Example:**
- RSI needs 14 days → first 14 rows are NaN
- MACD needs 35 days → first 35 rows are NaN
- After row 35, should have valid values

**Verify It's Expected:**
```bash
cat results/features_manifests/SYMBOL_features_manifest.json | jq '.features[] | {name, expected_nan_count}'
```

**If NaN Scattered Randomly:** Debug data cleaning phase

---

### Common Issue 4: Data Leakage Detection

**Symptom:** `Leakage detected: scaler fit on validation data`

**Root Cause:** StandardScaler fit on wrong data split

**Solution:**
```python
# CORRECT: Fit scaler ONLY on training data
scaler = StandardScaler()
scaler.fit(train_data)  # Only train

# Apply to all splits WITHOUT refitting
train_scaled = scaler.transform(train_data)
val_scaled = scaler.transform(val_data)    # Don't fit
test_scaled = scaler.transform(test_data)  # Don't fit

# WRONG: Refitting on validation/test
# scaler.fit(train_data)  # OK
# scaler.fit(val_data)    # BAD - refits on val data
```

---

### Common Issue 5: Inconsistent Results Across Runs

**Symptom:** Different features or splits across runs

**Root Cause:** Random seeds not initialized

**Solution:**
1. Verify seeds in config: `cat master_config.json | jq '.random_seeds'`
2. Initialize seeds at start:
   ```python
   from utils.reproducibility import initialize_seeds
   initialize_seeds(config['random_seeds'])
   ```

---

## Reference

### Key Functions and Classes

**Data Acquisition:**
- `DataAdapter` - Abstract base for data providers
- `IEXAdapter` - IEX Cloud implementation
- `YFinanceAdapter` - Yahoo Finance implementation
- `AcquisitionCoordinator` - Orchestrates with fallback

**Data Cleaning:**
- `DataCleaner` - Main cleaning orchestrator
- `MissingValueDetector` - Finds gaps and anomalies
- `SpikeDetector` - Identifies suspicious price movements
- `OHLCValidator` - Checks price relationships
- `SplitDividendAdjuster` - Handles corporate actions

**Data Quality:**
- `DataQualityValidator` - Validates cleaned data
- `SymbolExclusionManager` - Tracks excluded symbols

**Feature Engineering:**
- `FeatureOrchestrator` - Coordinates all feature computation
- `FeatureValidator` - Checks for leakage, NaN, causality
- `ReturnsFeature`, `NormalizedPricesFeature`, etc. - Individual feature modules

**Data Management:**
- `ChronologicalDataSplitter` - Train/val/test splitting
- `StandardScaler` - Preprocessing artifacts
- `ArtifactManager` - Versioning and storage

### Configuration Parameters

**Key Settings in `master_config.json`:**
```json
{
  "data_acquisition": {
    "min_trading_days": 2500,
    "lookback_years": 10,
    "retry_attempts": 3
  },
  "data_cleaning": {
    "spike_threshold": 0.20,
    "max_forward_fill_days": 2
  },
  "feature_engineering": {
    "tier1_enabled": true,
    "tier2_enabled": true,
    "tier3_enabled": false
  }
}
```

### Output Locations

```
results/
├── cleaning_reports/          # Per-symbol cleaning details
├── validation_reports/        # Quality validation results
├── features_manifests/        # Feature computation metadata
├── splits_metadata/           # Train/val/test date ranges
├── data_audit_trail.json      # Aggregate cleaning log
├── exclusion_summary.json     # Excluded symbols and reasons
└── cleaned_data/              # Cleaned OHLCV CSVs
```

---

## Further Reading

- **Requirements:** `.kiro/specs/stock-forecasting-system/requirements.md` (Sections 1, 3, 5)
- **Design:** `.kiro/specs/stock-forecasting-system/design.md` (Sections 1, 2, 3)
- **Troubleshooting:** `TROUBLESHOOTING.md` (data-related sections)
- **Architecture:** `ARCHITECTURE.md`
- **README:** `README.md` (quick start and overview)

---

**Last Updated:** 2024-01-19  
**Data Pipeline Version:** 1.0 (Stage 1)  
**Status:** Production-ready

