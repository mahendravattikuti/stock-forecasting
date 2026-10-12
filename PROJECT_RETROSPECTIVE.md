# Stock Forecasting System — Project Retrospective (Phases 1–15)

**Date of Audit:** October 12, 2026  
**Repository:** `mahendravattikuti/stock-forecasting` (`c:\Users\ASUS\stock optimizer`)  
**Auditor:** Antigravity (Advanced Agentic AI Senior Auditor)  
**Status Overview:** Stage 1 Foundation Partially Built; Core Deep Learning & Metaheuristic Optimization (DCNN, Attention, IJF-F) **NOT IMPLEMENTED**.

---

## 1. Executive Reconstruction of Development History

### 1.1 Git Commit Chronology
The repository's Git commit history (`.git/logs/HEAD`) reveals 5 major commits:

1. **Commit 1 (`c16acfe6`):** `Initial commit: Project setup with specifications and Phase 1-2 implementation`
   - Established directory structure, `master_config.json`, `requirements.txt`, `config/config_loader.py`, `utils/reproducibility.py`, `utils/logging_config.py`.
   - Built data acquisition adapters (`base_adapter.py`, `iex_adapter.py`, `yfinance_adapter.py`, `acquisition_coordinator.py`, `symbol_registry.py`).
2. **Commit 2 (`6a9a55ba`):** `Complete Phase 3: Data Cleaning & Validation (10/10 tasks)`
   - Implemented `detectors.py`, `correctors.py`, `adjusters.py`, `cleaner.py` under `preprocessing/data_cleaning/`.
3. **Commit 3 (`4381b403`):** `Complete Phase 4: Data Quality Validation (4/4 tasks)`
   - Implemented `validators.py` and `verify_phase4.py`.
4. **Commit 4 (`5eab959c`):** `Complete Phase 5: Feature Engineering Infrastructure (5/5 tasks)`
   - Implemented `base_features.py`, `feature_orchestrator.py`, `feature_validator.py`.
5. **Commit 5 (`8047d4e2`):** `Implement forecasting phases 7 through 14`
   - Added `tier1/` (returns, normalized prices), `tier2/` (technical indicators), `tier3/` (regime, cross-asset), `signal_processing/` (wavelet, ssa, kalman, causality), `cross_asset/`, `preprocessing/data_splitter.py`, `preprocessing/artifact_manager.py`, `baselines/` (ARIMA, Linear, Ridge, Random Walk, Historical Mean), and `evaluation/` (metrics, confidence intervals).
6. **Uncommitted Working Tree State:**
   - `ablation/ablation_framework.py`, `ablation/ablation_reporter.py`, `ablation_plan.json`.

### 1.2 The Gap Between Specification Claims and Source Code Reality
A critical disconnect was uncovered between what the project documentation and task files describe vs. what was actually implemented in Python code:

- **The Specification Roadmap (`.kiro/specs/stock-forecasting-system/tasks.md`):** This roadmap defined 20 phases focused strictly on "Stage 1: Dataset + Cleaning + Feature Engineering + Classical Baselines".
- **The Research Proposal Title:** *"Regime-Aware Multi-Scale Deep Stock Forecasting with WT, SSA, Kalman Filtering, Novel Market Attributes, Attention, and IJF-F Optimization"*.
- **The Actual Repository Code:**
  - **DCNN Architecture:** **0 lines of code**. No `models/` directory exists.
  - **Temporal Attention:** **0 lines of code**. No attention mechanism exists.
  - **IJF-F Metaheuristic:** **0 lines of code**. No optimization code exists.
  - **Price / Volume Pressure Features:** **0 lines of code**. Not found anywhere in the codebase.
  - **Target Generation:** No dedicated target generation module.
  - **Real Datasets & Saved Models:** `results/` subdirectories (`baseline_models`, `cleaning_reports`, `features_manifests`, `reports`, `splits_metadata`, `visualizations`) are completely empty. No stock data CSVs, model weights, or serialized checkpoints exist on disk.

---

## 2. Phase-by-Phase Retrospective (Phases 1 through 15)

Each phase is audited against the user's specific 15-phase review roadmap:

```
Status Taxonomy:
- VERIFIED WORKING: Code exists, executed, tested, inputs/outputs verified.
- IMPLEMENTED BUT UNTESTED: Code exists, but not executed end-to-end or lacks test coverage.
- PARTIALLY IMPLEMENTED: Incomplete logic, missing sub-modules, or broken configurations.
- BROKEN: Code exists but contains critical syntax/runtime errors or failing tests.
- NOT IMPLEMENTED: Code does not exist in the repository.
- BLOCKED BY MISSING INFORMATION: Cannot proceed without external specifications/equations.
```

---

### Phase 1: Dataset Loading and Cleaning
- **Original Objective:** Acquire 10+ years of daily OHLCV stock market data from IEX Cloud with yfinance fallback, detect anomalies, forward-fill missing values (max 2 days), correct OHLC violations, adjust for stock splits/dividends, and generate quality audit reports.
- **Files Created/Modified:**
  - `preprocessing/data_acquisition/base_adapter.py`
  - `preprocessing/data_acquisition/iex_adapter.py`
  - `preprocessing/data_acquisition/yfinance_adapter.py`
  - `preprocessing/data_acquisition/acquisition_coordinator.py`
  - `preprocessing/data_acquisition/symbol_registry.py`
  - `preprocessing/data_cleaning/detectors.py`
  - `preprocessing/data_cleaning/correctors.py`
  - `preprocessing/data_cleaning/adjusters.py`
  - `preprocessing/data_cleaning/validators.py`
  - `preprocessing/data_cleaning/cleaner.py`
- **Implementation:**
  - `AcquisitionCoordinator` attempts primary fetch from `IEXAdapter` (with exponential backoff) and falls back to `YFinanceAdapter`.
  - `DataCleaner` chains `MissingValueDetector`, `SpikeDetector`, `OHLCValidator`, `ForwardFillCorrector`, `OHLCCorrector`, `SpikeCorrector`, `SplitDividendAdjuster`, and `DataQualityValidator`.
  - Generates `CleaningReport` and aggregates `AuditTrail`.
- **Inputs and Outputs:**
  - Input: Symbol string (`AAPL`), Date range, or raw OHLCV DataFrame `[Date, Open, High, Low, Close, Volume]`.
  - Output: Cleaned DataFrame `[Date, Open, High, Low, Close, Volume]` and JSON serializable `CleaningReport`.
- **Configuration:** `master_config.json` (`data_acquisition`, `data_cleaning`). `forward_fill_max_days=2`, `spike_detection_threshold=0.20`, `min_trading_days=2500`, `quality_threshold_completeness=0.99`.
- **Dependencies:** `pandas`, `numpy`, `requests`, `yfinance`.
- **Execution Status:** Individual component test scripts (`test_acquisition.py`, `test_cleaner.py`, `test_data_quality.py`) were run by previous agents. Never executed end-to-end across a full portfolio; `results/cleaning_reports/` is empty.
- **Test Status:** Component tests pass.
- **Results:** Synthetic/mock test results only. No real cleaned stock CSVs saved on disk.
- **Problems:**
  - `SplitDividendAdjuster` attempts live network calls to yfinance during cleaning rather than operating on pre-cached corporate actions.
  - No disk caching of downloaded raw data in `acquisition_coordinator.py`.
- **Dependencies on Earlier Phases:** None (initial phase).
- **Next Action:** Build an offline data download & caching CLI script to persist raw and cleaned datasets to disk.
- **Status:** **PARTIALLY IMPLEMENTED**

---

### Phase 2: Target Generation
- **Original Objective:** Generate forward-looking forecast targets (e.g. next-day close $Close_{t+1}$, 1-day return $r_{t+1} = \frac{Close_{t+1} - Close_t}{Close_t}$, or directional classification label) with strict forward shifting ($t \to t+1$) to ensure zero look-ahead bias.
- **Files Created/Modified:** None. No dedicated `target_generator.py` or `targets/` module exists.
- **Implementation:**
  - Only implicit targets exist: `features/tier1/returns.py` computes *contemporaneous* returns $r_t = \frac{Close_t - Close_{t-1}}{Close_{t-1}}$.
  - `baselines/__init__.py` expects the caller to pass pre-sliced `y_train`, `y_validation`, and `y_test` arrays, but does not construct them.
- **Inputs and Outputs:** Undefined.
- **Configuration:** No target configuration exists in `master_config.json`.
- **Dependencies:** None.
- **Execution Status:** Never executed as a target pipeline.
- **Test Status:** No tests exist for target generation.
- **Results:** None.
- **Problems:** **CRITICAL RISK OF DATA LEAKAGE.** If a developer feeds `features['simple_return']` as the regression target without a 1-step negative shift (`shift(-1)`), the model will predict *yesterday's* return from today's features (or contemporary return), completely invalidating forecasting claims.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned close prices.
- **Next Action:** Implement a dedicated `preprocessing/target_builder.py` that computes $y_t = \frac{Close_{t+1} - Close_t}{Close_t}$ (1-day forward return) and binary direction $y_t \in \{0, 1\}$, dropping the final unobservable row.
- **Status:** **NOT IMPLEMENTED**

---

### Phase 3: Train/Validation/Test Splitting
- **Original Objective:** Split time series chronologically into Train (70%), Validation (15%), and Test (15%) splits without shuffling, enforce identical calendar cutoffs across multi-symbol portfolios, and fit preprocessing scalers strictly on training data.
- **Files Created/Modified:**
  - `preprocessing/data_splitter.py`
  - `preprocessing/test_data_splitter.py`
  - `preprocessing/artifact_manager.py`
  - `preprocessing/test_artifact_manager.py`
- **Implementation:**
  - `ChronologicalDataSplitter` derives cutoffs from the union of all timestamps: `train_mask = dates <= train_end`, `val_mask = (dates > train_end) & (dates <= val_end)`, `test_mask = dates > val_end`.
  - `verify_no_leakage()` strictly checks monotonic timestamps, lack of NaT, zero date overlaps, and proper chronological ordering.
  - `TrainOnlyStandardScaler` in `artifact_manager.py` refuses to fit unless `split_name == 'train'`. Transforms on validation/test use frozen training parameters.
- **Inputs and Outputs:**
  - Input: DataFrame or `Dict[str, DataFrame]` with `DatetimeIndex`.
  - Output: `{'train': df_train, 'validation': df_val, 'test': df_test}`, and `split_metadata.json`.
- **Configuration:** `master_config.json` (`data_splitting`: train 0.70, val 0.15, test 0.15).
- **Dependencies:** `pandas`, `numpy`, `sklearn`, `joblib`.
- **Execution Status:** Executed in unit tests.
- **Test Status:** 8/8 tests passed in `test_data_splitter.py`; 15/15 passed across `test_artifact_manager.py` and `test_data_splitter.py`.
- **Results:** Split metadata schema verified. `results/splits_metadata/` is empty on disk.
- **Problems:** Signal processing modules (WT, SSA) are currently designed to run on the whole series unless explicitly partitioned first.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned data.
- **Next Action:** Connect the splitter directly to the feature generation and model pipeline.
- **Status:** **VERIFIED WORKING**

---

### Phase 4: Baseline DCNN
- **Original Objective:** Implement a Deep Convolutional Neural Network (DCNN) architecture with 1D dilated or standard convolutions, skip connections, batch normalization, and dropout to serve as the deep learning baseline.
- **Files Created/Modified:** None.
- **Implementation:** **DOES NOT EXIST.** There is no neural network code anywhere in the repository.
- **Inputs and Outputs:** Undefined.
- **Configuration:** No DCNN configuration parameters exist in `master_config.json`.
- **Dependencies:** `tensorflow` is pinned in `requirements.txt` (2.13.0), but never imported in any model file.
- **Execution Status:** Never executed.
- **Test Status:** No tests exist.
- **Results:** None.
- **Problems:** Core research deliverable is completely missing.
- **Dependencies on Earlier Phases:** Relies on sliding window tensors from feature engineering and splitting.
- **Next Action:** Build `models/dcnn_baseline.py` in PyTorch or TensorFlow, accepting input tensor `(batch_size, window_size, num_features)` and predicting next-day return.
- **Status:** **NOT IMPLEMENTED**

---

### Phase 5: Training and Evaluation
- **Original Objective:** Establish training loop (loss function, gradient optimizer, learning rate schedule, early stopping, checkpointing) and evaluation pipeline (MAE, RMSE, MAPE, Directional Accuracy, Sharpe Ratio, Information Coefficient, and Bootstrap CIs).
- **Files Created/Modified:**
  - `baselines/base_model.py`
  - `baselines/random_walk.py`
  - `baselines/arima_model.py`
  - `baselines/linear_regression.py`
  - `baselines/ridge_regression.py`
  - `baselines/historical_mean.py`
  - `baselines/__init__.py` (`BaselineManager`)
  - `evaluation/metrics.py`
  - `evaluation/confidence_intervals.py`
- **Implementation:**
  - `EvaluationMetrics` provides all 6 evaluation metrics.
  - `BootstrapConfidenceIntervals` computes 95% paired bootstrap percentiles (1,000 resamples).
  - `BaselineManager` trains and evaluates 5 classical baselines.
  - **DCNN Training Loop:** **DOES NOT EXIST.** No neural network optimizer, no backprop, no validation early-stopping.
- **Inputs and Outputs:**
  - Inputs for baselines: `y_train, y_val, y_test`, `X_train, X_val, X_test`, `close_train, close_val, close_test`.
  - Outputs: Predictions array, metrics dictionary, saved `.joblib` models.
- **Configuration:** `master_config.json` (`baseline_models`, `evaluation`).
- **Dependencies:** `scikit-learn`, `statsmodels`, `scipy`, `numpy`, `pandas`.
- **Execution Status:** Unit tested in `baselines/test_baselines.py` and `evaluation/test_metrics.py`. Never executed on real market data.
- **Test Status:** 22/22 baseline tests passed; 29/29 evaluation tests passed.
- **Results:** Evaluated on synthetic test arrays. `results/baseline_models/` is empty.
- **Problems:** Classical models work, but the deep learning training engine does not exist.
- **Dependencies on Earlier Phases:** Relies on Phases 1, 2, and 3.
- **Next Action:** Build the training engine for deep learning models (`training/trainer.py`).
- **Status:** **PARTIALLY IMPLEMENTED** (Classical baselines verified; Deep learning training NOT IMPLEMENTED).

---

### Phase 6: Wavelet Transform (WT)
- **Original Objective:** Implement multi-scale Wavelet Transform decomposition on price series to extract approximation and detail coefficients without future data leakage.
- **Files Created/Modified:**
  - `features/signal_processing/base.py`
  - `features/signal_processing/wavelet.py`
  - `features/signal_processing/causality.py`
  - `features/signal_processing/test_signal_processing.py`
- **Implementation:**
  - `WaveletFeature`: Daubechies `db4` discrete wavelet decomposition over trailing rolling windows (window=64, level=3).
  - At each step $t \ge 63$, takes $log(Close_{t-63 \dots t})$, runs `pywt.wavedec`, isolates individual coefficients, runs `pywt.waverec`, and extracts the endpoint reconstruction at timestamp $t$.
  - Outputs: `wavelet_approximation`, `wavelet_detail_1`, `wavelet_detail_2`, `wavelet_detail_3`.
- **Inputs and Outputs:** Input OHLCV DataFrame; Output DataFrame ($N \times 4$ features, first 63 rows NaN).
- **Configuration:** `master_config.json` has `"signal_processing_enabled": false`. Configurable via module init (`wavelet='db4'`, `window=64`, `level=3`).
- **Dependencies:** `PyWavelets==1.10.0`, `numpy`, `pandas`.
- **Execution Status:** Unit tested in `test_signal_processing.py`.
- **Test Status:** Causality perturbation test passed (modifying future rows does not alter prior WT features).
- **Results:** Output verified on synthetic series.
- **Problems:**
  - Inconsistent naming: Code outputs `wavelet_detail_1..3`, but `ablation_plan.json` expects `wavelet_detail` and `wavelet_energy`.
  - In `master_config.json`, signal processing is globally disabled by default.
  - Computational cost: Rolling DWT at every bar is $O(N \cdot W \log W)$.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned close prices.
- **Next Action:** Harmonize column names with the ablation framework.
- **Status:** **VERIFIED WORKING**

---

### Phase 7: Singular Spectrum Analysis (SSA)
- **Original Objective:** Decompose time series into trend and oscillatory/residual components using Singular Spectrum Analysis without lookahead bias.
- **Files Created/Modified:**
  - `features/signal_processing/ssa.py`
  - `features/signal_processing/test_signal_processing.py`
- **Implementation:**
  - `SSAFeature`: Trailing-window SSA on log prices (window=40, embedding dimension $L=10$).
  - Constructs trajectory matrix ($10 \times 31$), performs SVD (`np.linalg.svd`), reconstructs rank-1 trend component at the current timestamp: `latest_trend = singular_values[0] * left[-1, 0] * right[0, -1]`. Residual = `segment[-1] - latest_trend`.
  - Outputs: `ssa_trend`, `ssa_residual`.
- **Inputs and Outputs:** Input OHLCV DataFrame; Output DataFrame ($N \times 2$ features, first 39 rows NaN).
- **Configuration:** `window=40`, `embedding_dimension=10`.
- **Dependencies:** `numpy`, `pandas`.
- **Execution Status:** Unit tested in `test_signal_processing.py`.
- **Test Status:** Causality perturbation test passed.
- **Results:** Verified numerically.
- **Problems:**
  - Inconsistent naming: Code outputs `ssa_trend`, `ssa_residual`, but `ablation_plan.json` expects `ssa_component_1`, `ssa_component_2`, `ssa_reconstruction`.
  - Heavy SVD computational cost when rolling over large datasets.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned close prices.
- **Next Action:** Align output column names with ablation plan.
- **Status:** **VERIFIED WORKING**

---

### Phase 8: Kalman Filter
- **Original Objective:** Recursive state estimation to smooth price series and extract innovation dynamics while fitting noise parameters on training data only.
- **Files Created/Modified:**
  - `features/signal_processing/kalman.py`
  - `features/signal_processing/test_signal_processing.py`
- **Implementation:**
  - `KalmanFilterFeature`: 1D local-level state space filter on log prices.
  - Forward recursion updates level estimate $x_t$, innovation $v_t$, innovation variance $F_t$, Kalman gain $K_t$, and posterior variance $P_t$.
  - Outputs: `kalman_level`, `kalman_innovation_zscore`, `kalman_variance`.
- **Inputs and Outputs:** Input OHLCV DataFrame; Output DataFrame ($N \times 3$ features).
- **Configuration:** `process_variance=1e-5`, `measurement_variance=1e-3`.
- **Dependencies:** `numpy`, `pandas`.
- **Execution Status:** Unit tested in `test_signal_processing.py`.
- **Test Status:** Causality perturbation test passed.
- **Results:** Verified numerically.
- **Problems:**
  - Inconsistent naming: Code outputs `kalman_level`, `kalman_innovation_zscore`, `kalman_variance`, but `ablation_plan.json` expects `kalman_state`, `kalman_smoothed`, `kalman_gain`.
  - Uses fixed hardcoded noise variances rather than estimating them from training data via maximum likelihood.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned close prices.
- **Next Action:** Add MLE parameter estimation on training split and update ablation column names.
- **Status:** **VERIFIED WORKING**

---

### Phase 9: Technical Indicators
- **Original Objective:** Implement 10+ standard technical indicators (RSI, MACD, Bollinger Bands, Stochastic Oscillator, ATR, ADX, OBV, Momentum, Volatility) adhering to the `FeatureModule` contract.
- **Files Created/Modified:**
  - `features/tier2/technical_indicators.py`
  - `features/tier2/other_indicators.py`
  - `features/tier2/test_tier2_features.py`
- **Implementation:**
  - Implements `RSIFeature` (14), `MACDFeature` (12, 26, 9), `BollingerBandsFeature` (20, 2), `StochasticFeature` (14, 3), `ATRFeature` (14), `ADXFeature` (14), `OBVFeature`, `MomentumFeature` (5, 20, 60), `VolatilityFeature` (20).
- **Inputs and Outputs:** Input OHLCV DataFrame; Outputs individual indicator DataFrames (total 17 feature columns).
- **Configuration:** Default parameters hardcoded inside class initializers.
- **Dependencies:** `pandas`, `numpy`.
- **Execution Status:** Executed in `features/tier2/test_tier2_features.py`.
- **Test Status:** **BROKEN (36/48 passed, 12 failed).**
  - Why tests failed: Classes like `RSIFeature` and `BollingerBandsFeature` ignore dictionary configuration overrides in `__init__` (e.g. `config={'rsi_period': 7}` is ignored, keeping `self.period = 14`).
- **Results:** Indicator formulas produce mathematically correct values for default parameters.
- **Problems:**
  - 12 failing tests due to unhandled constructor kwargs.
  - Column name discrepancies: code produces `bb_upper`, `bb_lower`, `bb_width`, but `ablation_plan.json` expects `bollinger_upper`, `bollinger_lower`, `bollinger_bandwidth`.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned OHLCV data.
- **Next Action:** Fix `__init__` in `technical_indicators.py` to accept custom config parameters and harmonize column naming.
- **Status:** **BROKEN**

---

### Phase 10: Novel Momentum, Volatility, and Pressure Features
- **Original Objective:** Implement novel, research-grade momentum, volatility, price pressure, and volume pressure features that advance beyond standard technical indicators.
- **Files Created/Modified:**
  - `features/tier2/other_indicators.py`
- **Implementation:**
  - Contains ONLY standard, textbook momentum: `(Close / Close.shift(p)) - 1` for $p \in \{5, 20, 60\}$.
  - Contains ONLY standard, textbook volatility: `returns.rolling(20).std()`.
  - **Price Pressure Features:** **NOT IMPLEMENTED.** (0 lines of code).
  - **Volume Pressure Features:** **NOT IMPLEMENTED.** (0 lines of code).
  - **Novel Multi-Horizon or Order-Flow Momentum:** **NOT IMPLEMENTED.**
- **Inputs and Outputs:** Outputs `momentum_5`, `momentum_20`, `momentum_60`, and `volatility_20`.
- **Configuration:** Window sizes 5, 20, 60.
- **Dependencies:** `pandas`, `numpy`.
- **Execution Status:** Executed in test suites.
- **Test Status:** Standard momentum and volatility tests pass.
- **Results:** Only standard return metrics computed.
- **Problems:** **FALSE RESEARCH NOVELTY CLAIM.** The codebase claims "novel momentum, volatility, and pressure features", but no novel feature definitions or pressure attributes exist anywhere in the code.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned data.
- **Next Action:** Formulate and implement explicit price/volume pressure indicators (e.g., Buying/Selling Pressure Ratio, Intraday Intensity Index, Volume-Weighted Spread Pressure).
- **Status:** **PARTIALLY IMPLEMENTED** (Standard features exist; Novel attributes NOT IMPLEMENTED).

---

### Phase 11: Market-Regime Features
- **Original Objective:** Classify market conditions into distinct regimes (bearish, sideways, bullish, high-volatility) to provide regime awareness to forecasting models.
- **Files Created/Modified:**
  - `features/tier3/regime.py`
  - `features/cross_asset/cross_asset_features.py`
  - `features/tier3/test_tier3_features.py`
- **Implementation:**
  - `MarketRegimeFeature`: Classifies 60-day rolling return and 60-day rolling volatility into 4 discrete regimes:
    - 3: High-volatility ($vol > 0.05$)
    - 2: Bullish ($ret > 0.02$, normal vol)
    - 0: Bearish ($ret < -0.02$, normal vol)
    - 1: Sideways ($|ret| \le 0.02$, normal vol)
  - `CrossAssetFeatureComputer`: Computes SPY-based market regime and annualized volatility.
- **Inputs and Outputs:** Input Close series; Output single integer column `market_regime` $\in \{0, 1, 2, 3\}$.
- **Configuration:** `lookback_period=60`, `volatility_threshold=0.05`, `return_threshold=0.02`.
- **Dependencies:** `pandas`, `numpy`.
- **Execution Status:** Executed in unit tests.
- **Test Status:** 18/18 tests passed in `test_tier3_features.py`.
- **Results:** Categorical classifications verified.
- **Problems:**
  - In `regime.py`, regime is derived from the *individual stock's own close price* rather than the broad market (SPY), misrepresenting stock momentum as "market" regime unless called through `CrossAssetFeatureComputer`.
  - Integer encoding $\{0, 1, 2, 3\}$ cannot be fed raw into DCNN; requires one-hot encoding.
- **Dependencies on Earlier Phases:** Relies on Phase 1 cleaned data.
- **Next Action:** Add one-hot encoding option and ensure SPY is strictly used for broad market regime.
- **Status:** **VERIFIED WORKING**

---

### Phase 12: Relative-Market, Sector, and Cross-Asset Features
- **Original Objective:** Extract cross-asset contextual features: rolling correlation with S&P 500 (SPY), correlation with sector ETFs (e.g. XLK, XLF), and dynamic peer correlations.
- **Files Created/Modified:**
  - `features/tier3/cross_asset.py`
  - `features/cross_asset/market_data_manager.py`
  - `features/cross_asset/cross_asset_features.py`
  - `features/cross_asset/test_cross_asset_features.py`
- **Implementation:**
  - `RelativeStrengthFeature`: 60-day rolling correlation of stock returns with SPY returns.
  - `SectorCorrelationFeature`: 60-day rolling correlation with sector ETF returns.
  - `CrossAssetFeatureComputer`: Aligns SPY, sector ETF, and peer prices using forward-fill only, computing top-5 peer correlations, peer correlation mean, and annualized market volatility.
  - Strict causality check perturbs future market data and confirms historical features are unchanged.
- **Inputs and Outputs:** Target stock OHLCV + Market dictionary of DataFrames; Outputs DataFrame with 9 cross-asset feature columns.
- **Configuration:** `correlation_window=60`, `top_peers=5`, `high_volatility_threshold=0.25`.
- **Dependencies:** `pandas`, `numpy`, `yfinance`.
- **Execution Status:** Executed with mock/injected market data.
- **Test Status:** 34/34 tests passed.
- **Problems:** `RelativeStrengthFeature.compute()` falls back to live `yf.download('SPY')` if external series is not pre-injected, breaking offline determinism and risking API failures.
- **Dependencies on Earlier Phases:** Relies on Phase 1 data and `SymbolRegistry`.
- **Next Action:** Enforce local offline caching so `compute()` never calls external APIs directly.
- **Status:** **VERIFIED WORKING**

---

### Phase 13: Feature Selection
- **Original Objective:** Implement algorithmic feature selection (e.g., Boruta, LASSO/ElasticNet penalty, mutual information, or metaheuristic selection) to reduce feature space and eliminate collinear attributes.
- **Files Created/Modified:**
  - `features/feature_orchestrator.py` (Contains manual registry flags only).
- **Implementation:** **DOES NOT EXIST.**
  - `FeatureRegistry` allows manual toggling (`enable_feature`, `disable_feature`, `enable_group`), but there is NO automated feature selection algorithm, importance ranking, or dimensionality reduction pipeline.
- **Inputs and Outputs:** None.
- **Configuration:** No feature selection configuration exists.
- **Dependencies:** None.
- **Execution Status:** Never executed.
- **Test Status:** No tests exist.
- **Results:** None.
- **Problems:** Missing component.
- **Dependencies on Earlier Phases:** Relies on all feature engineering tiers (Phases 6–12).
- **Next Action:** Implement a feature selector module (`features/feature_selector.py`) implementing Mutual Information and Lasso/ElasticNet CV selection.
- **Status:** **NOT IMPLEMENTED**

---

### Phase 14: Temporal Attention
- **Original Objective:** Implement a temporal attention layer to dynamically weigh historical timestamps within sliding windows for improved predictive performance and explainability.
- **Files Created/Modified:** None.
- **Implementation:** **DOES NOT EXIST.** No attention mechanisms, no self-attention, and no temporal query-key-value layers exist in the repository.
- **Inputs and Outputs:** Undefined.
- **Configuration:** No attention parameters in `master_config.json`.
- **Dependencies:** None.
- **Execution Status:** Never executed.
- **Test Status:** No tests exist.
- **Results:** None.
- **Problems:** Core research contribution from the project title is completely missing.
- **Dependencies on Earlier Phases:** Relies on Phase 4 DCNN feature maps.
- **Next Action:** Implement `models/attention.py` with Temporal Additive or Scaled Dot-Product Attention.
- **Status:** **NOT IMPLEMENTED**

---

### Phase 15: IJF-F Optimization
- **Original Objective:** Implement the Improved Jellyfish Search with Firefly (IJF-F) hybrid metaheuristic optimization algorithm to optimize model hyperparameters or weights/biases.
- **Files Created/Modified:** None.
- **Implementation:** **DOES NOT EXIST.** There is no optimization algorithm, metaheuristic search, swarm solver, or firefly algorithm anywhere in the codebase.
- **Inputs and Outputs:** Undefined.
- **Configuration:** No IJF-F parameters exist.
- **Dependencies:** None.
- **Execution Status:** Never executed.
- **Test Status:** No tests exist.
- **Results:** None.
- **Problems:** Core metaheuristic algorithm from the project title is completely absent.
- **Dependencies on Earlier Phases:** Relies on training loss and model architecture.
- **Next Action:** Obtain source equations for IJF-F, formulate representation (hyperparameter bounds or weight vectors), and implement `optimization/ijf_f_optimizer.py`.
- **Status:** **NOT IMPLEMENTED**

---

## 3. Summary Scorecard (Phases 1–15)

| Phase | Description | Actual Status | Evidence in Workspace |
|---|---|---|---|
| **Phase 1** | Dataset loading and cleaning | **PARTIALLY IMPLEMENTED** | Adapters & cleaning classes exist; results empty; no offline CLI |
| **Phase 2** | Target generation | **NOT IMPLEMENTED** | No target builder; contemporaneous returns exist, no forward shift |
| **Phase 3** | Train/val/test splitting | **VERIFIED WORKING** | `data_splitter.py` & `artifact_manager.py` pass 23 unit tests |
| **Phase 4** | Baseline DCNN | **NOT IMPLEMENTED** | No `models/` directory; 0 lines of neural network code |
| **Phase 5** | Training and evaluation | **PARTIALLY IMPLEMENTED** | Classical baselines & bootstrap metrics work; DL loop missing |
| **Phase 6** | Wavelet Transform | **VERIFIED WORKING** | Causal trailing Daubechies DWT; passes perturbation tests |
| **Phase 7** | Singular Spectrum Analysis | **VERIFIED WORKING** | Trailing SVD rank-1 reconstruction; passes perturbation tests |
| **Phase 8** | Kalman Filter | **VERIFIED WORKING** | 1D local level filter; passes perturbation tests |
| **Phase 9** | Technical indicators | **BROKEN** | 10 indicators coded, but 12 tests fail due to config handling |
| **Phase 10** | Novel momentum/vol/pressure | **PARTIALLY IMPLEMENTED** | Standard momentum/vol exist; Novel & pressure features absent |
| **Phase 11** | Market-regime features | **VERIFIED WORKING** | 4-state regime classifier passes 18 unit tests |
| **Phase 12** | Cross-asset features | **VERIFIED WORKING** | SPY & sector ETF rolling correlations pass 34 unit tests |
| **Phase 13** | Feature selection | **NOT IMPLEMENTED** | Only manual registry flags exist; no automated algorithm |
| **Phase 14** | Temporal attention | **NOT IMPLEMENTED** | 0 lines of attention code |
| **Phase 15** | IJF-F optimization | **NOT IMPLEMENTED** | 0 lines of metaheuristic code |

---

## 4. End-to-End Data Flow Trace (The Real vs. Intended System)

### 4.1 How a Sample Flows Through the Code Today
If an engineer attempts to trace one stock (`AAPL`) through the system today, here is the exact execution reality:

```
[1. Raw yfinance / IEX Data]
         │  DataFrame: Date index, OHLCV
         ▼
[2. DataCleaner (cleaner.py)]
         │  Detects gaps & spikes; forward-fills max 2 days; checks OHLC.
         │  Output: Cleaned OHLCV DataFrame
         ▼
[3. Feature Generation (Isolated Modules)]
         ├─ ReturnsFeature: simple & log returns
         ├─ NormalizedPricesFeature: MA20, STD20, normalized close & volume
         ├─ TechnicalIndicators: RSI, MACD, BB, Stoch, ATR, ADX, OBV
         ├─ OtherIndicators: Momentum (5,20,60), Volatility (20)
         ├─ SignalProcessing: Wavelet, SSA, Kalman (Optional)
         └─ CrossAssetFeatureComputer: SPY/Sector correlation
         ▼
[4. Feature Concatenation]
         │  FeatureOrchestrator._initialize_modules() is an EMPTY STUB.
         │  User must manually instantiate and register all 12 modules.
         ▼
[5. ChronologicalDataSplitter (data_splitter.py)]
         │  Splits into Train (70%), Val (15%), Test (15%) by calendar cutoffs.
         ▼
[6. TrainOnlyStandardScaler (artifact_manager.py)]
         │  Fits scaler on train split; transforms val & test splits.
         ▼
        ╔═══════════════════════════════════════════════════════════╗
        ║                  DISCONNECTION CLIFF                      ║
        ╚═══════════════════════════════════════════════════════════╝
         │
         ├──► Target Generation: MISSING. (No forward-shifted target $y_{t+1}$).
         ├──► Sliding Window Tensor Creation: MISSING. (No 3D tensor batching).
         ├──► DCNN Model: MISSING. (Cannot train neural network).
         ├──► Temporal Attention: MISSING. (Cannot apply attention).
         ├──► IJF-F Optimizer: MISSING. (Cannot optimize parameters).
         │
         ▼
[Alternative Path: BaselineManager (baselines/__init__.py)]
         │  Caller manually provides contemporaneous returns as y.
         │  Trains Random Walk, ARIMA(1,1,1), Linear Regression, Ridge Regression, Historical Mean.
         │  Evaluates MAE, RMSE, Directional Accuracy, Sharpe, IC.
         │  Saves to joblib (Tested in mock tests; never run on real data).
```

### 4.2 Disconnected Modules and Inert Settings
1. **Empty Feature Orchestrator Initialization:** In `features/feature_orchestrator.py` (lines 334–345), `_initialize_modules()` is an empty stub with a `# TODO` comment. Calling `orchestrator.compute_all_features()` without manually registering modules produces an empty DataFrame.
2. **Missing `pipeline.py`:** `README.md` instructs the user to run `python pipeline.py`, but `pipeline.py` does not exist in the repository.
3. **Inert Configuration Flags:**
   - `"signal_processing_enabled": false` in `master_config.json`: Never read by any pipeline script because no pipeline script exists.
   - `"ablation_studies": {"enabled": false}`: Never referenced by any execution script.
   - `"model_parameters"`: Absent from `master_config.json`.
4. **Column Name Inconsistencies:**
   - `features/tier2/technical_indicators.py` outputs `bb_upper`, `bb_middle`, `bb_lower`, `bb_width`. `ablation_plan.json` expects `bollinger_upper`, `bollinger_lower`, `bollinger_bandwidth`.
   - `features/signal_processing/wavelet.py` outputs `wavelet_detail_1..3`. `ablation_plan.json` expects `wavelet_detail`, `wavelet_energy`.
   - `features/signal_processing/ssa.py` outputs `ssa_trend`, `ssa_residual`. `ablation_plan.json` expects `ssa_component_1`, `ssa_component_2`, `ssa_reconstruction`.
   - `features/signal_processing/kalman.py` outputs `kalman_level`, `kalman_innovation_zscore`, `kalman_variance`. `ablation_plan.json` expects `kalman_state`, `kalman_smoothed`, `kalman_gain`.
5. **Live Network Leak in Offline Features:** `RelativeStrengthFeature.compute()` invokes `yf.download('SPY')` if external series is not pre-passed, which introduces nondeterministic network latency and breaks reproducible offline runs.
