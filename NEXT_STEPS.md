# Stock Forecasting System — Dependency and Readiness Report (`NEXT_STEPS.md`)

**Date:** October 12, 2026  
**Auditor:** Antigravity  
**Repository:** `c:\Users\ASUS\stock optimizer`  

---

## 1. Critical Bugs (Must Be Fixed First)

1. **Constructor Config Handling in Tier-2 Technical Indicators (`features/tier2/technical_indicators.py`):**
   - **Bug:** `RSIFeature`, `BollingerBandsFeature`, and other indicator initializers hardcode their parameters (`self.period = 14`, etc.) and completely ignore the `config` dictionary passed to `__init__`.
   - **Impact:** 12 unit tests in `test_tier2_features.py` fail immediately whenever custom periods are passed.
   - **Fix:** Update all classes in `technical_indicators.py` to unpack parameters from `config` with fallbacks:
     ```python
     self.period = int(self.config.get('rsi_period', self.config.get('period', 14)))
     ```

2. **Severe Feature Name Discrepancy with Ablation Plan (`ablation_plan.json`):**
   - **Bug:** The feature column names produced by the active feature modules do not match the column names defined in `ablation_plan.json` and `ablation/ablation_framework.py`:
     - Code produces `bb_upper, bb_lower, bb_width` $\leftrightarrow$ Plan expects `bollinger_upper, bollinger_lower, bollinger_bandwidth`.
     - Code produces `wavelet_detail_1..3` $\leftrightarrow$ Plan expects `wavelet_detail, wavelet_energy`.
     - Code produces `ssa_trend, ssa_residual` $\leftrightarrow$ Plan expects `ssa_component_1, ssa_component_2, ssa_reconstruction`.
     - Code produces `kalman_level, kalman_innovation_zscore, kalman_variance` $\leftrightarrow$ Plan expects `kalman_state, kalman_smoothed, kalman_gain`.
   - **Impact:** Any ablation run attempting to mask out these feature groups will fail to find the columns, rendering the ablation framework useless.
   - **Fix:** Align `ablation_plan.json` and `ablation/ablation_framework.py` to use the actual feature names produced by the signal processing and indicator modules.

3. **Live Network Calls Inside Feature Computation (`features/tier3/cross_asset.py`):**
   - **Bug:** If `RelativeStrengthFeature.compute()` is called without pre-injected SPY data, it executes a live `yf.download('SPY')` call.
   - **Impact:** Breaks offline execution, introduces network flakiness, slows down training, and risks Yahoo Finance rate limits or retroactively adjusted prices.
   - **Fix:** Mandate that all external market data be pre-loaded and cached by `MarketDataManager`, raising a deterministic `ValueError` if required data is missing.

4. **Empty Feature Orchestrator Initialization (`features/feature_orchestrator.py`):**
   - **Bug:** `_initialize_modules()` is an empty stub with `# TODO: Instantiate actual feature modules here`.
   - **Impact:** Calling `orchestrator.compute_all_features()` without manual registrations returns an empty DataFrame with 0 features.
   - **Fix:** Implement automatic instantiation and registration of all available feature modules inside `_initialize_modules()`.

---

## 2. Missing Implementations

1. **Target Generation Module (`preprocessing/target_builder.py`):**
   - Standardized target generation for next-day return ($y_t = \frac{Close_{t+1} - Close_t}{Close_t}$) and binary direction ($y_t \in \{0, 1\}$).
   - Strict temporal alignment: ensures $y_t$ aligns with features from timestamp $t$, dropping the final unobservable row.

2. **DCNN Model Architecture (`models/dcnn.py`):**
   - Deep 1D Dilated Convolutional Neural Network with residual connections, batch normalization, and dropout.
   - Accepts 3D sliding window tensor `(batch_size, window_size, num_features)`.

3. **Temporal Attention Mechanism (`models/attention.py`):**
   - Temporal attention block computing attention weights across the $T$ historical timesteps for model interpretability.

4. **Deep Learning Training Loop (`training/trainer.py`):**
   - Mini-batch data loader / generator for sliding windows.
   - Loss function (MSE, Huber Loss, or Directional Loss).
   - Adam / AdamW optimizer, learning rate scheduler, early stopping, and model checkpointing.

5. **Sliding Window Generator (`preprocessing/window_generator.py`):**
   - Converts 2D tabular features into 3D sequence tensors $(N - W + 1, W, D)$ aligned with target $y$.

6. **IJF-F Metaheuristic Optimizer (`optimization/ijf_f.py`):**
   - Implementation of the Improved Jellyfish Search with Firefly algorithm for hyperparameter optimization.

7. **Automated Feature Selection (`features/feature_selector.py`):**
   - Mutual Information or Lasso-based feature selection to filter the 40+ generated attributes down to the most predictive subset.

8. **End-to-End Execution Pipeline (`pipeline.py`):**
   - Unified runner orchestrating data acquisition, cleaning, feature extraction, splitting, tensor creation, model training, and evaluation.

---

## 3. Incorrect Assumptions in Prior Work

1. **Assumption that "Stage 1 Complete" meant the forecasting system was operational:**
   - Previous status summaries marked phases complete up to Phase 14, but this only referred to the *specification tasks* in `.kiro/specs/`, NOT the actual deep learning forecasting model.
2. **Assumption that DCNN and Attention existed:**
   - Mentions in the README and project titles led to the impression that a deep learning model was already running. The codebase currently only contains classical linear/statistical baselines.
3. **Assumption that novel pressure features were built:**
   - "Novel momentum, volatility, and pressure features" were cited, but only textbook percentage returns and rolling standard deviations exist.
4. **Assumption that experimental results had been obtained:**
   - The `results/` directories are completely empty; no real experiments have ever been executed or saved.

---

## 4. Components That Work but Need Stronger Tests

1. **`ChronologicalDataSplitter` (`preprocessing/data_splitter.py`):**
   - Unit tests pass on small synthetic frames. Needs validation on real multi-symbol universes with uneven trading calendars, holidays, and symbol inception dates.
2. **`TrainOnlyStandardScaler` (`preprocessing/artifact_manager.py`):**
   - Correctly enforces train-only fitting. Needs integration tests with the full 40-feature matrix including discrete market regime features.
3. **Wavelet & SSA Performance Scaling:**
   - Both modules perform trailing window calculations at every step. On 2,500 trading days, this performs 2,500 SVDs and DWTs per symbol. Needs benchmarking and vectorization or caching.

---

## 5. Components Ready for Experiments

1. **Data Acquisition Adapters:** `IEXAdapter` and `YFinanceAdapter` with `AcquisitionCoordinator`.
2. **Data Cleaning Pipeline:** `DataCleaner`, `MissingValueDetector`, `SpikeDetector`, `OHLCCorrector`, `ForwardFillCorrector`.
3. **Chronological Splitting & Artifact Management:** `ChronologicalDataSplitter` and `TrainOnlyStandardScaler`.
4. **Signal Processing Features:** `WaveletFeature`, `SSAFeature`, `KalmanFilterFeature` (all verified causal).
5. **Cross-Asset Features:** `CrossAssetFeatureComputer` (when market data is pre-cached).
6. **Evaluation Metrics:** `EvaluationMetrics` and `BootstrapConfidenceIntervals`.
7. **Classical Baseline Models:** `RandomWalkBaseline`, `ARIMABaseline`, `LinearRegressionBaseline`, `RidgeRegressionBaseline`, `HistoricalMeanBaseline`.

---

## 6. Components That Should Be Postponed

1. **Complex IJF-F Metaheuristic Integration:**
   - Postpone until the core DCNN baseline and training loop are fully functional and producing baseline benchmarks. Metaheuristic tuning on a non-existent or broken model is impossible.
2. **Multi-Horizon Forecasting:**
   - Keep forecast target strictly at 1-day ahead ($t+1$) until the baseline pipeline is stable.
3. **Live API Trading / Brokerage Connectors:**
   - Focus exclusively on offline research reproducibility.

---

## 7. Exact Verification Commands

Once the environment shell runner issue is resolved (or when running locally in terminal), the following exact commands should be executed to verify the test suite:

```bash
# 1. Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Run data acquisition tests
python -m pytest preprocessing/data_acquisition/test_acquisition.py -v

# 3. Run data cleaning and quality validation tests
python -m pytest preprocessing/data_cleaning/test_cleaner.py preprocessing/data_cleaning/test_data_quality.py preprocessing/data_cleaning/test_correctors.py -v

# 4. Run splitting and artifact management tests
python -m pytest preprocessing/test_data_splitter.py preprocessing/test_artifact_manager.py -v

# 5. Run Tier-1 and Tier-3 feature tests
python -m pytest features/tier1/test_tier1_features.py features/tier3/test_tier3_features.py -v

# 6. Run signal processing and causality tests
python -m pytest features/signal_processing/test_signal_processing.py features/cross_asset/test_cross_asset_features.py -v

# 7. Run classical baselines and evaluation metrics tests
python -m pytest baselines/test_baselines.py evaluation/test_metrics.py -v

# 8. Run Tier-2 tests (after fixing constructor config kwargs bug)
python -m pytest features/tier2/test_tier2_features.py -v
```

---

## 8. Recommended Next Phase & Action Plan

Before moving to Phase 16 or any advanced experimental features, we recommend executing the following **Corrective Foundation Phase**:

1. **Step 1: Fix Core Indicator & Config Bugs (Immediate)**
   - Fix `features/tier2/technical_indicators.py` constructor handling so all 48 Tier-2 tests pass.
   - Synchronize feature names in `ablation_plan.json` with actual module outputs.
   - Populate `_initialize_modules()` in `features/feature_orchestrator.py`.
2. **Step 2: Implement Target Builder & Sequence Windowing**
   - Build `preprocessing/target_builder.py` ($y_t = \frac{Close_{t+1} - Close_t}{Close_t}$) with negative shift and dropna.
   - Build `preprocessing/window_generator.py` to create 3D tensors $(N, T, D)$ for sequence models.
3. **Step 3: Implement Baseline DCNN & Training Loop**
   - Create `models/dcnn.py` with standard 1D convolutional layers, residual blocks, and regression head.
   - Create `training/trainer.py` with MSE loss, Adam optimizer, early stopping, and evaluation on validation split.
4. **Step 4: Implement Temporal Attention Layer**
   - Create `models/attention.py` and attach to DCNN feature maps.
5. **Step 5: Execute First End-to-End Benchmark Run**
   - Run data acquisition on a 5-symbol portfolio (`AAPL`, `MSFT`, `GOOGL`, `AMZN`, `TSLA`).
   - Clean, extract features, split, train classical baselines vs. DCNN vs. DCNN+Attention.
   - Save true verifiable metrics and checkpoints to `results/`.
