"""Tests for Phase 9 signal-processing features and causality checks."""

import numpy as np
import pandas as pd
import pytest

from features.base_features import FeatureModule
from features.feature_orchestrator import FeatureGrouping, FeatureOrchestrator
from features.signal_processing import (
    KalmanFilterFeature,
    SSAFeature,
    SignalProcessingCausalityChecker,
    WaveletFeature,
)


@pytest.fixture
def price_data():
    dates = pd.date_range('2023-01-01', periods=120, freq='D')
    returns = np.random.default_rng(21).normal(0.0005, 0.012, len(dates))
    close = 100 * np.exp(np.cumsum(returns))
    return pd.DataFrame({'Close': close}, index=dates)


def test_wavelet_decomposes_trailing_log_prices(price_data):
    feature = WaveletFeature()
    result = feature.compute(price_data)

    assert result.index.equals(price_data.index)
    assert result.columns.tolist() == [
        'wavelet_approximation',
        'wavelet_detail_1',
        'wavelet_detail_2',
        'wavelet_detail_3',
    ]
    assert result.iloc[:63].isna().all().all()
    assert np.isfinite(result.iloc[63:].to_numpy()).all()
    assert feature.validate(result) == (True, [])


def test_wavelet_rejects_level_beyond_window_capacity():
    with pytest.raises(ValueError, match='exceeds maximum'):
        WaveletFeature({'window': 16, 'level': 4})


def test_ssa_emits_rank_one_trend_and_residual(price_data):
    feature = SSAFeature({'window': 32, 'embedding_dimension': 8})
    result = feature.compute(price_data)

    assert result.columns.tolist() == ['ssa_trend', 'ssa_residual']
    assert result.iloc[:31].isna().all().all()
    assert np.isfinite(result.iloc[31:].to_numpy()).all()
    np.testing.assert_allclose(
        result['ssa_trend'].iloc[31:] + result['ssa_residual'].iloc[31:],
        np.log(price_data['Close'].iloc[31:]),
    )


def test_kalman_filter_is_finite_and_recursive(price_data):
    feature = KalmanFilterFeature()
    result = feature.compute(price_data)

    assert result.columns.tolist() == [
        'kalman_level', 'kalman_innovation_zscore', 'kalman_variance'
    ]
    assert np.isfinite(result.to_numpy()).all()
    assert np.all(result['kalman_variance'].to_numpy() >= 0)
    assert result['kalman_variance'].iloc[0] > result['kalman_variance'].iloc[-1]
    assert feature.validate(result) == (True, [])


@pytest.mark.parametrize('feature', [
    WaveletFeature({'window': 32, 'level': 2}),
    SSAFeature({'window': 32, 'embedding_dimension': 8}),
    KalmanFilterFeature(),
])
def test_signal_features_pass_future_perturbation_check(feature, price_data):
    is_causal, issues = SignalProcessingCausalityChecker().check(feature, price_data)

    assert is_causal, issues


def test_causality_checker_detects_future_shift(price_data):
    class FutureLeakFeature(FeatureModule):
        def __init__(self):
            super().__init__(name='future_leak', tier=4)

        def compute(self, df, fit_data=None):
            return pd.DataFrame({'future_close': df['Close'].shift(-1)}, index=df.index)

        def validate(self, features):
            return True, []

    is_causal, issues = SignalProcessingCausalityChecker().check(
        FutureLeakFeature(), price_data
    )

    assert not is_causal
    assert issues


def test_signal_features_integrate_with_orchestrator(price_data):
    orchestrator = FeatureOrchestrator(config={'include_signal_processing': True})
    orchestrator.register_module(
        KalmanFilterFeature(), FeatureGrouping.SIGNAL_PROCESSING
    )

    features, manifest = orchestrator.compute_all_features(
        symbol='TEST', ohlcv_df=price_data
    )

    assert 'kalman_level' in features.columns
    assert 'kalman_innovation_zscore' in features.columns
    assert manifest.total_features == 1
    assert manifest.features[0].grouping == FeatureGrouping.SIGNAL_PROCESSING


@pytest.mark.parametrize('feature', [
    WaveletFeature({'window': 32, 'level': 2}),
    SSAFeature({'window': 32, 'embedding_dimension': 8}),
    KalmanFilterFeature(),
])
def test_features_require_positive_finite_close(feature, price_data):
    invalid = price_data.copy()
    invalid.iloc[10, invalid.columns.get_loc('Close')] = 0

    with pytest.raises(ValueError, match='finite and greater than zero'):
        feature.compute(invalid)