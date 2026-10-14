# Architecture Document - Stock Market Forecasting System

**Audience:** System architects, new team members, developers extending the system  
**Last Updated:** 2024-01-19  
**Status:** Stage 1 Complete - Data Cleaning & Feature Engineering Foundation

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level System Architecture](#high-level-system-architecture)
3. [13-Phase Pipeline Orchestration](#13-phase-pipeline-orchestration)
4. [Layer Architecture](#layer-architecture)
5. [Module Hierarchy](#module-hierarchy)
6. [Data Flow & Transformations](#data-flow--transformations)
7. [Dependency Graph](#dependency-graph)
8. [Configuration Management](#configuration-management)
9. [Error Handling & Recovery](#error-handling--recovery)
10. [Reproducibility & Artifact Management](#reproducibility--artifact-management)
11. [Testing Architecture](#testing-architecture)
12. [Performance Characteristics](#performance-characteristics)
13. [Design Patterns](#design-patterns)
14. [Extension Points](#extension-points)
15. [Frequently Modified Code](#frequently-modified-code)
16. [Technical Debt & Future Improvements](#technical-debt--future-improvements)

---

## Overview

The Stock Market Forecasting System is a modular, research-grade platform that transforms raw market data into clean, validated, feature-rich datasets for time series forecasting. The architecture prioritizes:

- **Scientific rigor** through reproducible, deterministic processing
- **Modularity** enabling independent feature development and testing
- **Data integrity** via strict chronological preservation and leakage detection
- **Extensibility** through adapter/strategy pattern usage for data sources and models
- **Transparency** with comprehensive logging, documentation, and audit trails

**Key Constraints:**
- Must maintain strict temporal order (no shuffling of chronological data)
- Must prevent data leakage (validation/test data never touch preprocessing artifacts)
- Must handle symbol-level failures without halting pipeline
- Must support feature ablation studies (tier-based feature removal)
- Must track all lineage from raw data to model inputs

---

## High-Level System Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 STOCK FORECASTING SYSTEM - COMPLETE FLOW                │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────┐
                              │  Master Config   │
                              │  + API Tokens    │
                              │  + Symbols       │
                              │  + Seeds         │
                              └────────┬─────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │  Config Loader & Validation│
                        │  (ConfigLoader)             │
                        └──────────────┬──────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │   Reproducibility Initialization    │
                    │   (Seeds, Versioning)               │
                    └──────────────────┬──────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
  ┌──────────────┐           ┌──────────────────┐        ┌────────────────┐
  │   DATA       │           │   DATA CLEANING  │        │   FEATURE      │
  │ ACQUISITION  │──────────▶│   & VALIDATION   │───────▶│  ENGINEERING   │
  │              │           │                  │        │                │
  │ - IEX Cloud  │           │ - Spike removal  │        │ - Tier-1       │
  │ - yfinance   │           │ - Gap filling    │        │ - Tier-2       │
  │ - Fallback   │           │ - OHLC checks    │        │ - Tier-3       │
  │ - Retry      │           │ - Splits/divs    │        │ - Signal Proc  │
  │ - Validation │           │ - Audit trail    │        │ - Cross-asset  │
  └──────────────┘           └──────────────────┘        └────────────────┘
        │                              │                         │
        └──────────────────────────────┼─────────────────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │   Data Splitting            │
                        │   (Chronological 70/15/15)  │
                        └──────────────┬──────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │   Preprocessing & Scaling   │
                        │   (Fit on train only)       │
                        └──────────────┬──────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
  ┌──────────────┐          ┌────────────────────┐       ┌──────────────┐
  │  BASELINE    │          │   EVALUATION &     │       │   LEAKAGE    │
  │  MODELS      │──────────▶│   METRICS          │       │  DETECTION   │
  │              │          │                    │       │              │
  │ - RW         │          │ - MAE/RMSE/MAPE   │       │ - Verify fit │
  │ - ARIMA      │          │ - Directional Acc │       │ - Check data │
  │ - LinReg     │          │ - IC / Sharpe      │       │ - Audit      │
  │ - Ridge      │          │ - Bootstrap CI     │       │   temporal   │
  │ - HistMean   │          │                    │       │   order      │
  └──────────────┘          └────────────────────┘       └──────────────┘
        │                              │                         │
        └──────────────────────────────┼─────────────────────────┘
                                       │
                        ┌──────────────▼──────────────┐
                        │   REPORTING & ARTIFACTS    │
                        │                            │
                        │ - Pipeline reports         │
                        │ - Data quality dashboard   │
                        │ - Feature distributions    │
                        │ - Reproducibility metadata │
                        │ - Lineage graph            │
                        │ - Experiment tracking      │
                        └────────────────────────────┘
```

### Context & Interactions

```
External Systems                    Stock Forecasting System
├─ IEX Cloud API                   ┌─ Acquisition Coordinator
├─ Yahoo Finance                   ├─ Data Cleaner
├─ Symbol Registry                 ├─ Feature Orchestrator
└─ Market Data (benchmarks)    ────┤─ Baseline Manager
                                   ├─ Evaluation Engine
                                   ├─ Leakage Detector
                                   └─ Report Generator
```

---

## 13-Phase Pipeline Orchestration

The pipeline executes in strict sequence with error recovery at each phase:

### Phase 1: Reproducibility Initialization
```
Goal: Ensure deterministic execution and artifact versioning

Tasks:
  ✓ Initialize random seeds (NumPy, Python random, TensorFlow)
  ✓ Create reproducibility_artifacts/ directory
  ✓ Load master_config.json with version hash
  ✓ Log environment (Python version, package versions)
  ✓ Start structured logger (console + timestamped log file)

Outputs:
  - reproducibility_manager initialized
  - logging configured
  - config validated and loaded

Failure Handling:
  - Config validation failure → HALT (critical)
  - Seed initialization failure → HALT (critical)
  - Log setup failure → Console fallback
```

### Phase 2: Component Configuration
```
Goal: Initialize all pipeline components

Tasks:
  ✓ Create IEXAdapter (primary data source)
  ✓ Create YFinanceAdapter (fallback data source)
  ✓ Create AcquisitionCoordinator (orchestrates adapters)
  ✓ Create DataCleaner (cleans raw data)
  ✓ Create DataQualityValidator (validates cleaned data)
  ✓ Create FeatureOrchestrator (computes all features)
  ✓ Create ChronologicalDataSplitter (70/15/15 split)
  ✓ Create TrainOnlyStandardScaler (fit on train only)
  ✓ Create BaselineManager (train baselines)
  ✓ Create EvaluationMetrics (compute metrics)
  ✓ Create LeakageDetector (verify no leakage)
  ✓ Create PipelineReportGenerator (generate reports)

Outputs:
  - All component managers initialized
  - Configuration propagated to all components

Failure Handling:
  - Component initialization failure → HALT (critical)
```

### Phase 3: Symbol Validation
```
Goal: Validate input symbol list and load metadata

Tasks:
  ✓ Load symbols from config or input parameter
  ✓ Validate symbols exist and are active
  ✓ Check exchange membership (NYSE, NASDAQ, AMEX)
  ✓ Create symbols_registry.csv
  ✓ Initialize symbol-level error tracking

Outputs:
  - validated_symbols: List[str]
  - symbols_metadata: Dict[symbol, metadata]
  - symbols_registry.csv created

Failure Handling:
  - No valid symbols → HALT (critical)
  - Invalid exchange symbols → LOG WARNING, exclude
```

### Phase 4: Data Acquisition
```
Goal: Fetch 10+ years of OHLCV data for each symbol

Tasks:
  FOR each symbol:
    ✓ Try primary source (IEX Cloud)
    ✓ If failed, try fallback source (yfinance)
    ✓ Validate response format and completeness
    ✓ Check minimum trading days (2,500)
    ✓ Save raw OHLCV CSV
    ✓ Track success/failure

Outputs:
  - raw_data: Dict[symbol, DataFrame]
  - acquisition_manifest.json (per-symbol status)
  - Successfully acquired: Set[symbol]
  - Failed: Set[symbol]

Failure Handling:
  - Network error → Retry with exponential backoff (1s, 2s, 4s)
  - Insufficient data → LOG WARNING, try fallback
  - All sources fail → LOG ERROR, exclude symbol, continue
```

### Phase 5: Data Cleaning
```
Goal: Clean each symbol's raw OHLCV data

Tasks:
  FOR each symbol:
    ✓ Detect missing values and gaps
    ✓ Forward-fill gaps (max 2 consecutive days)
    ✓ Detect and remove/interpolate price spikes (±20%)
    ✓ Validate/correct OHLC relationships (High ≥ Close ≥ Low ≥ Open)
    ✓ Apply stock split and dividend adjustments
    ✓ Validate volume (positive, non-zero)
    ✓ Generate cleaning_report.json per symbol
    ✓ Save cleaned_symbol_clean.csv

Outputs:
  - cleaned_data: Dict[symbol, DataFrame]
  - cleaning_report.json per symbol
  - data_audit_trail.json (aggregate)
  - Successfully cleaned: Set[symbol]

Failure Handling:
  - Unfillable gaps (3+ days) → Exclude date range or symbol
  - Critical OHLC violations → LOG ERROR, try correction, exclude if unfixable
  - Symbol cleaning failure → LOG ERROR, mark for exclusion, continue
```

### Phase 6: Data Quality Validation
```
Goal: Validate cleaned data meets quality thresholds

Tasks:
  FOR each symbol:
    ✓ Check minimum trading days (≥2,500)
    ✓ Check completeness (≥95% non-null OHLCV)
    ✓ Check OHLC relationships (≥99% valid)
    ✓ Compute and validate statistics (no NaN/inf)
    ✓ Detect multi-day price stasis (flag if 5+ days)
    ✓ Generate per-symbol validation result

  ✓ Create validation_report.json
  ✓ Create symbols_excluded_reasons.json

Outputs:
  - validation_results: Dict[symbol, bool]
  - validated_data: Dict[symbol, DataFrame] (passing symbols only)
  - validation_report.json
  - symbols_excluded_reasons.json
  - Quality-assured: Set[symbol]

Failure Handling:
  - Symbol fails validation → LOG WARNING, exclude from downstream
  - Critical validation failure (0 symbols pass) → HALT
```

### Phase 7: Feature Engineering - Orchestration
```
Goal: Compute all features (Tier-1, 2, 3, signal processing) for each symbol

Tasks:
  ✓ Initialize FeatureOrchestrator with tier configuration
  
  FOR each validated symbol:
    ✓ Compute Tier-1 features (returns, normalized prices)
    ✓ Compute Tier-2 features (technical indicators) if enabled
    ✓ Compute Tier-3 features (market regime, cross-asset) if enabled
    ✓ Compute signal processing features (wavelet, SSA, Kalman) if enabled
    ✓ Validate features for NaN/inf/leakage
    ✓ Create feature_manifest per symbol
    ✓ Save features_{symbol}.csv

  ✓ Create aggregate features_manifest.json
  ✓ Create cross_asset_manifest.json

Outputs:
  - features_data: Dict[symbol, DataFrame]
  - features_manifest.json (per-symbol feature definitions)
  - cross_asset_manifest.json (cross-asset metadata)
  - successfully_featured: Set[symbol]

Failure Handling:
  - Feature computation error → LOG ERROR, try with Tier-1 only
  - NaN in features → LOG ERROR, exclude symbol or drop rows
  - Look-ahead bias detected → HALT (data leakage critical)
```

### Phase 8: Chronological Data Splitting
```
Goal: Create train/validation/test splits maintaining temporal integrity

Tasks:
  ✓ Calculate total valid trading days across all symbols
  ✓ Compute cutoff dates (70% train, 15% val, 15% test)
  ✓ Verify: train_end < val_start < test_start (strict chronological order)
  
  FOR each symbol:
    ✓ Split features into train, val, test DataFrames
    ✓ Verify temporal integrity per symbol
  
  ✓ Create splits_metadata.json with cutoff dates
  ✓ Create data_lineage_graph.json (dependency chain)

Outputs:
  - splits: {train: Dict[symbol, DataFrame], 
             val: Dict[symbol, DataFrame],
             test: Dict[symbol, DataFrame]}
  - splits_metadata.json (cutoff dates, date ranges)
  - data_lineage_graph.json

Failure Handling:
  - Temporal ordering violation → HALT (data leakage critical)
  - Symbol with misaligned dates → LOG ERROR, exclude
```

### Phase 9: Preprocessing & Standardization
```
Goal: Fit preprocessing artifacts on training data only

Tasks:
  ✓ Initialize TrainOnlyStandardScaler
  ✓ FIT scaler on training data only
    - Compute mean, std per feature
    - Save fitted scaler (versioned)
  
  ✓ APPLY scaler to training data (with fitted params)
  ✓ APPLY scaler to validation data (without refitting)
  ✓ APPLY scaler to test data (without refitting)
  
  ✓ Save preprocessing_artifacts/
    - v{version}_scalers.pkl
    - v{version}_config_hash.json
    - v{version}_metadata.json

Outputs:
  - processed_splits: {train: ..., val: ..., test: ...} (scaled)
  - preprocessing_artifacts directory
  - artifact_manifest.json

Failure Handling:
  - Scaler fit on validation/test → HALT (data leakage critical)
  - NaN in scaled features → LOG ERROR, investigate
```

### Phase 10: Baseline Model Training & Evaluation
```
Goal: Train all baseline models on training data and evaluate on val/test

Tasks:
  ✓ Initialize BaselineManager with 5 baselines:
    - Random Walk (return_t = return_{t-1})
    - ARIMA(1,1,1) fitted on training close prices
    - Linear Regression (Tier-1 features only)
    - Ridge Regression (all features, tuned on validation)
    - Historical Mean (mean return from training)
  
  FOR each baseline:
    ✓ Train on training data only
    ✓ Generate predictions on validation data
    ✓ Generate predictions on test data
    ✓ Compute metrics (MAE, RMSE, MAPE, Dir. Acc, IC, Sharpe)
    ✓ Compute 95% bootstrap confidence intervals
    ✓ Save baseline_model artifacts

  ✓ Create baseline_results.json (all metrics, all splits)
  ✓ Compare baselines against each other

Outputs:
  - baseline_results: Dict[baseline_name, metrics]
  - baseline_results.json
  - baseline_models/ directory (fitted models, hyperparams)
  - baseline_comparison.html

Failure Handling:
  - Model training failure → LOG ERROR, use NaN placeholder, continue
  - Insufficient data for baseline → LOG WARNING, skip baseline
```

### Phase 11: Data Leakage Detection & Verification
```
Goal: Verify no data leakage occurred throughout pipeline

Tasks:
  ✓ Verify scaler fit only on training data
  ✓ Verify training data earlier than validation data
  ✓ Verify validation data earlier than test data
  ✓ Verify features computed with no look-ahead bias
  ✓ Verify preprocessing artifacts not applied to training set during fit
  ✓ Check for any suspicious data patterns (e.g., identical distributions)

Outputs:
  - leakage_report.json (all checks: pass/fail)
  - data_integrity_verification.json

Failure Handling:
  - Leakage detected → LOG CRITICAL, halt execution, generate leakage_analysis.json
  - Cannot verify leakage (missing metadata) → LOG WARNING, flag for manual review
```

### Phase 12: Report Generation
```
Goal: Generate comprehensive reports and visualizations

Tasks:
  ✓ Generate pipeline_execution_report.md
    - Data sources, symbols processed, retention rates
    - Cleaning summary, feature engineering summary
    - Splits applied, baselines trained, metrics
    - Warnings, errors, execution time
  
  ✓ Generate data_quality_dashboard.html
    - Completeness by symbol
    - Price/volume distributions
    - Missing data trends
    - Cleaning impact visualization
  
  ✓ Generate features_distribution_report.html
    - Feature histograms per split (train/val/test)
    - Distribution shift detection
    - Statistical summaries
  
  ✓ Generate model_card.md
    - Intended use, training data description
    - Evaluation methodology, metrics
    - Known limitations, recommendations
  
  ✓ Save all JSON results (formatted, pretty-printed)
  ✓ Generate execution summary_report.txt

Outputs:
  - pipeline_execution_report.md
  - data_quality_dashboard.html
  - features_distribution_report.html
  - model_card.md
  - summary_report.txt
  - results/ directory populated

Failure Handling:
  - Report generation error → LOG ERROR, skip report, continue
```

### Phase 13: Artifact Archival & Versioning
```
Goal: Save all artifacts with versioning for reproducibility

Tasks:
  ✓ Create experiment_results/{experiment_id}/ directory
  ✓ Archive all outputs:
    - Cleaned data CSVs
    - Feature CSVs
    - Features manifest
    - Splits metadata
    - Preprocessing artifacts
    - Baseline results
    - All reports
    - Configuration (master_config.json)
    - Execution logs
  
  ✓ Create experiment_metadata.json
    - experiment_id (timestamp + hash)
    - git_commit_hash (if available)
    - config_hash
    - execution_duration
    - symbols_processed
    - outcome (success/partial/failure)
  
  ✓ Create reproducibility_checklist.json
    - Seeds fixed: ✓
    - Config saved: ✓
    - Artifacts versioned: ✓
    - Logs generated: ✓
    - No leakage detected: ✓
    - All symbols documented: ✓
  
  ✓ Log completion with timestamp

Outputs:
  - experiment_results/{experiment_id}/ (complete archive)
  - experiment_metadata.json
  - reproducibility_checklist.json
  - COMPLETION_REPORT.md

Failure Handling:
  - Archival failure → LOG ERROR, but don't halt (artifacts still available in staging)
```

---

## Layer Architecture

The system is organized in horizontal layers, each with distinct responsibilities:

```
┌────────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER                                       │
│  (StockForecastingPipeline)                                │
│  - Coordinates 13 phases                                   │
│  - Error recovery and sequencing                           │
│  - Result aggregation                                      │
└────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌────────────────────────────────────────────────────────────┐
│  FEATURE ENGINEERING LAYER                                 │
│  (FeatureOrchestrator)                                     │
│  - Tier-1/2/3 feature modules                              │
│  - Signal processing (wavelet, SSA, Kalman)                │
│  - Cross-asset features                                    │
│  - Feature validation and causality checks                 │
└────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌────────────────────────────────────────────────────────────┐
│  DATA VALIDATION LAYER                                     │
│  (DataQualityValidator)                                    │
│  - Quality thresholds enforcement                          │
│  - Symbol inclusion/exclusion logic                        │
│  - Statistical validation                                  │
│  - Audit trail generation                                  │
└────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌────────────────────────────────────────────────────────────┐
│  DATA CLEANING LAYER                                       │
│  (DataCleaner)                                             │
│  - Missing value detection & forward-filling               │
│  - Spike detection and removal                             │
│  - OHLC relationship validation                            │
│  - Stock split/dividend adjustment                         │
│  - Cleaning report generation                              │
└────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌────────────────────────────────────────────────────────────┐
│  DATA ACQUISITION LAYER                                    │
│  (AcquisitionCoordinator)                                  │
│  - Multi-source adapter orchestration                      │
│  - Fallback mechanism (IEX → yfinance)                     │
│  - Retry logic with exponential backoff                    │
│  - Response validation                                     │
└────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌────────────────────────────────────────────────────────────┐
│  EXTERNAL DATA SOURCES                                     │
│  - IEX Cloud API                                           │
│  - Yahoo Finance (yfinance)                                │
│  - Symbol registry metadata                                │
└────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities & Inputs/Outputs

| Layer | Responsibility | Input | Output |
|-------|---|---|---|
| Orchestration | Coordinate phases, error recovery | Config | Results dict, reports |
| Feature Engineering | Compute 1000+ features | Cleaned data | Feature vectors |
| Data Validation | Quality gates, inclusions | Cleaned data | Validated symbols set |
| Data Cleaning | Standardize raw data | Raw OHLCV | Cleaned OHLCV + reports |
| Acquisition | Fetch data from sources | Symbol list | Raw OHLCV CSVs |
| External | Provide data | API requests | OHLCV data |

---

## Module Hierarchy

### Directory Structure

```
stock-forecasting-system/
│
├── config/
│   ├── __init__.py
│   └── config_loader.py              # ConfigLoader: Load & validate master_config.json
│
├── preprocessing/
│   ├── __init__.py
│   │
│   ├── data_acquisition/             # Fetch raw data from external sources
│   │   ├── __init__.py
│   │   ├── base_adapter.py           # DataAdapter: Abstract interface
│   │   ├── iex_adapter.py            # IEXAdapter: IEX Cloud implementation
│   │   ├── yfinance_adapter.py       # YFinanceAdapter: Yahoo Finance impl
│   │   └── acquisition_coordinator.py # AcquisitionCoordinator: Orchestrate adapters
│   │
│   ├── data_cleaning/                # Clean and standardize raw OHLCV
│   │   ├── __init__.py
│   │   ├── detectors.py              # MissingValueDetector, SpikeDetector
│   │   ├── correctors.py             # SpikeCorrector, OHLCCorrector
│   │   ├── validators.py             # OHLCValidator, DataQualityValidator
│   │   ├── adjusters.py              # SplitDividendAdjuster
│   │   ├── cleaner.py                # DataCleaner: Main orchestrator
│   │   └── test_*.py                 # Unit tests for cleaning components
│   │
│   ├── data_splitter.py              # ChronologicalDataSplitter: 70/15/15 split
│   ├── artifact_manager.py           # TrainOnlyStandardScaler, artifact versioning
│   ├── reproducibility/
│   │   ├── __init__.py
│   │   └── reproducibility_manager.py # ReproducibilityManager: Seed management
│   │
│   └── test_*.py                     # Integration tests
│
├── features/                         # Feature engineering orchestration
│   ├── __init__.py
│   ├── base_features.py              # FeatureModule: Abstract base class
│   │
│   ├── tier1/                        # Basic returns and normalized prices
│   │   ├── __init__.py
│   │   ├── returns.py                # ReturnsFeature: Simple & log returns
│   │   ├── normalized_prices.py      # NormalizedPricesFeature: Price/vol norm
│   │   ├── test_tier1_features.py
│   │   └── __pycache__/
│   │
│   ├── tier2/                        # Technical indicators
│   │   ├── __init__.py
│   │   ├── technical_indicators.py   # RSI, MACD, Bollinger, Stochastic, etc.
│   │   ├── momentum.py               # MomentumFeature: 5, 20, 60-day
│   │   ├── volatility.py             # VolatilityFeature: Rolling STD
│   │   ├── other_indicators.py       # Additional technical features
│   │   ├── test_tier2_features.py
│   │   └── __pycache__/
│   │
│   ├── tier3/                        # Market regimes and cross-asset
│   │   ├── __init__.py
│   │   ├── regime.py                 # MarketRegimeFeature: Regime detection
│   │   ├── cross_asset.py            # RelativeStrengthFeature, correlations
│   │   ├── test_tier3_features.py
│   │   └── __pycache__/
│   │
│   ├── signal_processing/            # Advanced signal decomposition
│   │   ├── __init__.py
│   │   ├── base.py                   # SignalProcessingModule: Base class
│   │   ├── wavelet_transform.py      # WaveletTransformFeature: Multi-scale
│   │   ├── ssa.py                    # SSAFeature: Trend/seasonal decomposition
│   │   ├── kalman_filter.py          # KalmanFilterFeature: State smoothing
│   │   ├── causality.py              # Causality checking utilities
│   │   ├── test_signal_processing.py
│   │   └── __pycache__/
│   │
│   ├── cross_asset/                  # Cross-asset feature computation
│   │   ├── __init__.py
│   │   ├── cross_asset_features.py   # CrossAssetFeature implementations
│   │   ├── market_data_manager.py    # MarketDataManager: Fetch benchmarks
│   │   ├── test_cross_asset_features.py
│   │   └── __pycache__/
│   │
│   ├── feature_orchestrator.py       # FeatureOrchestrator: Coordinate all features
│   ├── feature_validator.py          # FeatureValidator: Check NaN/leakage
│   ├── test_phase5_infrastructure.py # Integration tests
│   └── __pycache__/
│
├── baselines/                        # Baseline models for result contextualization
│   ├── __init__.py
│   ├── base_model.py                 # BaselineModel: Abstract interface
│   ├── random_walk.py                # RandomWalkBaseline: return_t = return_{t-1}
│   ├── arima_model.py                # ARIMABaseline: ARIMA(1,1,1)
│   ├── linear_regression.py          # LinearRegressionBaseline: Tier-1 features
│   ├── ridge_regression.py           # RidgeRegressionBaseline: All features
│   ├── historical_mean.py            # HistoricalMeanBaseline: Mean return
│   ├── baseline_manager.py           # BaselineManager: Orchestrate baselines
│   ├── test_baselines.py
│   └── __pycache__/
│
├── evaluation/                       # Metrics computation and CI
│   ├── __init__.py
│   ├── metrics.py                    # MetricsComputer: MAE, RMSE, IC, Sharpe, etc.
│   ├── confidence_intervals.py       # Bootstrap confidence interval computation
│   ├── test_metrics.py
│   └── __pycache__/
│
├── ablation/                         # Ablation study framework
│   ├── __init__.py
│   ├── ablation_framework.py         # AblationStudy: Remove features, retrain
│   ├── ablation_reporter.py          # AblationReporter: Analyze results
│   ├── test_ablation.py
│   └── __pycache__/
│
├── reporting/                        # Report and visualization generation
│   ├── __init__.py
│   ├── report_generator.py           # PipelineReportGenerator, contexts
│   ├── model_card_generator.py       # ModelCardGenerator: ML model card
│   ├── visualization_utils.py        # Chart generation utilities
│   ├── test_reporting.py
│   └── __pycache__/
│
├── optimization/                     # Advanced optimization (IJF-F)
│   ├── __init__.py
│   ├── ijff_optimizer.py             # IJFFOptimizer: Jellyfish + foraging
│   ├── test_optimization.py
│   └── __pycache__/
│
├── utils/                            # Utilities and helpers
│   ├── __init__.py
│   ├── logging_config.py             # StructuredLogger: JSON logging
│   ├── error_handler.py              # ErrorHandler: Exception tracking
│   ├── leakage_detector.py           # LeakageDetector: Data integrity checks
│   ├── test_utils.py
│   └── __pycache__/
│
├── tests/                            # Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_config_loader.py
│   ├── test_data_acquisition.py
│   ├── test_data_cleaning.py
│   ├── test_feature_engineering.py
│   ├── test_baselines.py
│   ├── test_evaluation.py
│   ├── test_leakage_detection.py
│   └── ... (450+ tests total)
│
├── pipeline.py                       # Main entry point: 13-phase orchestrator
├── master_config.json                # Configuration template (all settings)
├── requirements.txt                  # Pinned dependencies
│
├── results/                          # Output directory (created at runtime)
│   ├── cleaning_report.json
│   ├── validation_report.json
│   ├── features_manifest.json
│   ├── cross_asset_manifest.json
│   ├── splits_metadata.json
│   ├── data_lineage_graph.json
│   ├── baseline_results.json
│   ├── pipeline_execution_report.md
│   ├── model_card.md
│   ├── summary_report.txt
│   ├── visualizations/
│   │   ├── data_quality_dashboard.html
│   │   ├── features_distribution_report.html
│   │   ├── baseline_comparison.png
│   │   └── ... (more PNG exports)
│   └── experiment_results/
│       └── {experiment_id}/          # Versioned experiment archive
│
├── reproducibility_artifacts/        # Versioned preprocessing artifacts
│   ├── v1_scalers.pkl
│   ├── v1_kalman_params.pkl
│   ├── v1_config_hash.json
│   ├── v1_metadata.json
│   └── ... (versioned per experiment)
│
├── logs/                             # Execution logs
│   └── pipeline_{timestamp}.log
│
├── README.md                         # Project overview
├── DATA_GUIDE.md                     # Data pipeline guide
├── ARCHITECTURE.md                   # This file
├── EXPERIMENTS.md                    # Ablation & experiment guide
├── CONTINUATION_GUIDE.md             # Development status
├── TROUBLESHOOTING.md                # Common issues
└── .gitignore
```

### Module Responsibility Matrix

| Module | Primary Responsibility | Key Classes | Dependencies |
|--------|---|---|---|
| config_loader | Load and validate master_config.json | ConfigLoader | json, pathlib |
| data_acquisition | Fetch raw OHLCV from external sources | DataAdapter, IEXAdapter, YFinanceAdapter, AcquisitionCoordinator | requests, pandas, yfinance |
| data_cleaning | Clean and standardize OHLCV | DataCleaner, MissingValueDetector, SpikeDetector, OHLCValidator | pandas, numpy |
| data_splitter | Create chronological train/val/test splits | ChronologicalDataSplitter | pandas |
| artifact_manager | Scale features and version artifacts | TrainOnlyStandardScaler | sklearn, pickle |
| reproducibility | Initialize seeds and manage versioning | ReproducibilityManager | numpy, random |
| features/tier1 | Basic returns and normalized prices | ReturnsFeature, NormalizedPricesFeature | pandas, numpy |
| features/tier2 | Technical indicators (RSI, MACD, etc) | RSIFeature, MACDFeature, BollingerBandsFeature | pandas, numpy, ta-lib |
| features/tier3 | Market regimes and cross-asset features | MarketRegimeFeature, RelativeStrengthFeature | pandas, numpy |
| features/signal_processing | Wavelet, SSA, Kalman decompositions | WaveletTransformFeature, SSAFeature, KalmanFilterFeature | pywt, numpy |
| feature_orchestrator | Coordinate all feature modules | FeatureOrchestrator | All feature modules |
| baselines | Train baseline models | BaselineModel, RandomWalkBaseline, ARIMABaseline | sklearn, statsmodels |
| evaluation | Compute metrics and confidence intervals | MetricsComputer | numpy, scipy |
| ablation | Run ablation studies | AblationStudy | Feature and baseline modules |
| reporting | Generate reports and dashboards | PipelineReportGenerator, ModelCardGenerator | jinja2, plotly |
| utils | Logging, error handling, leakage detection | StructuredLogger, ErrorHandler, LeakageDetector | logging, json |
| pipeline | Main orchestrator | StockForecastingPipeline | All other modules |

---

## Data Flow & Transformations

### Complete Data Flow Diagram

```
Raw Data Symbols
      │
      ▼
┌──────────────────────────┐
│ Symbol Validation        │
│ - Check registry         │
│ - Validate exchange      │
└──────────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ IEX Cloud / yfinance │
    │ (Acquisition)        │
    └──────────┬───────────┘
               │
      ▼────────▼─────────┐
      │ Raw OHLCV CSV    │
      │ (per symbol)     │
      └────────┬─────────┘
               │
      ┌────────▼──────────┐
      │ Data Cleaning     │
      │ - Gap fill        │
      │ - Spike removal   │
      │ - OHLC validation │
      │ - Split/div adj.  │
      └────────┬──────────┘
               │
      ▼────────▼──────────┐
      │ Cleaned OHLCV    │
      │ + Reports        │
      └────────┬──────────┘
               │
      ┌────────▼──────────┐
      │ Quality Validation│
      │ - Min days check  │
      │ - Completeness    │
      │ - Statistics      │
      └────────┬──────────┘
               │
     ▼─────────▼──────────┐
     │ Validated Symbols │
     │ (pass/fail set)   │
     └────────┬──────────┘
              │
    ┌─────────▼────────────┐
    │ Feature Engineering   │
    ├─ Tier-1: Returns     │
    ├─ Tier-2: Indicators  │
    ├─ Tier-3: Regimes     │
    └─ Signal Proc: W/S/K  │
    └─────────┬────────────┘
              │
     ▼────────▼──────────┐
     │ Feature Vectors  │
     │ (1000+ cols)     │
     └────────┬──────────┘
              │
    ┌─────────▼────────────┐
    │ Chronological Split  │
    │ - Train: 70%         │
    │ - Val:   15%         │
    │ - Test:  15%         │
    └─────────┬────────────┘
              │
     ▼────────▼──────────┐
     │ Split Data        │
     │ (train/val/test)  │
     │ + Metadata        │
     └────────┬──────────┘
              │
    ┌─────────▼──────────────┐
    │ Preprocessing          │
    │ - Fit scaler on train  │
    │ - Apply to val/test    │
    │ - Save artifacts       │
    └─────────┬──────────────┘
              │
     ▼────────▼────────────┐
     │ Scaled Data          │
     │ (ready for models)   │
     │ + Artifacts          │
     └────────┬─────────────┘
              │
    ┌─────────▼────────────────┐
    │ Baseline Training        │
    │ - Train 5 baselines      │
    │ - Generate predictions   │
    │ - Compute metrics        │
    └─────────┬────────────────┘
              │
     ▼────────▼──────────────┐
     │ Baseline Results       │
     │ (metrics, preds)       │
     │ + Model artifacts      │
     └────────┬───────────────┘
              │
    ┌─────────▼────────────────┐
    │ Leakage Detection        │
    │ - Verify scaler fit      │
    │ - Check temporal order   │
    │ - Validate causality     │
    └─────────┬────────────────┘
              │
   ┌──────────▼──────────────┐
   │ Final Reports           │
   │ - Execution report      │
   │ - Data quality dash     │
   │ - Feature distributions │
   │ - Model card            │
   └──────────┬───────────────┘
              │
  ▼───────────▼────────────┐
  │ Artifact Archive       │
  │ experiment_results/{id}│
  │ + Metadata & Lineage   │
  └────────────────────────┘
```

### Data Transformation Examples

**Example 1: Raw to Cleaned OHLCV (Symbol: AAPL)**

```
Input (Raw):
Date       Open    High    Low     Close   Volume
2020-03-16 NaN     NaN     NaN     NaN     NaN        ← Gap
2020-03-17 NaN     NaN     NaN     NaN     NaN        ← Gap
2020-03-18 280.10  285.50  280.00  285.25  45000000
2020-03-19 284.00  305.00  282.00  298.45  89000000   ← 4.6% spike

Processing:
1. Forward-fill 2-day gap with 2020-03-17
2. Verify OHLC relationships (285.25 within 280-285.50: OK)
3. Spike: 4.6% checked against alternative sources
4. Apply dividend adjustment (if any)

Output (Cleaned):
Date       Open    High    Low     Close   Volume      AdjClose
2020-03-16 280.10  285.50  280.00  285.25  45000000   285.25 ← Forward-filled
2020-03-17 280.10  285.50  280.00  285.25  45000000   285.25 ← Forward-filled
2020-03-18 280.10  285.50  280.00  285.25  45000000   285.25 ← Real data
2020-03-19 284.00  305.00  282.00  298.45  89000000   298.45 ← Spike verified
```

**Example 2: Cleaned to Featured Data (First 3 Tier-1 + Tier-2 features)**

```
Input (Cleaned OHLCV):
Date       Close   Volume
2020-03-18 285.25  45000000
2020-03-19 298.45  89000000
2020-03-20 295.50  67000000

Processing (Tier-1):
simple_return_t = (Close_t - Close_{t-1}) / Close_{t-1}
log_return_t = log(Close_t / Close_{t-1})

Processing (Tier-2: RSI):
RSI_t = 100 - 100/(1 + RS), where RS = AvgGain/AvgLoss

Output (Featured):
Date       simple_return log_return RSI_14  ... (1000+ more features)
2020-03-18 NaN           NaN        NaN     (lag 1)
2020-03-19 0.0460        0.0449     NaN     (lag 1)
2020-03-20 -0.0099       -0.0099    42.3    (computed from 14-day history)
```

**Example 3: Features to Splits (Train/Val/Test)**

```
Input (All Features, 2523 trading days):
symbol=AAPL, dates: 2002-01-02 to 2024-01-19
All 1000+ features computed and aligned

Processing (70/15/15 chronological split):
Total days = 2523
Train_days = floor(2523 * 0.70) = 1766
Val_days = floor(2523 * 0.15) = 378
Test_days = 2523 - 1766 - 378 = 379

Cutoff dates:
train_start: 2002-01-02
train_end: 2013-12-20     ← Last training day
val_start: 2013-12-23     ← First validation day (after train_end)
val_end: 2017-06-30       ← Last validation day
test_start: 2017-07-03    ← First test day (after val_end)
test_end: 2024-01-19      ← Last test day

Output (3 Splits):
train: DataFrame[2002-01-02 : 2013-12-20, 1000+ features, 1766 rows]
val:   DataFrame[2013-12-23 : 2017-06-30, 1000+ features, 378 rows]
test:  DataFrame[2017-07-03 : 2024-01-19, 1000+ features, 379 rows]
```

**Example 4: Preprocessing Artifacts (Scaling)**

```
Input (Split Data):
train_features: shape (1766, 1000)  ← Contains all features, 1766 days
val_features:   shape (378, 1000)
test_features:  shape (379, 1000)

FIT SCALER ON TRAINING DATA ONLY:
For each feature:
  mean_feature = np.mean(train_features[:, feature_idx])
  std_feature = np.std(train_features[:, feature_idx])
  
Example: simple_return feature
  mean = 0.00087  (0.087% average return)
  std = 0.02134   (2.134% volatility)

APPLY SCALER (NO REFITTING):
train_scaled = (train_features - mean) / (std + eps)  ← Using fitted params
val_scaled = (val_features - mean) / (std + eps)      ← SAME params, no refit!
test_scaled = (test_features - mean) / (std + eps)    ← SAME params, no refit!

Output (Artifact):
reproducibility_artifacts/v1_scalers.pkl:
  {'simple_return': {'mean': 0.00087, 'std': 0.02134, 'fit_on': 'train'},
   'rsi_14': {'mean': 48.5, 'std': 18.2, 'fit_on': 'train'},
   ... (per feature)}

Output (Scaled Data):
train_scaled: shape (1766, 1000), mean≈0, std≈1 per feature
val_scaled:   shape (378, 1000)   (different mean/std than original)
test_scaled:  shape (379, 1000)   (different mean/std than original)
```

---

## Dependency Graph

### Module Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                    ConfigLoader (ROOT)                          │
│  - Loads master_config.json                                      │
│  - Provides config dict to all phases                            │
└──────────┬──────────────────────────────────────────────────────┘
           │
    ┌──────┴──────────┬──────────────┬──────────────┬──────────────┐
    ▼                 ▼              ▼              ▼              ▼
┌─────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐
│   Logs  │  │Reproducibility│ │Acquisition│ │Cleaning  │  │Validation  │
│ Manager │  │  Manager     │  │Coordinator│ │          │  │            │
└─────────┘  └──────────────┘  └──────────┘  └──────────┘  └────────────┘
                                    │              │              │
                      IEXAdapter,   │              │              │
                      YFinanceAdapter          │              │
                                    │              │              │
                                    └──────────┬───┴───┬──────────┘
                                               │       │
                                           Raw Data   Cleaned Data
                                           CSVs       + Reports
                                               │       │
                                    ┌──────────▼───────▼──────────┐
                                    │  FeatureOrchestrator        │
                                    │  (All feature modules)      │
                                    └──────────────┬──────────────┘
                                                   │
                                            Feature Vectors
                                                   │
                                    ┌──────────────▼──────────────┐
                                    │  ChronologicalDataSplitter  │
                                    │  (70/15/15 split)           │
                                    └──────────────┬──────────────┘
                                                   │
                                            Train/Val/Test
                                                   │
                                    ┌──────────────▼──────────────┐
                                    │  TrainOnlyStandardScaler    │
                                    │  (Fit on train, apply all)  │
                                    └──────────────┬──────────────┘
                                                   │
                                            Scaled Data
                                            + Artifacts
                                                   │
                    ┌──────────────────────────────┼──────────────────────┐
                    ▼                              ▼                       ▼
            ┌──────────────┐          ┌────────────────────┐     ┌──────────────┐
            │ BaselineManager         │ MetricsComputer    │     │LeakageDetector
            │ (5 baselines)           │ (MAE, RMSE, IC)    │     │              │
            └──────────────┘          └────────────────────┘     └──────────────┘
                    │                              │                       │
                    └──────────────┬────────────────┴───────────────────────┘
                                   │
                           Baseline Results
                           Metrics, Scores
                                   │
                    ┌──────────────▼──────────────┐
                    │  PipelineReportGenerator    │
                    │  (Generate all reports)     │
                    └──────────────┬──────────────┘
                                   │
                           Reports, Dashboards,
                           Model Cards, Lineage
                                   │
                    ┌──────────────▼──────────────┐
                    │  ArtifactManager            │
                    │  (Archive & Version)        │
                    └─────────────────────────────┘
```

### Class Hierarchy

**DataAdapter Hierarchy:**
```
DataAdapter (ABC)
  ├─ IEXAdapter
  │   ├─ __init__(api_token)
  │   ├─ fetch(symbol, start_date, end_date) → DataFrame
  │   ├─ validate_response(df) → bool
  │   └─ _retry_with_backoff() → responses
  │
  └─ YFinanceAdapter
      ├─ __init__()
      ├─ fetch(symbol, start_date, end_date) → DataFrame
      └─ validate_response(df) → bool
```

**FeatureModule Hierarchy:**
```
FeatureModule (ABC)
  ├─ ReturnsFeature
  │   └─ compute(df) → [simple_return, log_return]
  │
  ├─ NormalizedPricesFeature
  │   └─ compute(df) → [norm_close_20, norm_volume_20]
  │
  ├─ RSIFeature (Tier-2)
  │   └─ compute(df, period=14) → [rsi_14]
  │
  ├─ MACDFeature (Tier-2)
  │   └─ compute(df) → [macd_line, macd_signal, macd_histogram]
  │
  ├─ MarketRegimeFeature (Tier-3)
  │   └─ compute(df, lookback=60) → [regime]
  │
  └─ SignalProcessingModule (ABC)
      ├─ WaveletTransformFeature
      │   └─ compute(df, wavelet='db4', levels=3) → [wavelet_*]
      ├─ SSAFeature
      │   └─ compute(df, embedding_dim=60) → [ssa_trend, ssa_seasonal]
      └─ KalmanFilterFeature
          └─ compute(df, fit_data=None) → [kalman_smoothed, kalman_uncertainty]
```

**BaselineModel Hierarchy:**
```
BaselineModel (ABC)
  ├─ RandomWalkBaseline
  │   └─ predict(df_train, df_test) → predictions
  │
  ├─ ARIMABaseline
  │   └─ fit(df_train); predict(df_test) → predictions
  │
  ├─ LinearRegressionBaseline
  │   └─ fit(X_train, y_train); predict(X_test) → predictions
  │
  ├─ RidgeRegressionBaseline
  │   └─ fit(X_train, y_train, alpha); predict(X_test) → predictions
  │
  └─ HistoricalMeanBaseline
      └─ predict(df_train, df_test) → predictions
```

---

## Configuration Management

### Configuration Flow

```
Environment
  │
  ├─ IEX_CLOUD_TOKEN (env var)
  └─ Python version, packages
  
                    │
                    ▼
            master_config.json
            - Static configuration
            - Hardcoded paths
            - Feature selections
            - Model hyperparameters
                    │
                    ▼
            ConfigLoader
            - Load JSON
            - Validate schema
            - Override from env
            - Resolve paths
                    │
                    ▼
            config dict (in-memory)
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   Pipeline    Adapters    Feature
   Components  Components  Modules
```

### Configuration Schema (master_config.json)

```json
{
  "pipeline_metadata": {
    "execution_timestamp": "2024-01-19T10:30:00Z",
    "pipeline_version": "1.0",
    "stage": "Stage_1_DataCleaning_FeatureEngineering"
  },
  
  "random_seeds": {
    "numpy_seed": 42,
    "random_seed": 42,
    "tensorflow_seed": 42,
    "documentation": "For reproducibility, fixed before all stochastic operations"
  },
  
  "logging": {
    "log_dir": "logs/",
    "log_level": "INFO",
    "format": "structured_json"
  },
  
  "data_acquisition": {
    "primary_source": "iex_cloud",
    "fallback_source": "yfinance",
    "iex_api_token": "${IEX_CLOUD_TOKEN}",
    "lookback_years": 10,
    "min_trading_days": 2500,
    "retry_attempts": 3,
    "retry_backoff_factor": 2,
    "timeout_seconds": 30
  },
  
  "symbols": {
    "list": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    "max_portfolio_size": 100,
    "supported_exchanges": ["NYSE", "NASDAQ", "AMEX"]
  },
  
  "data_cleaning": {
    "max_consecutive_missing_days": 2,
    "spike_threshold": 0.20,
    "spike_verification_sources": 3,
    "ohlc_fix_method": "linear_interpolation",
    "volume_fill_method": "forward_fill"
  },
  
  "feature_engineering": {
    "tier1_enabled": true,
    "tier2_enabled": true,
    "tier3_enabled": true,
    "signal_processing_enabled": false,
    "tier2_indicators": ["rsi", "macd", "bollinger", "atr", "adx", "obv"],
    "tier3_lookback": 60
  },
  
  "data_splitting": {
    "methodology": "chronological_70_15_15",
    "train_ratio": 0.70,
    "val_ratio": 0.15,
    "test_ratio": 0.15
  },
  
  "preprocessing": {
    "scaler_type": "standard",
    "fit_on": "train_only",
    "artifact_versioning": true
  },
  
  "baseline_models": {
    "random_walk": {"enabled": true},
    "arima_111": {"enabled": true, "order": [1, 1, 1]},
    "linear_regression": {"enabled": true, "features": "tier1"},
    "ridge_regression": {"enabled": true, "alpha": 1.0, "tune_on": "val"},
    "historical_mean": {"enabled": true}
  },
  
  "evaluation": {
    "metrics": ["mae", "rmse", "mape", "directional_accuracy", "ic", "sharpe"],
    "bootstrap_ci_resamples": 1000,
    "ci_level": 0.95
  },
  
  "reporting": {
    "output_dir": "results/",
    "generate_dashboards": true,
    "generate_visualizations": true,
    "visualization_dpi": 300
  }
}
```

### Configuration Override Hierarchy

```
Default Values (hardcoded)
         ↑ (overridden by)
master_config.json
         ↑ (overridden by)
Environment Variables (${VAR_NAME})
         ↑ (overridden by)
Runtime Parameters (CLI args, function params)
```

---

## Error Handling & Recovery

### Error Handling Architecture

```
┌─────────────────────────────────────────────────────┐
│              ErrorHandler Manager                   │
│  - Centralized exception handling                   │
│  - Error tracking and recovery                      │
│  - Structured error logging                         │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    Data       Validation   Computation
    Errors     Errors       Errors
        │          │          │
        ▼          ▼          ▼
    Retry    Symbol      Log &
    Logic    Exclusion   Continue
```

### Error Categories & Recovery Strategies

| Error Category | Example | Severity | Recovery Strategy |
|---|---|---|---|
| **Network Error** | IEX Cloud timeout | Medium | Retry (exponential backoff); try fallback |
| **Data Format Error** | Unexpected column in response | Medium | Log error; try fallback source; exclude symbol |
| **Insufficient Data** | < 2,500 trading days for symbol | Low | Log warning; exclude symbol; continue |
| **Data Integrity** | OHLC violation; NaN in features | Medium | Log error; correct if possible; exclude symbol if not |
| **Leakage Detected** | Validation data in scaler fit | Critical | Log CRITICAL; halt execution; generate leakage_report.json |
| **Configuration Error** | Missing required config key | Critical | Log error; halt execution; suggest fix |
| **Temporal Order Violation** | val_start < train_end | Critical | Log error; halt execution; check split logic |

### Symbol-Level Error Recovery

```
FOR each symbol:
  TRY:
    Acquire data
    Clean data
    Validate data
    Compute features
    Split data
    Preprocess
  
  EXCEPT AcquisitionError:
    Log "Symbol {symbol}: acquisition failed"
    Try fallback
    IF fallback succeeds:
      Continue
    ELSE:
      Mark symbol as EXCLUDED
      Add to failed_symbols set
      Continue with next symbol
  
  EXCEPT ValidationError:
    Log "Symbol {symbol}: validation failed - reason"
    Mark symbol as EXCLUDED
    Add to failed_symbols set
    Continue with next symbol

IF all_symbols_failed:
  Log CRITICAL "No symbols succeeded"
  HALT execution
ELSE:
  Continue to next phase
```

### Error Reporting

**error_summary.json** (at pipeline completion):

```json
{
  "execution_status": "PARTIAL_SUCCESS",
  "symbols_processed": 500,
  "symbols_succeeded": 495,
  "symbols_failed": 5,
  "errors": [
    {
      "symbol": "BADSTOCK",
      "phase": "acquisition",
      "error_type": "InsufficientDataError",
      "message": "Only 1800 trading days, need 2500",
      "timestamp": "2024-01-19T10:30:15Z"
    }
  ],
  "warnings": [
    {
      "type": "DataQualityWarning",
      "count": 12,
      "message": "12 symbols flagged for manual review due to multi-day price stasis"
    }
  ],
  "critical_issues": []
}
```

---

## Reproducibility & Artifact Management

### Reproducibility Mechanisms

```
Reproducibility Stack:

┌─────────────────────────────────────────┐
│  Experiment ID: timestamp + config_hash │
│  git_commit_hash (if available)         │
└────────────┬────────────────────────────┘
             │
    ┌────────▼────────┐
    │ Configuration   │
    │ Hashing         │
    │ (master_config) │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ Random Seed     │
    │ Initialization  │
    │ (numpy, py,tf)  │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ Reproducibility │
    │ Artifacts       │
    │ (scalers,       │
    │  kalman_params, │
    │  model_weights) │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ Data Lineage    │
    │ Graph           │
    │ (dependency     │
    │  chain)         │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ Complete        │
    │ Experiment      │
    │ Archive         │
    └─────────────────┘
```

### Artifact Versioning

```
reproducibility_artifacts/
├── v1/
│   ├── scalers.pkl                    # Fitted StandardScaler
│   ├── kalman_params.pkl              # Fitted Kalman filter params
│   ├── config_hash.json               # master_config hash
│   ├── metadata.json                  # Experiment metadata
│   └── lineage_graph.json             # Data dependency chain
├── v2/
│   ├── scalers.pkl
│   ├── kalman_params.pkl
│   ├── config_hash.json
│   ├── metadata.json
│   └── lineage_graph.json
└── ...
```

### Experiment Archive Structure

```
results/experiment_results/{experiment_id}/
├── master_config.json                 # Exact configuration used
├── experiment_metadata.json           # ID, timestamp, hashes, outcome
│
├── data/
│   ├── cleaned/
│   │   ├── AAPL_clean.csv
│   │   ├── MSFT_clean.csv
│   │   └── ...
│   └── features/
│       ├── AAPL_features.csv
│       ├── MSFT_features.csv
│       └── ...
│
├── artifacts/
│   ├── v1_scalers.pkl
│   ├── v1_kalman_params.pkl
│   ├── features_manifest.json
│   ├── splits_metadata.json
│   ├── data_lineage_graph.json
│   └── reproducibility_checklist.json
│
├── results/
│   ├── cleaning_report.json
│   ├── validation_report.json
│   ├── baseline_results.json
│   ├── ablation_results.json (if applicable)
│   └── evaluation_metrics.json
│
├── reports/
│   ├── pipeline_execution_report.md
│   ├── model_card.md
│   ├── data_quality_summary.txt
│   └── visualizations/
│       ├── data_quality_dashboard.html
│       ├── features_distribution.html
│       └── baseline_comparison.png
│
└── logs/
    └── pipeline_{experiment_id}.log
```

### Reproducibility Checklist

**reproducibility_checklist.json** (at completion):

```json
{
  "experiment_id": "exp_20240119_103045_8f3c4a2b",
  "checklist": {
    "seeds_fixed": {
      "status": "PASS",
      "numpy_seed": 42,
      "random_seed": 42,
      "tensorflow_seed": 42,
      "verified_at": "Phase 1"
    },
    "config_saved": {
      "status": "PASS",
      "config_hash": "sha256:8f3c4a2b...",
      "path": "results/experiment_results/{id}/master_config.json"
    },
    "artifacts_versioned": {
      "status": "PASS",
      "version": "v1",
      "artifacts": ["scalers.pkl", "kalman_params.pkl", "metadata.json"],
      "verified_at": "Phase 13"
    },
    "logs_generated": {
      "status": "PASS",
      "log_file": "logs/pipeline_20240119_103045.log",
      "entries": 5234,
      "format": "structured_json"
    },
    "no_leakage_detected": {
      "status": "PASS",
      "verified_at": "Phase 11",
      "checks": ["scaler_fit_on_train_only", "temporal_order", "causality"]
    },
    "all_symbols_documented": {
      "status": "PASS",
      "total_input": 500,
      "successfully_processed": 495,
      "excluded": 5,
      "exclusion_reasons_documented": true
    }
  },
  "overall_status": "REPRODUCIBLE"
}
```

---

## Testing Architecture

### Test Organization

```
tests/
├── conftest.py                        # Pytest fixtures
├── test_config_loader.py              # Configuration loading
├── test_data_acquisition.py           # Data source adapters, fallback
├── test_data_cleaning.py              # Cleaning algorithms
├── test_data_validation.py            # Quality validation
├── test_feature_engineering.py        # Tier-1/2/3 features
├── test_signal_processing.py          # Wavelet, SSA, Kalman
├── test_baselines.py                  # Baseline models
├── test_evaluation_metrics.py         # Metrics computation
├── test_leakage_detection.py          # Data integrity checks
├── test_pipeline_integration.py       # End-to-end tests
└── test_ablation_framework.py         # Ablation studies
```

### Test Coverage Goals

| Module | Test Type | Coverage | Status |
|--------|---|---|---|
| data_acquisition | Unit + Integration | 95%+ | ✓ |
| data_cleaning | Unit + Integration | 90%+ | ✓ |
| feature_engineering | Unit + Property-based | 85%+ | ✓ |
| baselines | Unit | 90%+ | ✓ |
| evaluation | Unit | 90%+ | ✓ |
| pipeline orchestration | Integration | 80%+ | ✓ |
| **Total Test Suite** | **All combined** | **450+ tests** | **✓** |

### Test Execution

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_features.py -v

# With coverage report
pytest tests/ --cov=. --cov-report=html

# Integration tests only
pytest tests/ -m integration -v

# Fast tests only (skip slow/network tests)
pytest tests/ -m "not slow" -v
```

---

## Performance Characteristics

### Computational Complexity

| Phase | Operation | Complexity | Data Size | Time (est.) |
|-------|---|---|---|---|
| Acquisition | Fetch 1 symbol × 10 years | O(1) per symbol | ~2,500 rows | 1-5 sec |
| Cleaning | 1 symbol: gaps, spikes, OHLC | O(n) | 2,500 rows | 0.1 sec |
| Validation | Quality checks per symbol | O(n) | 2,500 rows | 0.05 sec |
| Features | Tier-1 + Tier-2 (50+ features) | O(n × m) | n=2,500, m=50 | 0.5 sec |
| Splitting | Chronological split 70/15/15 | O(n) | 2,500 rows | 0.01 sec |
| Preprocessing | Fit/apply StandardScaler | O(n × m) | 2,500 × 1000 | 0.1 sec |
| Baselines | Train 5 models (ARIMA is slowest) | O(n × m × iterations) | n=1,766 | 5-10 sec |
| Evaluation | Compute metrics + bootstrap CI | O(n × resamples) | n=379, resamples=1,000 | 1 sec |
| **Total (100 symbols)** | **All phases** | **Mostly linear** | **250K rows** | **5-10 min** |

### Memory Usage Patterns

```
Phase              Memory Peak      Description
────────────────────────────────────────────────────
Acquisition        Low (100MB)      Raw OHLCV for 1 symbol
Cleaning           Low (100MB)      Processed OHLCV per symbol
Validation         Low (100MB)      QA checks on 1 symbol
Features           High (1GB+)      All features for all symbols in memory
Splitting          High (1GB+)      Train/val/test datasets
Preprocessing      Medium (500MB)   Scalers, fit models
Baselines          Medium (500MB)   5 baseline models
Evaluation         Low (100MB)      Results aggregation
────────────────────────────────────────────────────
Peak:              ~1-2 GB (for 100 symbols)
```

### Scalability Analysis

**Scaling with Portfolio Size:**
```
Symbols  | Time  | Memory | Disk Output
---------|-------|--------|─────────────
10       | 30s   | 150MB  | 500MB
50       | 2m30s | 500MB  | 2GB
100      | 5-10m | 1-2GB  | 4GB
500      | 30-60m| 4-5GB  | 20GB
```

**Scaling with Feature Tier:**
```
Feature Tiers Enabled | Computation Time | Feature Count
───────────────────────────────────────────────────────
Tier-1 only           | 1x baseline      | ~5 features
Tier-1 + Tier-2       | 3-4x baseline    | ~50 features
Tier-1 + 2 + 3        | 5-6x baseline    | ~150+ features
+ Signal Processing   | 10-15x baseline  | ~200+ features
```

### Bottleneck Analysis

**Primary Bottlenecks (in order):**
1. **Network I/O** (data acquisition from IEX/yfinance) - 30-40% of total time
2. **ARIMA Model Training** (slowest baseline) - 20-30% of total time
3. **Feature Computation** (especially signal processing) - 15-20% of total time
4. **Report Generation** (visualizations, HTML) - 10-15% of total time
5. **Metrics & Confidence Intervals** (bootstrap resampling) - 5-10% of total time

**Optimization Opportunities:**
- Parallelize symbol processing (currently sequential)
- Cache data downloads
- Skip slow baselines if only interested in features
- Use vectorized NumPy operations (already done)
- Lazy-load signal processing features (only if needed)

---

## Design Patterns

### 1. **Adapter Pattern** (Data Sources)

```python
class DataAdapter(ABC):
    @abstractmethod
    def fetch(self, symbol: str, start_date: str, end_date: str) -> DataFrame:
        pass

class IEXAdapter(DataAdapter):
    def fetch(self, symbol: str, start_date: str, end_date: str) -> DataFrame:
        # IEX Cloud implementation

class YFinanceAdapter(DataAdapter):
    def fetch(self, symbol: str, start_date: str, end_date: str) -> DataFrame:
        # Yahoo Finance implementation
```

**Use Case:** Support multiple data sources with consistent interface; easy to add new sources.

---

### 2. **Strategy Pattern** (Feature Modules)

```python
class FeatureModule(ABC):
    @abstractmethod
    def compute(self, df: DataFrame) -> DataFrame:
        pass

class ReturnsFeature(FeatureModule):
    def compute(self, df: DataFrame) -> DataFrame:
        return df['Close'].pct_change()

class RSIFeature(FeatureModule):
    def compute(self, df: DataFrame) -> DataFrame:
        # RSI computation
```

**Use Case:** Swap feature modules without changing orchestrator; enable ablation studies.

---

### 3. **Orchestrator Pattern** (Pipeline)

```python
class StockForecastingPipeline:
    def run(self, symbols: List[str]):
        self._phase_1_initialization()
        self._phase_2_configuration()
        self._phase_3_symbol_validation()
        # ... etc
        self._phase_13_artifact_archival()
```

**Use Case:** Coordinate complex multi-step workflow; centralize error handling and logging.

---

### 4. **Chain of Responsibility** (Data Validation)

```
Data Quality Validator
  ├─ Check: Minimum trading days
  │   └─ If fail: Exclude symbol
  ├─ Check: OHLC relationships
  │   └─ If fail: Correct or exclude
  ├─ Check: No multi-day stasis
  │   └─ If fail: Flag for review
  └─ Check: Valid statistics
      └─ If fail: Exclude symbol
```

**Use Case:** Apply multiple validation rules in sequence; early rejection of bad data.

---

### 5. **Factory Pattern** (Model Creation)

```python
class BaselineManager:
    def __init__(self, config):
        self.baselines = []
        if config['random_walk']['enabled']:
            self.baselines.append(RandomWalkBaseline())
        if config['arima_111']['enabled']:
            self.baselines.append(ARIMABaseline())
        # ... etc
```

**Use Case:** Create baseline models dynamically based on configuration.

---

### 6. **Decorator Pattern** (Preprocessing)

```python
def apply_scaling(features: DataFrame, scaler) -> DataFrame:
    # Decorator: Apply preprocessing without modifying original
    return scaler.transform(features)

# Usage
scaled_features = apply_scaling(raw_features, fitted_scaler)
```

**Use Case:** Add preprocessing step without modifying original data; ensure immutability.

---

### 7. **Template Method Pattern** (Feature Computation)

```python
class FeatureModule(ABC):
    def __call__(self, df: DataFrame) -> DataFrame:
        raw_features = self.compute(df)
        self.validate(raw_features)
        self.check_causality(raw_features)
        return raw_features
    
    @abstractmethod
    def compute(self, df: DataFrame) -> DataFrame:
        pass
    
    def validate(self, features: DataFrame) -> None:
        # Default validation (override in subclasses)
        pass
```

**Use Case:** Enforce consistent pre/post-processing steps across all feature modules.

---

### 8. **Repository Pattern** (Artifact Storage)

```python
class ArtifactRepository:
    def save_artifact(self, name: str, data: Any, version: str) -> str:
        path = f"reproducibility_artifacts/v{version}/{name}.pkl"
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        return path
    
    def load_artifact(self, name: str, version: str) -> Any:
        path = f"reproducibility_artifacts/v{version}/{name}.pkl"
        with open(path, 'rb') as f:
            return pickle.load(f)
```

**Use Case:** Centralize artifact storage; version management; easy retrieval.

---

## Extension Points

### 1. Adding a New Data Source

**Step 1: Create Adapter Class**
```python
# preprocessing/data_acquisition/custom_adapter.py
from preprocessing.data_acquisition.base_adapter import DataAdapter

class CustomDataAdapter(DataAdapter):
    def __init__(self, api_token: str = None):
        self.api_token = api_token
        self.base_url = "https://custom-api.com"
    
    def fetch(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # Implementation: Fetch from custom API
        # Must return DataFrame with columns: [Date, Open, High, Low, Close, Volume]
        pass
    
    def validate_response(self, df: pd.DataFrame) -> bool:
        # Validation logic
        pass
```

**Step 2: Register in AcquisitionCoordinator**
```python
# preprocessing/data_acquisition/acquisition_coordinator.py
from preprocessing.data_acquisition.custom_adapter import CustomDataAdapter

class AcquisitionCoordinator:
    def __init__(self, config):
        if config.get('custom_source'):
            self.adapters.append(CustomDataAdapter(config['custom_token']))
```

**Step 3: Update Configuration**
```json
{
  "data_acquisition": {
    "primary_source": "custom",
    "custom_token": "${CUSTOM_API_TOKEN}",
    "fallback_source": "iex_cloud"
  }
}
```

---

### 2. Adding a New Feature Module

**Step 1: Create Feature Class**
```python
# features/tier2/my_indicator.py
from features.base_features import FeatureModule
import numpy as np
import pandas as pd

class MyIndicatorFeature(FeatureModule):
    def __init__(self, period: int = 14, config: dict = None):
        super().__init__("my_indicator", tier=2, config=config or {})
        self.period = period
    
    def compute(self, df: pd.DataFrame, fit_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Compute my indicator.
        
        Returns:
            DataFrame with column [my_indicator]
        """
        # Implementation
        result = pd.DataFrame({'my_indicator': [...]}, index=df.index)
        return result
    
    def validate(self, features: pd.DataFrame) -> tuple[bool, list[str]]:
        """
        Validate computed features for NaN, inf, leakage.
        """
        errors = []
        if features['my_indicator'].isna().any():
            errors.append("my_indicator contains NaN")
        return len(errors) == 0, errors
```

**Step 2: Register in FeatureOrchestrator**
```python
# features/feature_orchestrator.py
from features.tier2.my_indicator import MyIndicatorFeature

class FeatureOrchestrator:
    def _initialize_modules(self):
        if self.config.include_tier2:
            self.tier2_modules.extend([
                # ... existing modules
                MyIndicatorFeature(),
            ])
```

**Step 3: Add Configuration Option (optional)**
```json
{
  "feature_engineering": {
    "tier2_indicators": ["rsi", "macd", "my_indicator"]
  }
}
```

---

### 3. Adding a New Baseline Model

**Step 1: Create Baseline Class**
```python
# baselines/my_model.py
from baselines.base_model import BaselineModel
import numpy as np

class MyBaselineModel(BaselineModel):
    def __init__(self, config: dict = None):
        super().__init__("my_model", config or {})
        self.model = None
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train model on training data only."""
        # Training implementation
        pass
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        # Prediction implementation
        pass
    
    def get_params(self) -> dict:
        """Return hyperparameters."""
        return {"param1": value1, "param2": value2}
```

**Step 2: Register in BaselineManager**
```python
# baselines/baseline_manager.py
from baselines.my_model import MyBaselineModel

class BaselineManager:
    def _initialize_baselines(self):
        if self.config['my_model']['enabled']:
            self.baselines.append(MyBaselineModel(self.config['my_model']))
```

**Step 3: Update Configuration**
```json
{
  "baseline_models": {
    "my_model": {
      "enabled": true,
      "param1": "value1",
      "param2": "value2"
    }
  }
}
```

---

### 4. Adding New Evaluation Metrics

**Step 1: Add Metric Method**
```python
# evaluation/metrics.py
class MetricsComputer:
    @staticmethod
    def my_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Compute my custom metric.
        
        Returns:
            Scalar metric value
        """
        # Implementation
        return metric_value
```

**Step 2: Register in Configuration**
```json
{
  "evaluation": {
    "metrics": ["mae", "rmse", "my_metric"]
  }
}
```

**Step 3: Use in Pipeline**
```python
# pipeline.py
metrics = self.metrics_computer.compute_all_metrics(
    y_train, y_train_pred,
    y_val, y_val_pred,
    y_test, y_test_pred
)
```

---

### 5. Adding New Visualizations

**Step 1: Create Visualization Function**
```python
# reporting/visualization_utils.py
def plot_my_visualization(data: DataFrame, output_path: str) -> None:
    """Generate custom visualization."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    # Add traces, layout, etc.
    fig.write_html(output_path)
```

**Step 2: Integrate into Report Generator**
```python
# reporting/report_generator.py
class PipelineReportGenerator:
    def generate_visualizations(self):
        # ... existing visualizations
        plot_my_visualization(self.data, "results/visualizations/my_viz.html")
```

---

## Frequently Modified Code

### Areas Where Changes Are Common

**1. Configuration Adjustments (master_config.json)**
- Symbol lists
- Feature tier enablement
- Baseline model selection
- Data acquisition parameters
- Metric selections

**2. Feature Engineering (features/)**
- Adding new technical indicators
- Adjusting lookback periods
- Enabling/disabling tier-3 features
- Adding signal processing decompositions

**3. Baseline Model Tuning (baselines/)**
- Ridge regression alpha parameter
- ARIMA order (currently fixed at 1,1,1)
- Feature selections for each baseline
- Training hyperparameters

**4. Threshold Values (preprocessing/data_cleaning/)**
- Spike threshold (currently ±20%)
- Max consecutive missing days (currently 2)
- Min trading days requirement (currently 2,500)
- OHLC validation tolerance

**5. Data Split Ratios (preprocessing/data_splitter.py)**
- Train/validation/test percentages (currently 70/15/15)
- Alternative stratification strategies

**6. Visualization Settings (reporting/)**
- Chart colors and styles
- Dashboard layout
- Output formats (HTML, PNG, PDF)

### Code with Minimal Changes Needed

- Core pipeline orchestration (pipeline.py)
- Data adapter implementations (if using same APIs)
- Phase sequencing logic
- Fundamental feature computation algorithms

---

## Technical Debt & Future Improvements

### Known Limitations (Current Stage)

1. **Sequential Symbol Processing**
   - Current: Processes symbols sequentially
   - Impact: Slow for large portfolios (100+ symbols)
   - Solution: Implement parallel processing (ThreadPoolExecutor, Ray)
   - Priority: Medium (after core functionality stable)

2. **No Advanced Time Series Validation**
   - Current: Basic gap and spike detection
   - Missing: Seasonal decomposition validation, outlier detection (IQR, Mahalanobis)
   - Impact: May miss subtle data quality issues
   - Solution: Add advanced statistical tests
   - Priority: Medium

3. **Limited Fallback Strategies**
   - Current: Only 2 data sources (IEX, yfinance)
   - Missing: Bloomberg, Quandl, OANDA, etc.
   - Impact: Limited options if both sources unavailable
   - Solution: Add more adapters (modular, easy to extend)
   - Priority: Low (current sources sufficient)

4. **No Real-Time Data Support**
   - Current: Daily OHLCV only
   - Missing: Intraday data, tick-level data, streaming
   - Impact: Cannot support high-frequency trading strategies
   - Solution: Add real-time data layer (Phase 2-3)
   - Priority: Low (Stage 1 focused on daily data)

5. **Fixed Hyperparameters**
   - Current: ARIMA(1,1,1), RSI(14), Bollinger(20,2)
   - Missing: Auto-tuning, cross-validation, Bayesian optimization
   - Impact: May not be optimal for all symbols
   - Solution: Add hyperparameter tuning module
   - Priority: Medium (after ablation studies)

6. **Single Scaler Type**
   - Current: StandardScaler only
   - Missing: MinMaxScaler, RobustScaler, QuantileTransformer
   - Impact: May not handle heavy outliers well
   - Solution: Make scaler configurable
   - Priority: Low

### Planned Improvements (Roadmap)

**Stage 2 (Model Development):**
- [ ] Implement LSTM/GRU encoder-decoder architecture
- [ ] Add attention mechanisms for interpretability
- [ ] Integrate IJF-F optimization for hyperparameter tuning
- [ ] Implement transfer learning across symbols/sectors

**Stage 3 (Scalability & Deployment):**
- [ ] Parallelize symbol processing (Ray/Dask)
- [ ] Add distributed compute support (Spark)
- [ ] Implement model serving (FastAPI, Docker)
- [ ] Add real-time prediction pipeline

**Stage 4 (Advanced Features):**
- [ ] Add graph neural networks for sector/market relationships
- [ ] Implement reinforcement learning for portfolio optimization
- [ ] Add ensemble learning (stacking, blending)
- [ ] Integrate sentiment analysis from news/social media

### Performance Optimization Opportunities

1. **Vectorization:** Replace loops with NumPy operations (already mostly done)
2. **Caching:** Cache downloaded data and computed features (disk cache layer)
3. **Lazy Loading:** Load features only when needed
4. **GPU Acceleration:** Use CuPy for large matrix operations
5. **Numba JIT:** Compile hot spots with Numba for 10-100x speedup

### Code Quality Improvements

1. **Type Hints:** Add comprehensive type annotations (mypy compliance)
2. **Documentation:** Docstring coverage 100% (NumPy/Google style)
3. **Error Messages:** More descriptive, actionable error messages
4. **Logging:** Add DEBUG-level logging for troubleshooting
5. **Testing:** Increase coverage to 90%+ across all modules
6. **Code Review:** Establish review process before merges

---

## Summary

This ARCHITECTURE.md document provides a comprehensive blueprint for understanding, maintaining, and extending the Stock Market Forecasting System. Key takeaways:

1. **Modular Design:** Each layer and module has clear responsibilities; extensibility via adapters/strategies
2. **Reproducibility First:** Seeds, configs, and artifacts versioned; full lineage tracked
3. **Data Integrity:** Strict temporal order, leakage detection, quality gates at each phase
4. **Scalability:** Horizontal scaling supported; bottlenecks identified and documented
5. **Maintainability:** Clear code organization, comprehensive testing, detailed documentation

For further information:
- **Data Pipeline:** See DATA_GUIDE.md
- **Usage Examples:** See EXPERIMENTS.md
- **Development Status:** See CONTINUATION_GUIDE.md
- **Troubleshooting:** See TROUBLESHOOTING.md
- **Code Documentation:** Embedded NumPy/Google-style docstrings in all modules

---

**Last Updated:** 2024-01-19  
**Status:** Stage 1 Complete - Ready for Model Development (Phase 14+)
