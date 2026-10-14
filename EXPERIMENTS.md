# Experiments Guide - Stock Market Forecasting System

A comprehensive practitioner's guide to running baseline models, executing ablation studies, interpreting results, troubleshooting, and extending the system.

**Audience:** Researchers, ML practitioners, and data scientists conducting experiments and ablation studies.

**Last Updated:** 2024-01-19  
**Status:** Stage 1 Complete - Baseline Models & Ablation Framework Ready

---

## Table of Contents

1. [Introduction](#introduction)
2. [Baseline Models](#baseline-models)
3. [Evaluation Metrics](#evaluation-metrics)
4. [Executing Ablation Studies](#executing-ablation-studies)
5. [Interpreting Results](#interpreting-results)
6. [Advanced Workflows](#advanced-workflows)
7. [Troubleshooting](#troubleshooting)
8. [Extending the System](#extending-the-system)
9. [Case Studies](#case-studies)
10. [Best Practices](#best-practices)

---

## Introduction

This guide covers three core experiment types:

### Baseline Model Evaluation

Baseline models provide contextualization for more sophisticated models:

- **Random Walk**: Null model predicting next return equals today's return
- **ARIMA(1,1,1)**: Time series model learning autoregressive and moving average patterns
- **Linear Regression**: Simple linear model on Tier-1 features only
- **Ridge Regression**: Regularized regression on all available features
- **Historical Mean**: Predicts next return as the historical average from training data

Why baselines matter:
- **Contextualization:** A 10% RMSE improvement only matters if baselines achieve 50% RMSE
- **Sanity check:** If baselines outperform your complex model, something is wrong
- **Feature value:** Comparing against baselines shows which features matter most
- **Publication standard:** Peer-reviewed papers require baseline comparisons

### Ablation Study Design

Ablation studies measure feature importance by systematically removing features and observing performance degradation:

- **Single removal:** Remove one feature or feature group
- **Sequential removal:** Remove features in priority order
- **Result:** Rank features by their contribution to model performance

### Result Interpretation

Understanding what results mean:
- Which metrics matter for your use case (risk-adjusted vs. prediction accuracy)
- Detecting data quality issues (distribution shifts, stationarity violations)
- Spotting data leakage (suspiciously good validation performance)
- Comparing fairly (same feature sets, same splits)

---

## Baseline Models

### Overview: Why Five Baselines?

Each baseline tests a specific hypothesis about predictability:

| Baseline | Hypothesis | Complexity | When to Use |
|----------|-----------|-----------|----------|
| **Random Walk** | Returns are random | Trivial | Null model; test market efficiency |
| **ARIMA(1,1,1)** | Returns autocorrelated | Low | Classic time series baseline |
| **Linear Regression** | Linear relationship, basic features | Low | Simple feature baseline |
| **Ridge Regression** | Linear relationship with regularization | Low | Leverage all features |
| **Historical Mean** | Stationary mean return | Trivial | Another null model |

### Running Baseline Models

#### Option 1: Full Pipeline (Recommended)

```bash
python pipeline.py
```

This trains all 5 baselines on your data and produces `baseline_results.json`.

#### Option 2: Programmatic Execution

```python
from baselines import BaselineManager
from evaluation import MetricsComputer

# Initialize manager
baseline_mgr = BaselineManager(config={})

# Train all baselines
results = baseline_mgr.train_and_evaluate_all(
    X_train=X_train,
    y_train=y_train,
    X_val=X_val,
    y_val=y_val,
    X_test=X_test,
    y_test=y_test
)

# Access results
for baseline_name, baseline_results in results.items():
    test_mae = baseline_results['test']['mae']
    print(f"{baseline_name}: MAE={test_mae:.4f}")
```

### Baseline 1: Random Walk

**What it does:** Next return = today's return

**Formula:** `r̂_t = r_{t-1}`

**When to use:** 
- Establish floor for model performance
- Detect spurious improvements
- Test if market is random walk

**Example:**

```python
from baselines.random_walk import RandomWalkBaseline

rw = RandomWalkBaseline()
rw.fit(y_train=y_train)
predictions = rw.predict(steps=len(y_test))
```

**Interpretation:** If Random Walk significantly outperforms your model, investigate:
- Is there strong return autocorrelation?
- Is your model overfitting to training data?
- Are your features causing data leakage?

### Baseline 2: ARIMA(1,1,1)

**What it does:** Autoregressive Integrated Moving Average

**Formula:**
```
∆r_t = μ + φ₁∆r_{t-1} + θ₁ε_{t-1} + ε_t

AR(1): Uses 1 past value
I(1): First difference (differencing)
MA(1): Uses 1 past error
```

**When to use:**
- Establish statistical baseline
- Test time series dynamics
- Compare with feature-based models

**Example:**

```python
from baselines.arima_model import ARIMABaseline

arima = ARIMABaseline(order=(1, 1, 1))
arima.fit(close_train=prices_train)
predicted_prices = arima.predict(steps=len(y_test))
```

**Interpretation:** If ARIMA outperforms Random Walk, returns have autocorrelation. If features beat ARIMA, features matter more than time series patterns.

### Baseline 3: Linear Regression (Tier-1)

**What it does:** Simple linear model using basic features only

**Formula:** `ŷ = β₀ + β₁·simple_return + β₂·log_return + β₃·norm_close_20 + β₄·norm_volume_20`

**When to use:**
- Baseline for feature-based models
- Show value of interpretable features
- Compare complex vs. simple models

**Example:**

```python
from baselines.linear_regression import LinearRegressionBaseline

lin_reg = LinearRegressionBaseline()
lin_reg.fit(y_train=y_train, X_train=X_train_tier1)

# View coefficients
coefs = lin_reg.coefficient_interpretation()
for feature, coef in coefs['coefficients'].items():
    print(f"{feature}: {coef:.6f}")
```

**Interpretation:** Coefficients show which features matter. Negative coefficient = contrarian signal.

### Baseline 4: Ridge Regression (All Features)

**What it does:** Regularized linear regression using all feature tiers

**Formula:**
```
minimize ||y - Xβ||² + α||β||²

Features: Tier-1 + Tier-2 + optional Tier-3
Alpha tuned via CV on validation set
```

**When to use:**
- Strong feature-based baseline
- Leverage all features with regularization
- Compare with deep learning models

**Example:**

```python
from baselines.ridge_regression import RidgeRegressionBaseline

ridge = RidgeRegressionBaseline(
    alphas=[0.001, 0.01, 0.1, 1.0, 10.0],
    cv=5
)
ridge.fit(y_train=y_train, X_train=X_train)
predictions = ridge.predict(X=X_test)

print(f"Selected alpha: {ridge.alpha_}")
```

**Interpretation:** If Ridge significantly outperforms Linear Regression, regularization helps (many correlated features). If similar, features are mostly independent.

### Baseline 5: Historical Mean

**What it does:** Predict next return as training average

**Formula:** `ŷ = mean(y_train)`

**When to use:**
- Another null model comparison
- Test mean-reversion hypothesis
- Quick sanity check

**Example:**

```python
from baselines.historical_mean import HistoricalMeanBaseline

hist_mean = HistoricalMeanBaseline()
hist_mean.fit(y_train=y_train)
predictions = hist_mean.predict(steps=len(y_test))
# All predictions = mean(y_train)
```

**Interpretation:** If Historical Mean outperforms other baselines, returns are stationary with mean-reversion. If other models beat it, returns have trending or complex patterns.

---

## Evaluation Metrics

Six metrics evaluate forecast quality from different perspectives.

### 1. Mean Absolute Error (MAE)

**What it measures:** Average absolute deviation

**Formula:** `MAE = mean(|predicted_return - actual_return|)`

**Interpretation:**
- In same units as returns (e.g., 0.025 = 2.5% average error)
- Robust to outliers (doesn't square errors)
- Easier to interpret than RMSE

**Example:**
```
Predicted: [0.02, -0.01, 0.03]
Actual:    [0.015, -0.015, 0.04]
Errors:    [0.005, 0.005, 0.01]
MAE: 0.00667 (0.667% average error)
```

**Use when:** You care about average prediction accuracy and want interpretable units.

### 2. Root Mean Squared Error (RMSE)

**What it measures:** Penalizes large errors more than small ones

**Formula:** `RMSE = sqrt(mean((predicted_return - actual_return)²))`

**Interpretation:**
- Quadratic penalty on errors (large errors hurt more)
- Same units as MAE
- RMSE ≥ MAE always (equality only if all errors same)

**Example:**
```
Errors: [0.001, 0.001, 0.05]
MAE: 0.017
RMSE: 0.029

RMSE penalizes the 0.05 error heavily, making RMSE >> MAE
```

**Use when:** Large errors are disproportionately costly (e.g., trading costs, risk management).

### 3. Mean Absolute Percentage Error (MAPE)

**What it measures:** Percentage error relative to actual returns

**Formula:** `MAPE = mean(|predicted_return - actual_return| / |actual_return|) × 100%`

**Interpretation:**
- Normalized by actual magnitude
- Good for comparing across symbols with different return scales
- Undefined when actual return = 0 (handled by ignoring those cases)

**Example:**
```
Predicted: 0.02, Actual: 0.10 → Error: 20%
Predicted: 0.02, Actual: 0.01 → Error: 100%

MAPE captures relative accuracy regardless of magnitude
```

**Use when:** Comparing performance across symbols with different volatilities.

### 4. Directional Accuracy

**What it measures:** Percentage of up/down predictions correct

**Formula:** `Directional_Accuracy = mean(sign(predicted_return) == sign(actual_return))`

**Interpretation:**
- Binary correctness: Did you get direction right?
- 50% = random guessing
- >55% is typically considered good for daily returns
- Ignores magnitude of error

**Example:**
```
Predictions: [+, -, +, -, +]
Actual:      [+, -, -, +, +]
Correct:     [✓, ✓, ✗, ✗, ✓]
Accuracy: 60%
```

**Use when:** Strategy depends on correct directional bets (long/short decisions).

### 5. Information Coefficient (IC)

**What it measures:** Ranking ability (Spearman rank correlation)

**Formula:** `IC = Spearman_correlation(actual_returns, predicted_returns)`

**Interpretation:**
- Ranges from -1 to +1
- Measures if model ranks returns correctly
- More robust to outliers than Pearson correlation
- 0 = no predictive power, 0.1 = weak, 0.3+ = strong

**Example:**
```
Top 5 actual returns: [0.08, 0.06, 0.05, 0.03, 0.02]
Model predicts:      [0.07, 0.06, 0.04, 0.03, 0.02]

Ranking is similar → High IC (ranks are correct even if magnitudes off)
```

**Use when:** Strategy ranks stocks/predictions and picks top N. IC matters more than absolute accuracy.

### 6. Sharpe Ratio

**What it measures:** Risk-adjusted returns (return per unit of volatility)

**Formula:** `Sharpe_Ratio = mean(predicted_returns) / std(predicted_returns)`

**Interpretation:**
- Assumes 0% risk-free rate
- Computed on predicted returns
- Higher is better (more return per volatility)
- Annualized: `Sharpe_Annual = Sharpe_Daily × sqrt(252)`

**Example:**
```
Model A predictions: mean=0.001, std=0.015 → Sharpe=0.067
Model B predictions: mean=0.001, std=0.012 → Sharpe=0.083

Model B more efficient (same return, lower volatility)
```

**Use when:** Portfolio management or risk-conscious trading (penalizes volatility).

### Computing Metrics

```python
from evaluation import MetricsComputer

# Initialize computer
computer = MetricsComputer(n_bootstrap=1000, random_state=42)

# Compute all metrics with bootstrap confidence intervals
results = computer.compute_all_metrics(
    y_true=y_test,
    y_pred=predictions,
    split_name='test'
)

# Access point estimates and CIs
for metric_name, metric_data in results['metrics'].items():
    point = metric_data['point_estimate']
    ci_lower = metric_data['ci_lower']
    ci_upper = metric_data['ci_upper']
    print(f"{metric_name}:")
    print(f"  Point: {point:.4f}")
    print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
```

**Output:**
```
mae:
  Point: 0.0245
  95% CI: [0.0218, 0.0272]
rmse:
  Point: 0.0356
  95% CI: [0.0304, 0.0408]
directional_accuracy:
  Point: 0.5342
  95% CI: [0.5101, 0.5583]
sharpe_ratio:
  Point: 0.0782
  95% CI: [-0.0045, 0.1609]
information_coefficient:
  Point: 0.0854
  95% CI: [0.0612, 0.1096]
mape:
  Point: 127.34
  95% CI: [98.2, 156.1]
```

### Metric Selection Guide

| Use Case | Best Metrics |
|----------|--------------|
| **Risk management** | RMSE, Sharpe Ratio |
| **Trading strategy** | Directional Accuracy, IC |
| **Portfolio optimization** | MAE, Sharpe Ratio |
| **Academic paper** | All six (completeness) |
| **Production deployment** | Directional Accuracy, IC (trading signals) |

---

## Executing Ablation Studies

Ablation studies measure feature contribution by removing features and measuring performance change.

### Understanding Ablation

**Core idea:** If removing feature X causes large performance drop, X is important. If removing X causes no drop, X is not contributing.

**Ablation types:**

1. **Single removal:** Remove one feature at a time (quick, interpretable)
2. **Group removal:** Remove entire feature tier (Tier-2, Tier-3, etc.)
3. **Sequential removal:** Remove features in priority order
4. **Full factorial:** All possible combinations (expensive, rarely used)

### Ablation Plan Structure

Ablation plan defines what to remove. Default in `ablation_plan.json`:

```json
{
  "groups": [
    {
      "name": "tier2_momentum",
      "description": "All momentum indicators (5/20/60-day)",
      "features": ["momentum_5", "momentum_20", "momentum_60"]
    },
    {
      "name": "tier2_volatility",
      "description": "Volatility indicators",
      "features": ["volatility_20"]
    },
    {
      "name": "tier2_rsi",
      "description": "RSI(14)",
      "features": ["rsi_14"]
    },
    {
      "name": "tier2_macd",
      "description": "MACD(12,26,9)",
      "features": ["macd_line", "macd_signal", "macd_histogram"]
    },
    {
      "name": "tier3_all",
      "description": "All Tier-3 features",
      "features": ["regime_bullish", "regime_bearish", "regime_sideways", "market_relative_strength"]
    }
  ]
}
```

### Running Ablation Studies

#### Option 1: Full Pipeline Ablation

```bash
# Run complete pipeline with ablation
python pipeline.py --ablation
```

This will:
1. Train baseline model on full feature set
2. For each group in ablation_plan:
   - Remove features from group
   - Retrain model
   - Evaluate on test set
   - Compute metric deltas
3. Produce `ablation_results.json` and `ablation_summary_table.csv`

#### Option 2: Programmatic Ablation

```python
from ablation import AblationFramework, AblationReporter
import json

# Load ablation plan
with open('ablation_plan.json') as f:
    plan_dict = json.load(f)

plan = AblationFramework.AblationPlan.build_from_dict(plan_dict)

# Run ablations
ablation_framework = AblationFramework(plan=plan)

results = ablation_framework.run_ablations(
    full_features=X_train,
    y_train=y_train,
    X_val=X_val,
    y_val=y_val,
    X_test=X_test,
    y_test=y_test,
    model_class=MyModel  # Your model (Ridge, etc.)
)

# Generate report
reporter = AblationReporter()
report = reporter.generate_report(results)
print(report)
```

#### Option 3: Single Ablation (Quick Test)

```python
from baselines.ridge_regression import RidgeRegressionBaseline
from evaluation import MetricsComputer

# Train full-feature baseline
ridge_full = RidgeRegressionBaseline()
ridge_full.fit(y_train=y_train, X_train=X_train_full)
pred_full = ridge_full.predict(X=X_test_full)

# Remove specific features (e.g., momentum)
X_test_no_momentum = X_test_full.drop(columns=['momentum_5', 'momentum_20', 'momentum_60'])
X_train_no_momentum = X_train_full.drop(columns=['momentum_5', 'momentum_20', 'momentum_60'])

ridge_no_momentum = RidgeRegressionBaseline()
ridge_no_momentum.fit(y_train=y_train, X_train=X_train_no_momentum)
pred_no_momentum = ridge_no_momentum.predict(X=X_test_no_momentum)

# Compare metrics
computer = MetricsComputer()
metrics_full = computer.compute_all_metrics(y_test, pred_full)
metrics_no_momentum = computer.compute_all_metrics(y_test, pred_no_momentum)

# Compute deltas
mae_delta = metrics_no_momentum['metrics']['mae']['point_estimate'] - metrics_full['metrics']['mae']['point_estimate']
print(f"Momentum features contribution (MAE delta): {mae_delta:.4f}")
```

### Interpreting Ablation Results

**Ablation output:** `ablation_summary_table.csv`

```csv
feature_group,baseline_mae,ablation_mae,mae_delta,mae_percent_change,baseline_directional_acc,ablation_directional_acc,acc_delta,p_value_ttest,significance
momentum,0.0245,0.0267,0.0022,9.0%,0.534,0.528,-0.006,0.156,not_significant
rsi_14,0.0245,0.0252,0.0007,2.9%,0.534,0.531,-0.003,0.387,not_significant
macd,0.0245,0.0289,0.0044,18.0%,0.534,0.521,-0.013,0.003,significant
tier3,0.0245,0.0251,0.0006,2.4%,0.534,0.533,-0.001,0.423,not_significant
```

**How to read:**
- **mae_delta**: MAE increases by this amount when feature removed (negative = better without feature)
- **mae_percent_change**: % degradation (positive = important feature)
- **p_value_ttest**: Statistical significance of difference (< 0.05 = significant)
- **significance**: Practical significance (marked if p < 0.05)

**Interpretation examples:**

| Feature | Delta | % | P-value | Conclusion |
|---------|-------|---|---------|-----------|
| MACD | +0.0044 | 18% | 0.003 | **Critical:** Removing hurts significantly |
| Momentum | +0.0022 | 9% | 0.156 | **Moderate:** Removes hurt performance but not significant |
| RSI | +0.0007 | 3% | 0.387 | **Weak:** Not contributing much |
| Tier-3 | +0.0006 | 2% | 0.423 | **Negligible:** Can likely remove |

### Feature Ranking

After ablation, rank features by importance:

```
1. MACD (18% degradation, p<0.001)
2. Momentum (9% degradation, p=0.156)
3. RSI (3% degradation, p=0.387)
4. Tier-3 (2% degradation, p=0.423)
```

**Use for:**
- Decide which features to keep in production
- Prioritize feature engineering efforts
- Reduce model complexity (remove low-importance features)
- Understand which market signals matter



---

## Interpreting Results

### Reading Output Reports

After running the pipeline, check these files:

**1. `results/baseline_results.json`**

```json
{
  "execution_timestamp": "2024-01-19T10:30:00Z",
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "baselines": {
    "random_walk": {
      "validation": {
        "mae": 0.0234,
        "rmse": 0.0356,
        "mape": 98.2,
        "directional_accuracy": 0.513,
        "sharpe_ratio": 0.0456,
        "information_coefficient": 0.0123
      },
      "test": {
        "mae": 0.0267,
        "rmse": 0.0389,
        "mape": 112.5,
        "directional_accuracy": 0.502,
        "sharpe_ratio": -0.0178,
        "information_coefficient": -0.0056
      }
    },
    "arima_111": { ... },
    "linear_regression": { ... },
    "ridge_regression": { ... },
    "historical_mean": { ... }
  }
}
```

**How to interpret:**
- Compare metrics across baselines (which is best?)
- Compare validation vs. test (large gap = overfitting?)
- Compare against deep learning model (how much better?)
- Check if any metric unusually good (possible data leakage?)

**2. `results/pipeline_report.md`**

Human-readable summary containing:
- Data source and symbols processed
- Cleaning summary (rows removed, gaps filled)
- Feature engineering summary
- Data split dates and row counts
- Baseline results comparison
- Any warnings or data quality issues
- Execution time

**3. `results/model_card.md`**

Documentation for the model:
- Intended use
- Training data description
- Evaluation methodology
- Known limitations
- Recommendations

### Detecting Data Quality Issues

Poor data quality shows up in results. Warning signs:

**1. Validation >> Test Performance**

```
Validation MAE: 0.015
Test MAE: 0.045

Large gap suggests overfitting or validation data different from test
```

**Action:** Check `splits_metadata.json` for date ranges. Are validation and test from different market regimes?

**2. Very High Directional Accuracy (>60% on daily returns)**

```
Directional Accuracy: 0.68

Too good to be true for daily returns (random walk has ~50%)
```

**Action:** Check for data leakage. Are future prices used in features?

**3. Baseline Wildly Better Than Complex Model**

```
Historical Mean MAE: 0.015
Your Deep Learning Model MAE: 0.045
```

**Action:** 
- Check feature computation for leakage (e.g., using future data)
- Verify preprocessing fit only on training data
- Check if features are scaled correctly

**4. All Baselines Similar Performance**

```
Random Walk: 0.0245 MAE
ARIMA: 0.0248 MAE
Linear Reg: 0.0246 MAE
Ridge: 0.0244 MAE
Historical Mean: 0.0247 MAE
```

**Action:** Likely no strong signals in data or baselines not properly configured. Check feature distributions.

**5. NaN or Inf in Results**

```
mae: null
information_coefficient: null
sharpe_ratio: null
```

**Action:** Indicates missing data or invalid predictions. Check logs for warnings about NaN values.

### Comparing Baselines Fairly

**Fair comparison requires:**

1. ✓ Same training data
2. ✓ Same validation/test splits
3. ✓ Same preprocessing (if applicable)
4. ✓ Same evaluation metrics
5. ✓ Statistical significance testing (bootstrap CIs)

**Unfair comparison (to avoid):**

- ✗ Different train/test splits per baseline
- ✗ Preprocessing fit per-baseline (leakage!)
- ✗ Hyperparameter tuning on test data
- ✗ Cherry-picking metrics that make model look good

### Baseline Ranking Example

**Real example: AAPL daily return prediction**

```
Test Set Performance (MAE, lower better):

1. Ridge Regression:     0.0234 ± 0.0018  ← Best
2. Linear Regression:    0.0245 ± 0.0021
3. ARIMA(1,1,1):         0.0256 ± 0.0023
4. Historical Mean:      0.0267 ± 0.0025
5. Random Walk:          0.0278 ± 0.0027

Ridge beats Random Walk by 16% (0.0234 vs 0.0278)

Directional Accuracy:

1. Ridge Regression:     55.3% ± 2.1%     ← Better than random
2. Linear Regression:    54.8% ± 2.2%
3. ARIMA:                53.2% ± 2.3%
4. Historical Mean:      50.9% ± 2.4%     ← At random chance
5. Random Walk:          50.1% ± 2.5%     ← Random (51% by chance)
```

**Conclusion:** Ridge Regression is best. Features matter (beats baselines). Directional accuracy modest but above random.

---

## Advanced Workflows

### 1. Custom Feature Ablation

Test importance of a custom feature:

```python
# Your new feature engineering
X_custom = X_test.copy()
X_custom['my_custom_feature'] = compute_custom_feature(prices_test)

# Train with custom feature
model_with = Ridge()
model_with.fit(
    X_train[[...all features..., 'my_custom_feature']],
    y_train
)
pred_with = model_with.predict(X_custom)

# Train without
model_without = Ridge()
model_without.fit(
    X_train[[...all except custom...]],
    y_train
)
pred_without = model_without.predict(X_test.drop('my_custom_feature', axis=1))

# Compare
mae_with = np.mean(np.abs(pred_with - y_test))
mae_without = np.mean(np.abs(pred_without - y_test))
improvement = (mae_without - mae_with) / mae_without * 100

print(f"Custom feature improves MAE by {improvement:.1f}%")
```

### 2. Per-Symbol Analysis

Ablation by symbol to see if features matter differently across stocks:

```python
import pandas as pd
from baselines.ridge_regression import RidgeRegressionBaseline

symbols = ['AAPL', 'MSFT', 'GOOGL']
results_per_symbol = {}

for symbol in symbols:
    # Get data for symbol
    idx = train_symbols == symbol
    X_train_sym = X_train[idx]
    y_train_sym = y_train[idx]
    X_test_sym = X_test[test_symbols == symbol]
    y_test_sym = y_test[test_symbols == symbol]
    
    # Full features
    ridge = RidgeRegressionBaseline()
    ridge.fit(y_train_sym, X_train_sym)
    pred_full = ridge.predict(X_test_sym)
    mae_full = np.mean(np.abs(pred_full - y_test_sym))
    
    # Without momentum
    X_train_no_mom = X_train_sym.drop(['momentum_5', 'momentum_20', 'momentum_60'], axis=1)
    X_test_no_mom = X_test_sym.drop(['momentum_5', 'momentum_20', 'momentum_60'], axis=1)
    ridge_no_mom = RidgeRegressionBaseline()
    ridge_no_mom.fit(y_train_sym, X_train_no_mom)
    pred_no_mom = ridge_no_mom.predict(X_test_no_mom)
    mae_no_mom = np.mean(np.abs(pred_no_mom - y_test_sym))
    
    # Delta
    delta = (mae_no_mom - mae_full) / mae_full * 100
    results_per_symbol[symbol] = delta
    print(f"{symbol}: Momentum importance = {delta:.1f}%")
```

### 3. Time-Based Ablation

See if feature importance changes over time:

```python
# Split test data into months
test_df = X_test.copy()
test_df['date'] = test_dates
test_df['month'] = test_df['date'].dt.to_period('M')

ablation_by_month = {}

for month, group in test_df.groupby('month'):
    idx = group.index
    y_month = y_test[idx]
    X_month = X_test.iloc[idx]
    
    # Run ablation for this month
    ridge_full = RidgeRegressionBaseline()
    ridge_full.fit(y_train, X_train)
    mae_full = np.mean(np.abs(ridge_full.predict(X_month) - y_month))
    
    # (Without momentum, etc.)
    # ... calculate mae_no_momentum ...
    
    ablation_by_month[str(month)] = {
        'mae_full': mae_full,
        'mae_no_momentum': mae_no_momentum,
        'importance': (mae_no_momentum - mae_full) / mae_full
    }

# Plot importance over time
import matplotlib.pyplot as plt
months = list(ablation_by_month.keys())
importances = [ablation_by_month[m]['importance'] for m in months]
plt.plot(months, importances, marker='o')
plt.ylabel('Momentum Feature Importance')
plt.xlabel('Month')
plt.show()
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Baseline Results All NaN

**Symptom:** `baseline_results.json` contains only null values

**Causes:**
- Features contain NaN values
- Preprocessing produced invalid data
- Feature scaling failed

**Solution:**
```python
# Check for NaN in features
print(f"NaN in X_train: {X_train.isna().sum().sum()}")
print(f"NaN in y_train: {y_train.isna().sum()}")

# Check scaling
print(f"Feature means: {X_train.mean()}")
print(f"Feature stds: {X_train.std()}")

# Ensure no inf
print(f"Inf in X_train: {np.isinf(X_train).sum().sum()}")
```

#### Issue 2: Validation MAE Much Better Than Test MAE

**Symptom:**
```
Validation MAE: 0.015
Test MAE: 0.045 (3x worse!)
```

**Causes:**
- Validation and test from different market regimes
- Preprocessing leak (scaler fit on both train and validation)
- Hyperparameters overfit to validation set

**Solution:**
```python
# Check date ranges
print(f"Train dates: {train_dates.min()} to {train_dates.max()}")
print(f"Val dates: {val_dates.min()} to {val_dates.max()}")
print(f"Test dates: {test_dates.min()} to {test_dates.max()}")

# Verify no overlap
assert train_dates.max() <= val_dates.min()
assert val_dates.max() <= test_dates.min()

# Check distributions
print(f"Train return mean: {y_train.mean():.4f}, std: {y_train.std():.4f}")
print(f"Val return mean: {y_val.mean():.4f}, std: {y_val.std():.4f}")
print(f"Test return mean: {y_test.mean():.4f}, std: {y_test.std():.4f}")

# If very different, market regimes are different
```

#### Issue 3: Ridge Regression Much Worse Than Linear Regression

**Symptom:**
```
Linear Regression MAE: 0.024
Ridge Regression MAE: 0.038 (significantly worse)
```

**Causes:**
- Alpha too high (over-regularized)
- Features have different scales

**Solution:**
```python
# Check alpha selected
print(f"Selected alpha: {ridge.alpha_}")

# Try different alpha range
ridge = RidgeRegressionBaseline(
    alphas=[0.00001, 0.0001, 0.001, 0.01, 0.1],  # Wider range
    cv=5
)
ridge.fit(y_train, X_train)
print(f"New alpha: {ridge.alpha_}")

# Ensure features are scaled
print(f"Feature std before scaling: {X_train.std()}")
# They should be roughly 1.0 each after scaling
```

#### Issue 4: ARIMA Fails to Fit

**Symptom:**
```
ValueError: ARIMA(1,1,1) failed to converge
```

**Causes:**
- Insufficient training data
- Missing values in close prices
- Non-stationary differencing unstable

**Solution:**
```python
# Check data length
print(f"Training data points: {len(y_train)}")
# ARIMA needs at least 50+ points

# Check for NaN in close prices
print(f"NaN in close prices: {close_train.isna().sum()}")
# Must be 0

# Try different order
arima = ARIMABaseline(order=(1, 0, 1))  # No differencing
arima.fit(close_train=close_train)
```

#### Issue 5: Ablation Results Show All Features Equally Important

**Symptom:**
```
All features have ~5% importance
Nothing stands out
```

**Causes:**
- Features are highly correlated (multicollinearity)
- Signal is weak in data
- Model can't learn individual feature importance

**Solution:**
```python
# Check correlation
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 10))
plt.imshow(X_train.corr(), cmap='coolwarm', vmin=-1, vmax=1)
plt.colorbar()
plt.title('Feature Correlation')
plt.show()

# Remove highly correlated features
corr_matrix = X_train.corr().abs()
upper_tri = corr_matrix.where(
    np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
)
to_drop = [col for col in upper_tri.columns if (upper_tri[col] > 0.95).any()]
print(f"Remove correlated features: {to_drop}")

X_train_clean = X_train.drop(to_drop, axis=1)
X_test_clean = X_test.drop(to_drop, axis=1)
```

---

## Extending the System

### Adding a Custom Baseline Model

**Step 1: Create model class**

```python
# baselines/my_model.py
import numpy as np
from baselines.base_model import BaselineModel

class MyCustomBaseline(BaselineModel):
    """My custom baseline model."""
    
    def __init__(self, logger=None):
        super().__init__(name='my_custom', logger=logger)
        self.model = None
    
    def fit(self, y_train, X_train=None, **kwargs):
        """Train on training data."""
        y_train = self._as_vector(y_train, 'y_train')
        
        # Your training logic here
        self.model = self._fit_my_model(y_train, X_train)
        return self
    
    def predict(self, X=None, steps=None, **kwargs):
        """Generate predictions."""
        if steps is None:
            steps = len(X) if X is not None else 1
        
        # Your prediction logic
        predictions = self._predict_my_model(steps)
        return predictions
    
    def _fit_my_model(self, y, X):
        # Custom implementation
        pass
    
    def _predict_my_model(self, steps):
        # Custom implementation
        pass
```

**Step 2: Register in BaselineManager**

```python
# baselines/__init__.py - add to train_and_evaluate_all()

def train_and_evaluate_all(self, X_train, y_train, X_val, y_val, X_test, y_test):
    results = {}
    
    # ... existing baselines ...
    
    # Add your custom baseline
    my_model = MyCustomBaseline(logger=self.logger)
    my_model.fit(y_train, X_train=X_train)
    
    results['my_custom'] = {
        'validation': self._evaluate_split(my_model, X_val, y_val, 'validation'),
        'test': self._evaluate_split(my_model, X_test, y_test, 'test'),
        'model': my_model
    }
    
    return results
```

**Step 3: Test**

```python
from baselines import BaselineManager

manager = BaselineManager()
results = manager.train_and_evaluate_all(X_train, y_train, X_val, y_val, X_test, y_test)

print(f"My Custom MAE: {results['my_custom']['test']['mae']:.4f}")
```

### Adding Custom Features for Ablation

**Step 1: Create feature module**

```python
# features/custom/my_feature.py
import numpy as np
import pandas as pd
from features.base_features import FeatureModule

class MyCustomFeature(FeatureModule):
    """My custom feature computation."""
    
    def __init__(self, config=None):
        super().__init__('my_custom_feature', tier=2, config=config or {})
    
    def compute(self, df, fit_data=None):
        """Compute feature from OHLCV DataFrame."""
        # Your computation
        feature_values = self._compute_my_logic(df)
        
        result = pd.DataFrame({
            'my_custom_feature': feature_values
        }, index=df.index)
        
        return result
    
    def validate(self, features):
        """Validate output."""
        errors = []
        if features['my_custom_feature'].isna().any():
            errors.append("Feature contains NaN")
        if np.isinf(features['my_custom_feature']).any():
            errors.append("Feature contains inf")
        return len(errors) == 0, errors
    
    def _compute_my_logic(self, df):
        # Your logic
        pass
```

**Step 2: Add to ablation plan**

```json
{
  "groups": [
    {
      "name": "my_custom_features",
      "description": "My custom features",
      "features": ["my_custom_feature"]
    }
  ]
}
```

**Step 3: Test importance**

```python
# Run ablation with your custom feature
# Results will show importance of my_custom_features group
```

### Adding a New Evaluation Metric

**Step 1: Add to EvaluationMetrics**

```python
# evaluation/metrics.py

class EvaluationMetrics:
    # ... existing metrics ...
    
    @staticmethod
    def custom_metric(y_true, y_pred):
        """Your custom metric computation."""
        actual, predicted = EvaluationMetrics._paired(y_true, y_pred)
        
        # Your logic
        result = my_computation(actual, predicted)
        return float(result)
```

**Step 2: Add to compute_all()**

```python
    @classmethod
    def compute_all(cls, y_true, y_pred, sharpe_returns=None):
        actual, predicted = cls._paired(y_true, y_pred)
        return {
            'mae': cls.mae(actual, predicted),
            'rmse': cls.rmse(actual, predicted),
            'mape': cls.mape(actual, predicted),
            'directional_accuracy': cls.directional_accuracy(actual, predicted),
            'sharpe_ratio': cls.sharpe_ratio(predicted if sharpe_returns is None else sharpe_returns),
            'information_coefficient': cls.information_coefficient(actual, predicted),
            'custom_metric': cls.custom_metric(actual, predicted),  # ADD THIS
        }
```

---

## Case Studies

### Case Study 1: Feature Importance Discovery

**Scenario:** You trained a complex model but want to understand which features drive predictions.

**Approach:**

1. Train Ridge Regression baseline (strong interpretable baseline)
2. Run ablation removing each Tier-2 indicator
3. Rank features by MAE degradation
4. Focus engineering on top-3 features

**Example:**

```python
# Run ablation
ablation_results = run_ablations_for_symbol('AAPL', model=RidgeRegression)

# Results
top_features = ablation_results.sort_values('mae_delta', ascending=False).head(5)
print(top_features)
```

**Output:**
```
feature_group          mae_delta   importance
macd                   0.0044      18%
momentum                0.0022      9%
volatility_20          0.0018      7%
rsi_14                 0.0007      3%
bollinger_bands        0.0005      2%
```

**Decision:** Focus engineering on MACD and momentum. RSI and Bollinger don't contribute much.

### Case Study 2: Debugging Poor Performance

**Scenario:** Your model performs well on validation (50% directional accuracy) but poorly on test (46%).

**Diagnosis:**

```python
# Check for data issues
print(f"Validation return distribution:")
print(f"  Mean: {y_val.mean():.6f}, Std: {y_val.std():.6f}")
print(f"  Min: {y_val.min():.4f}, Max: {y_val.max():.4f}")

print(f"Test return distribution:")
print(f"  Mean: {y_test.mean():.6f}, Std: {y_test.std():.6f}")
print(f"  Min: {y_test.min():.4f}, Max: {y_test.max():.4f}")

# Check baselines
print(f"Baseline performance:")
print(f"  Random Walk Val: {baseline_rw_val:.4f}, Test: {baseline_rw_test:.4f}")
print(f"  Ridge Val: {baseline_ridge_val:.4f}, Test: {baseline_ridge_test:.4f}")
```

**Findings:**

```
Validation return distribution:
  Mean: 0.000234, Std: 0.018234
  Min: -0.105, Max: 0.098

Test return distribution:
  Mean: -0.001876, Std: 0.025612  ← Much higher volatility!
  Min: -0.156, Max: 0.142

Baseline performance:
  Random Walk Val: 0.50, Test: 0.48
  Ridge Val: 0.52, Test: 0.44  ← Also degrades more

Conclusion: Test period has higher volatility (different market regime).
Model overfit to validation volatility level.
```

**Solution:** 
- Retrain with adaptive volatility scaling
- Or accept that model's signal is period-dependent
- Flag test period as high-volatility (trade with smaller positions)

### Case Study 3: Comparing Models

**Scenario:** You have Model A (deep learning) and want to compare against baselines.

**Process:**

```python
import pandas as pd

# Get baseline results
baseline_results = {
    'Random Walk': 0.0278,
    'ARIMA': 0.0256,
    'Linear Reg': 0.0245,
    'Ridge': 0.0234,
}

# Your model result
my_model_mae = 0.0218

# Compare
comparison = pd.DataFrame({
    'Model': list(baseline_results.keys()) + ['My Deep Learning'],
    'MAE': list(baseline_results.values()) + [my_model_mae],
})

comparison['Better Than'] = comparison['MAE'].apply(
    lambda x: sum(1 for v in comparison['MAE'] if v > x) / len(comparison)
)

comparison = comparison.sort_values('MAE')
print(comparison)
```

**Output:**
```
                Model     MAE  Better Than
3               Ridge  0.0234  20% (1/5)
4  My Deep Learning  0.0218  60% (3/5)  ← Your model wins!
0        Linear Reg  0.0245   0% (0/5)
2              ARIMA  0.0256   0% (0/5)
1        Random Walk  0.0278   0% (0/5)
```

**Conclusion:** Your model beats Ridge by 6.8% (0.0234 → 0.0218). This is modest but meaningful if prediction accuracy translates to trading profit.

---

## Best Practices

### 1. Reproducibility Checklist

- [ ] Save `master_config.json` with experiment ID
- [ ] Document random seed (should be fixed)
- [ ] Version all preprocessing artifacts (scalers, Kalman params)
- [ ] Save training/validation/test split dates
- [ ] Document feature engineering logic (formula for each feature)
- [ ] Keep experiment logs (pipeline_*.log)
- [ ] Archive results in `experiment_results/{exp_id}/`

### 2. Baseline Comparison Best Practices

- [ ] Use SAME training data for all baselines
- [ ] Use SAME validation/test splits for all baselines
- [ ] Apply preprocessing (scaling) consistently across baselines
- [ ] Report metrics with bootstrap confidence intervals
- [ ] Test statistical significance (p-values)
- [ ] Compare on all metrics (not just MAE)
- [ ] Include baseline comparisons in plots/tables

### 3. Ablation Study Best Practices

- [ ] Pre-define ablation plan before running experiments
- [ ] Use paired tests (both with and without feature from same train/val/test)
- [ ] Report statistical significance (p-values)
- [ ] Test on both validation and test sets
- [ ] Document feature definitions in ablation report
- [ ] Consider interaction effects (some features valuable only with others)
- [ ] Archive ablation plan with results for reproducibility

### 4. Results Interpretation Best Practices

- [ ] Always compare against baselines (never report model results alone)
- [ ] Check for data leakage (suspiciously good validation performance)
- [ ] Verify train/val/test splits are truly chronological
- [ ] Report confidence intervals (not just point estimates)
- [ ] Note market regimes during evaluation periods
- [ ] Discuss limitations (which symbols/periods work best/worst)
- [ ] Be honest about what your model can't do

### 5. Result Documentation

For each experiment, record:

```markdown
## Experiment {ID}

### Setup
- Symbols: AAPL, MSFT, GOOGL
- Data range: 2015-01-01 to 2024-01-19
- Features: Tier-1 + Tier-2
- Model: Ridge Regression

### Results

#### Baseline Comparison
| Model | Test MAE | Directional Acc |
|-------|----------|-----------------|
| Random Walk | 0.0278 | 50.1% |
| ARIMA | 0.0256 | 53.2% |
| Linear Reg | 0.0245 | 54.8% |
| Ridge | 0.0234 | 55.3% |

#### Feature Ablation
| Feature | Importance | P-value |
|---------|-----------|---------|
| MACD | 18% | 0.003 |
| Momentum | 9% | 0.156 |
| RSI | 3% | 0.387 |

### Conclusions
- Ridge beats baselines by 16%
- MACD is critical (p<0.01)
- Momentum contributes but not significantly (p=0.156)

### Limitations
- Only 5 symbols tested
- Market conditions 2024 may differ from training period (2015-2023)
- High volatility periods not thoroughly tested
```

---

## FAQ

### Q: Why doesn't my baseline outperform Random Walk?

**A:** Possible reasons:
1. Market is efficient (returns are truly random)
2. Features are poor quality or have NaN values
3. Preprocessing created issues (scaling problems)
4. Hyperparameters not tuned (e.g., Ridge alpha too high)

**Check:** Run diagnostic on features and data splits.

### Q: Should I use MAE or RMSE?

**A:** Use both:
- **MAE:** More robust to outliers, easier to interpret
- **RMSE:** Better when large errors are costly

Report both in any publication.

### Q: How do I know if ablation differences are "significant"?

**A:** Use p-values from paired t-tests:
- **p < 0.05:** Statistically significant (can trust the difference)
- **p > 0.05:** Not significant (could be random variation)
- **p < 0.01:** Highly significant (very strong evidence)

Ablation framework computes this automatically.

### Q: Can I use the same data for hyperparameter tuning and ablation?

**A:** NO! Hyperparameter tuning and ablation require independent data:
- Tune hyperparameters on validation set
- Run ablation on test set
- Otherwise, you're double-dipping (overfitting)

### Q: What if ablation shows all features equally important?

**A:** Likely causes:
1. Features are multicollinear (highly correlated)
2. Signal is weak in data
3. Model can't isolate feature importance

**Solution:** Remove correlated features first, then re-run ablation.

### Q: How many samples do I need for good baseline performance?

**A:** At least:
- **500 samples:** Minimum for any learning
- **1,000 samples:** Better
- **2,500+ samples:** Ideal (what the system targets)

With < 1,000 samples, expect high variance in results.

### Q: Should I run baselines on each symbol separately?

**A:** Depends on your use case:
- **Per-symbol baselines:** If trading individual stocks, yes
- **Pooled baselines:** If portfolio strategy, combine all symbols

Report both perspectives if possible.

### Q: Can I compare models trained on different feature sets?

**A:** Only with caution. Best practice:
- Train Model A on Feature Set 1
- Train Model B on same Feature Set 1
- Compare results
- Then ablate Feature Set 1 to isolate feature effect

Don't compare models on different feature sets (confounds too many variables).

---

**Last Updated:** 2024-01-19  
**Maintained by:** Research team  
**Questions?** Refer to ARCHITECTURE.md, DATA_GUIDE.md, or TROUBLESHOOTING.md
