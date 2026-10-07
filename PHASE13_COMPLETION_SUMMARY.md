# Phase 13: Baseline Models - Completion Summary

**Status:** Complete  
**Tasks:** 13.1-13.8  
**Test result:** 22 passed across Phases 11-13

## Implemented

- `BaselineModel` provides a shared fit/predict/evaluate contract and MAE, RMSE, and directional-accuracy metrics.
- `RandomWalkBaseline` predicts the latest observed return, including rolling one-step predictions from prior observed returns.
- `ARIMABaseline` fits statsmodels ARIMA(1,1,1) on training closes and forecasts close levels. The manager converts forecasts to returns so all baselines are evaluated on the same target.
- `LinearRegressionBaseline` fits return targets from Tier-1 features and reports interpretable coefficients.
- `RidgeRegressionBaseline` performs five-fold `RidgeCV` selection on training data, optionally selects the final alpha by validation MSE, and refits on training data only.
- `HistoricalMeanBaseline` predicts the training-period mean return.
- `BaselineManager.train_and_evaluate_all()` fits all five models, evaluates validation and test forecasts, and persists joblib models, per-model metadata, and `baseline_results.json`. Metadata records training dates, feature sets, hyperparameters, validation performance, and training-only fit provenance.

## Verification

```text
python -m pytest baselines/test_baselines.py preprocessing/test_artifact_manager.py preprocessing/test_data_splitter.py -q
```

Result: **22 passed**. Tests cover predictions and metrics, ARIMA fitting/forecasting, regression coefficients, Ridge validation alpha tuning, feature/target date alignment, and artifact persistence.