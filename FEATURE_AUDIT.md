# Comprehensive Feature Audit & Literature Contribution Analysis

**Project:** Regime-Aware Multi-Scale Deep Stock Forecasting System  
**Date:** October 12, 2026  
**Repository:** `c:\Users\ASUS\stock optimizer`  

---

## 1. Master Feature Audit Table

The table below catalogs every feature currently implemented, partially implemented, or claimed in project specifications.

| Feature Name | Formula / Logic | Source Data | Implemented | Leakage-Safe | Tested | Used by Model |
|---|---|---|---|---|---|---|
| `simple_return` | $\frac{Close_t - Close_{t-1}}{Close_{t-1}}$ | Close | Yes | Yes (uses $t-1$) | Yes | Yes (Linear/Ridge Baselines) |
| `log_return` | $\ln(Close_t / Close_{t-1})$ | Close | Yes | Yes (uses $t-1$) | Yes | No (Unused) |
| `close_ma20` | $\frac{1}{20}\sum_{i=0}^{19} Close_{t-i}$ | Close | Yes | Yes (trailing 20) | Yes | No (Unused) |
| `close_std20` | $\sqrt{\frac{1}{19}\sum_{i=0}^{19}(Close_{t-i} - MA20_t)^2}$ | Close | Yes | Yes (trailing 20) | Yes | No (Unused) |
| `normalized_close` | $\frac{Close_t - close\_ma20_t}{close\_std20_t}$ | Close | Yes | Yes (trailing 20) | Yes | Yes (Linear/Ridge Baselines) |
| `normalized_volume` | $\frac{Volume_t}{\text{MA}(Volume, 20)_t}$ | Volume | Yes | Yes (trailing 20) | Yes | Yes (Linear/Ridge Baselines) |
| `rsi_14` | $100 - \frac{100}{1 + \frac{\text{EMA}(Gain, 14)}{\text{EMA}(Loss, 14)}}$ | Close | Yes | Yes (trailing 14) | Partial (12 tests fail) | No (Unused) |
| `macd_line` | $\text{EMA}(Close, 12) - \text{EMA}(Close, 26)$ | Close | Yes | Yes (trailing EMA) | Partial | No (Unused) |
| `macd_signal` | $\text{EMA}(macd\_line, 9)$ | Close | Yes | Yes (trailing EMA) | Partial | No (Unused) |
| `macd_histogram` | $macd\_line_t - macd\_signal_t$ | Close | Yes | Yes (trailing EMA) | Partial | No (Unused) |
| `bb_upper` | $\text{SMA}(Close, 20) + 2 \times \sigma_{20}$ | Close | Yes | Yes (trailing 20) | Partial | No (Unused) |
| `bb_middle` | $\text{SMA}(Close, 20)$ | Close | Yes | Yes (trailing 20) | Partial | No (Unused) |
| `bb_lower` | $\text{SMA}(Close, 20) - 2 \times \sigma_{20}$ | Close | Yes | Yes (trailing 20) | Partial | No (Unused) |
| `bb_width` | $bb\_upper_t - bb\_lower_t$ | Close | Yes | Yes (trailing 20) | Partial | No (Unused) |
| `stoch_k` | $100 \times \frac{Close_t - \min(Low_{t-13..t})}{\max(High_{t-13..t}) - \min(Low_{t-13..t})}$ | High, Low, Close | Yes | Yes (trailing 14) | Partial | No (Unused) |
| `stoch_d` | $\text{SMA}(stoch\_k, 3)$ | High, Low, Close | Yes | Yes (trailing 3) | Partial | No (Unused) |
| `atr_14` | $\text{SMA}(\text{TrueRange}, 14)$ | High, Low, Close | Yes | Yes (trailing 14) | Partial | No (Unused) |
| `adx_plus_di` | $100 \times \frac{\text{SMA}(+DM, 14)}{atr\_14}$ | High, Low, Close | Yes | Yes (trailing 14) | Partial | No (Unused) |
| `adx_minus_di` | $100 \times \frac{\text{SMA}(-DM, 14)}{atr\_14}$ | High, Low, Close | Yes | Yes (trailing 14) | Partial | No (Unused) |
| `adx_value` | $\text{SMA}\left(100 \times \frac{\|+DI - -DI\|}{+DI + -DI}, 14\right)$ | High, Low, Close | Yes | Yes (trailing 14) | Partial | No (Unused) |
| `obv` | $\sum \text{sign}(\Delta Close_t) \times Volume_t$ | Close, Volume | Yes | Yes (cumulative) | Partial | No (Unused) |
| `obv_ma20` | $\text{SMA}(obv, 20)$ | Close, Volume | Yes | Yes (trailing 20) | Partial | No (Unused) |
| `momentum_5` | $\frac{Close_t}{Close_{t-5}} - 1$ | Close | Yes | Yes (lag 5) | Yes | No (Unused) |
| `momentum_20` | $\frac{Close_t}{Close_{t-20}} - 1$ | Close | Yes | Yes (lag 20) | Yes | No (Unused) |
| `momentum_60` | $\frac{Close_t}{Close_{t-60}} - 1$ | Close | Yes | Yes (lag 60) | Yes | No (Unused) |
| `volatility_20` | $\sigma(r_{t-19 \dots t})$ | Close | Yes | Yes (trailing 20) | Yes | No (Unused) |
| `price_pressure` | Claimed order-flow / price pressure | OHLCV | **NO** | N/A | No | No |
| `volume_pressure` | Claimed buying/selling volume pressure | OHLCV | **NO** | N/A | No | No |
| `market_regime` | Discrete state $\{0,1,2,3\}$ based on 60d return & vol | Close (own/SPY) | Yes | Yes (trailing 60) | Yes | No (Unused) |
| `market_volatility_annualized` | $\sigma_{60}(\text{SPY}) \times \sqrt{252}$ | SPY Close | Yes | Yes (trailing 60) | Yes | No (Unused) |
| `relative_strength` | $\text{Corr}_{60}(r_{\text{stock}}, r_{\text{SPY}})$ | Stock Close, SPY Close | Yes | Potential (live network) | Yes | No (Unused) |
| `sector_correlation` | $\text{Corr}_{60}(r_{\text{stock}}, r_{\text{sector\_ETF}})$ | Stock Close, Sector ETF | Yes | Potential (live network) | Yes | No (Unused) |
| `sector_peer_corr_top_1..5` | Dynamic top 5 correlations among sector peers | Stock & Peer Closes | Yes | Yes (trailing 60) | Yes | No (Unused) |
| `sector_peer_corr_top_mean` | Mean of top 5 peer correlations | Stock & Peer Closes | Yes | Yes (trailing 60) | Yes | No (Unused) |
| `wavelet_approximation` | Endpoint reconstructed Daubechies db4 approx ($L3$) | Trailing log Close (64) | Yes | Yes (trailing window) | Yes | No (Unused) |
| `wavelet_detail_1..3` | Endpoint reconstructed db4 details ($L1, L2, L3$) | Trailing log Close (64) | Yes | Yes (trailing window) | Yes | No (Unused) |
| `ssa_trend` | Rank-1 SVD reconstructed trend endpoint | Trailing log Close (40) | Yes | Yes (trailing window) | Yes | No (Unused) |
| `ssa_residual` | $log(Close_t) - ssa\_trend_t$ | Trailing log Close (40) | Yes | Yes (trailing window) | Yes | No (Unused) |
| `kalman_level` | Recursive 1D state estimate $x_{t \mid t}$ | Log Close | Yes | Yes (forward filter) | Yes | No (Unused) |
| `kalman_innovation_zscore` | Standardized innovation $\frac{y_t - x_{t \mid t-1}}{\sqrt{F_t}}$ | Log Close | Yes | Yes (forward filter) | Yes | No (Unused) |
| `kalman_variance` | Filtered state posterior variance $P_{t \mid t}$ | Log Close | Yes | Yes (forward filter) | Yes | No (Unused) |

---

## 2. Mathematical Definition Verification & Edge Cases

### 2.1 Return Calculations (`tier1/returns.py`)
- **Simple Return:** $r_t = \frac{P_t - P_{t-1}}{P_{t-1}}$.
  - *Edge case handled:* Row 0 is `NaN`.
  - *Bug/Risk:* If $P_{t-1} = 0$, division by zero occurs. In stock markets prices are non-zero, but data cleaning must guarantee $P > 0$.
- **Log Return:** $z_t = \ln(P_t / P_{t-1})$.
  - *Edge case handled:* Requires $P_t > 0$. First row is `NaN`.

### 2.2 Normalized Features (`tier1/normalized_prices.py`)
- **Normalized Close:** $z_t = \frac{Close_t - \text{MA20}_t}{\text{STD20}_t}$.
  - *Edge case:* First 19 rows are `NaN`. If price is static over 20 days, $\text{STD20} = 0$, causing division by zero. Code does not add an $\epsilon = 10^{-8}$ to the denominator, risking `inf` or `NaN`.
- **Normalized Volume:** $v_t = \frac{Volume_t}{\text{MA20}(Volume)_t}$.
  - *Edge case:* Zero-volume days produce 0 or division by zero if average volume is zero.

### 2.3 Technical Indicators (`tier2/technical_indicators.py`)
- **RSI(14):** Wilder's RSI using exponential smoothing with span 14:
  $$RS = \frac{\text{EMA}(Gain, 14)}{\text{EMA}(Loss, 14)}, \quad RSI = 100 - \frac{100}{1 + RS}$$
  - *Edge case:* If there are zero losses over 14 bars, `avg_loss = 0`, causing $RS = \infty$ and division by zero. Pandas returns `inf`, and $RSI \to 100$, but unhandled warnings can occur.
- **Bollinger Bands:** $\text{SMA20} \pm 2 \cdot \sigma_{20}$.
  - *Inconsistency:* Outputs `bb_width`, but `ablation_plan.json` looks for `bollinger_bandwidth`.
- **Stochastic Oscillator:**
  - $K = 100 \times \frac{Close_t - L_{14}}{H_{14} - L_{14}}$.
  - *Edge case:* In price stasis ($H_{14} = L_{14}$), denominator is zero. Result is `NaN`.
- **ADX(14):**
  - Requires smoothing of $+DM, -DM$ and True Range.
  - *Edge case:* If $DI^+ + DI^- = 0$, $DX = \frac{|DI^+ - DI^-|}{DI^+ + DI^-}$ encounters division by zero.

### 2.4 Signal Processing (`features/signal_processing/`)
- **Wavelet Transform (`wavelet.py`):**
  - Uses `pywt.wavedec` on trailing window of length 64.
  - Causality preserved: Only values up to $t$ are in window.
  - *Edge case:* Rows $0 \dots 62$ are filled with `NaN`.
- **Singular Spectrum Analysis (`ssa.py`):**
  - Uses trajectory matrix of dimension $L=10$ on trailing window 40.
  - SVD extracts rank-1 component.
  - *Edge case:* Rows $0 \dots 39$ are `NaN`.
- **Kalman Filter (`kalman.py`):**
  - Forward 1-step recursion:
    $$x_{t|t-1} = x_{t-1|t-1}, \quad P_{t|t-1} = P_{t-1|t-1} + Q$$
    $$v_t = y_t - x_{t|t-1}, \quad F_t = P_{t|t-1} + R$$
    $$K_t = P_{t|t-1} / F_t, \quad x_{t|t} = x_{t|t-1} + K_t v_t, \quad P_{t|t} = (1 - K_t) P_{t|t-1}$$
  - *Edge case:* Fixed $Q = 10^{-5}, R = 10^{-3}$. No `NaN` values produced; recursion starts at $t=0$ using $y_0$.

---

## 3. Warmup Periods, Lag Alignment, and Missing Values

Because many features require historical lookback windows, every feature generates an initial block of `NaN` values:

| Module / Feature | Warmup Period (Rows) | Earliest Valid Index |
|---|---|---|
| Returns (`simple_return`, `log_return`) | 1 row | Index 1 |
| Normalized Price / Volume | 19 rows | Index 19 |
| Stochastic Oscillator | 13 rows ($K$), 15 rows ($D$) | Index 15 |
| RSI(14), ATR(14), ADX(14) | 13 to 27 rows (due to double smoothing) | Index 27 |
| Bollinger Bands, Volatility, Momentum(20) | 19 rows | Index 19 |
| SSA (`ssa_trend`) | 39 rows | Index 39 |
| Momentum(60), Market Regime(60), Correlations(60) | 59 rows | Index 59 |
| Wavelet Transform (`wavelet_approximation`) | 63 rows | Index 63 |

> [!WARNING]
> **Pipeline Warmup Requirement:**  
> When combining all feature modules into a unified matrix, the composite warmup period is **64 trading days**. Any dataset passed to the model must drop the first 64 rows, or all rows prior to index 64 will contain missing values.

---

## 4. Leakage and Causality Audit

### 4.1 Chronological Splitting
- **Finding:** Clean. `ChronologicalDataSplitter` partitions data chronologically (70/15/15) without shuffling.

### 4.2 Standard Normalization
- **Finding:** Clean. `TrainOnlyStandardScaler` enforces that fitting only occurs on `split_name='train'`. Transforms on validation/test use frozen statistics ($\mu_{train}, \sigma_{train}$).

### 4.3 Signal Processing (WT and SSA) Full-Series vs. Window Leakage
- **Crucial Question:** *Did WT or SSA decompose the complete series all at once across train, validation, and test?*
- **Finding:** **NO FULL-SERIES DECOMPOSITION DETECTED.**
- **Verification:** Both `WaveletFeature` and `SSAFeature` were implemented using **strictly trailing rolling windows** (`segment = signal[end - window + 1 : end + 1]`). Future observations $t+1, t+2 \dots$ do not enter the decomposition of row $t$.
- **Empirical Check:** Verified by `SignalProcessingCausalityChecker.check()`, which perturbed future prices by $\times 1.137$ and confirmed that historical features through row $t$ remained bit-for-bit identical ($10^{-10}$ tolerance).

### 4.4 Live External Network Calls (Risk of Nondeterminism)
- **Finding:** **POTENTIAL LEAKAGE & REPRODUCIBILITY HAZARD.**
- In `features/tier3/cross_asset.py`, `RelativeStrengthFeature.compute()` will call `yf.download('SPY')` directly from Yahoo Finance if pre-fetched SPY data is not injected.
- **Risk:** If run on different dates without pinning, Yahoo Finance historical dividend adjustments can retroactively alter past SPY prices, causing historical feature drift.

---

## 5. Research Contribution & Literature Comparison

The project specification claims several "novel attributes" as core research contributions. Here is the objective academic assessment comparing each feature against established literature:

### 5.1 Claim: "Novel Multi-Scale Signal Processing (WT, SSA, Kalman)"
- **Literature Reality:**
  - Daubechies Wavelet decomposition of financial time series has been widely published since Ramsey (2002) and Mallat (1999).
  - Trailing Singular Spectrum Analysis (SSA) has been standard in econometric signal extraction since Golyandina et al. (2001).
  - Kalman filtering for stock trend and state estimation dates to Hamilton (1994).
- **Assessment:** **ESTABLISHED PRIOR WORK.** The implementations are correct, causal engineering adaptations of well-known signal processing techniques, not new mathematical discoveries.

### 5.2 Claim: "Novel Momentum, Volatility, and Pressure Features"
- **Literature Reality:**
  - Code contains standard percentage return $P_t / P_{t-k} - 1$ (Levy, 1967; Jegadeesh & Titman, 1993) and standard rolling standard deviation of returns.
  - Price pressure and volume pressure features (such as Kyle's $\lambda$, Chaikin Money Flow, or order-imbalance indicators) **do not exist in the code**.
- **Assessment:** **ZERO NOVELTY IN CURRENT CODE.** The implemented features are textbook financial basics; the claimed pressure features were never written.

### 5.3 Claim: "Market-Regime Awareness"
- **Literature Reality:**
  - Classifying market regimes by rolling return and rolling volatility is standard heuristic partitioning (similar to Hamilton's Markov switching simplifications).
- **Assessment:** **ESTABLISHED PRACTITIONER HEURISTIC.** Useful for conditional gating, but not a novel theoretical model.

### 5.4 Claim: "Cross-Asset Context & Dynamic Sector Peer Correlations"
- **Literature Reality:**
  - Rolling correlation with broad market index (SPY) and sector ETFs is standard multi-factor / market model context (Sharpe, 1964; Fama-French, 1993).
  - Dynamic top-$k$ rolling peer correlation within sector is a solid, practical feature engineering design.
- **Assessment:** **VALUABLE PRACTICAL FEATURE ENGINEERING.** While conceptually standard in quantitative portfolio management, dynamically ranking top-$k$ peers per timestamp is a well-implemented feature for temporal networks.

---

## 6. Audit Conclusion on Features

1. **Which features reach the model today?**
   - In `baselines/__init__.py`, only `y_train` (simple return) and `X_tier1` (`simple_return`, `normalized_close`, `normalized_volume`) are consumed by `LinearRegressionBaseline` and `RidgeRegressionBaseline`.
   - **All 30+ other features (RSI, MACD, BB, Stochastic, ATR, ADX, OBV, Momentum, Volatility, Market Regime, Relative Strength, Sector Correlation, Peer Correlations, Wavelet, SSA, Kalman) ARE COMPLETELY UNUSED BY ANY MODEL.**
2. **What must be done:**
   - Resolve the 12 failing tests in `tier2/test_tier2_features.py` by supporting config kwargs in constructors.
   - Synchronize output feature names between feature modules and `ablation_plan.json`.
   - Implement genuine price pressure and volume pressure attributes.
   - Build the sliding-window tensor generator that feeds all 40 features into the DCNN model.
