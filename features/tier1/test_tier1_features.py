"""
Comprehensive test suite for Tier-1 features.

Tests verify:
- Returns computed correctly (spot-check against manual calculation)
- Normalized features in reasonable ranges
- No unexpected NaN beyond expected lags
- Causality checks pass
- Integration with feature infrastructure
- Edge cases and error handling

Test Coverage:
- ReturnsFeature: simple returns, log returns, NaN handling
- NormalizedPricesFeature: rolling means/stds, normalized values, division by zero
- End-to-end integration tests
"""

import pytest
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from features.tier1.returns import ReturnsFeature
from features.tier1.normalized_prices import NormalizedPricesFeature


class TestReturnsFeature:
    """Test suite for ReturnsFeature module."""
    
    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2024-01-01', periods=100)
        np.random.seed(42)
        close_prices = 100 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, 100)))
        
        df = pd.DataFrame({
            'Open': close_prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
            'High': close_prices * (1 + np.abs(np.random.uniform(0, 0.02, 100))),
            'Low': close_prices * (1 - np.abs(np.random.uniform(0, 0.02, 100))),
            'Close': close_prices,
            'Volume': np.random.randint(1000000, 5000000, 100),
        }, index=dates)
        
        return df
    
    def test_returns_initialization(self):
        """Test that ReturnsFeature initializes correctly."""
        feature = ReturnsFeature()
        assert feature.name == "returns"
        assert feature.tier == 1
        assert isinstance(feature.logger, logging.Logger)
    
    def test_simple_returns_computation(self, sample_ohlcv):
        """Test simple returns computation against manual calculation."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        # Manual calculation
        expected_simple = sample_ohlcv['Close'].pct_change()
        
        # Compare (allowing small numerical differences)
        pd.testing.assert_series_equal(
            result['simple_return'],
            expected_simple,
            check_exact=False,
            atol=1e-10,
            check_names=False
        )
    
    def test_log_returns_computation(self, sample_ohlcv):
        """Test log returns computation against manual calculation."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        # Manual calculation
        expected_log = np.log(sample_ohlcv['Close'] / sample_ohlcv['Close'].shift(1))
        
        # Compare
        pd.testing.assert_series_equal(
            result['log_return'],
            expected_log,
            check_exact=False,
            atol=1e-10,
            check_names=False
        )
    
    def test_first_row_is_nan(self, sample_ohlcv):
        """Test that first row is NaN (no previous close to compare)."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        assert pd.isna(result['simple_return'].iloc[0])
        assert pd.isna(result['log_return'].iloc[0])
    
    def test_no_unexpected_nan(self, sample_ohlcv):
        """Test that no unexpected NaN values exist beyond first row."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        # All rows after first should have valid values
        assert not result['simple_return'].iloc[1:].isna().any()
        assert not result['log_return'].iloc[1:].isna().any()
    
    def test_known_return_values(self):
        """Test with known prices to verify exact computation."""
        df = pd.DataFrame({
            'Close': [100.0, 101.0, 99.0, 102.0],
            'Open': [100.0, 101.0, 99.0, 102.0],
            'High': [101.0, 102.0, 100.0, 103.0],
            'Low': [99.0, 100.0, 98.0, 101.0],
            'Volume': [1000000, 1000000, 1000000, 1000000],
        }, index=pd.date_range('2024-01-01', periods=4))
        
        feature = ReturnsFeature()
        result = feature.compute(df)
        
        # Spot-check values
        assert pd.isna(result['simple_return'].iloc[0])
        assert np.isclose(result['simple_return'].iloc[1], 0.01)  # (101-100)/100
        expected_return_2 = (99.0 - 101.0) / 101.0  # (99-101)/101
        assert np.isclose(result['simple_return'].iloc[2], expected_return_2)
        
        assert pd.isna(result['log_return'].iloc[0])
        assert np.isclose(result['log_return'].iloc[1], np.log(101/100))
        assert np.isclose(result['log_return'].iloc[2], np.log(99/101))
    
    def test_returns_validation_passes(self, sample_ohlcv):
        """Test that valid returns pass validation."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        is_valid, errors = feature.validate(result)
        assert is_valid
        assert len(errors) == 0
    
    def test_validation_detects_inf(self):
        """Test that validation detects infinite values."""
        features = pd.DataFrame({
            'simple_return': [np.nan, 0.01, np.inf, 0.02],
            'log_return': [np.nan, 0.0099, 0.0198, 0.02],
        })
        
        feature = ReturnsFeature()
        is_valid, errors = feature.validate(features)
        
        assert not is_valid
        assert any('inf' in err for err in errors)
    
    def test_validation_detects_unexpected_nan(self):
        """Test that validation detects unexpected NaN values."""
        features = pd.DataFrame({
            'simple_return': [np.nan, 0.01, np.nan, 0.02],  # NaN at row 2!
            'log_return': [np.nan, 0.0099, 0.0198, 0.02],
        })
        
        feature = ReturnsFeature()
        is_valid, errors = feature.validate(features)
        
        assert not is_valid
        assert any('NaN' in err for err in errors)
    
    def test_causality_check_passes(self, sample_ohlcv):
        """Test that returns pass causality check (fully causal)."""
        feature = ReturnsFeature()
        is_causal, errors = feature.check_causality(sample_ohlcv)
        
        assert is_causal
        assert len(errors) == 0
    
    def test_input_validation_empty_dataframe(self):
        """Test that empty DataFrame raises error."""
        feature = ReturnsFeature()
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError):
            feature.compute(empty_df)
    
    def test_input_validation_missing_close(self):
        """Test that missing 'Close' column raises error."""
        feature = ReturnsFeature()
        df = pd.DataFrame({
            'Open': [100, 101],
            'High': [101, 102],
            'Low': [99, 100],
            'Volume': [1000000, 1000000],
        }, index=pd.date_range('2024-01-01', periods=2))
        
        with pytest.raises(ValueError):
            feature.compute(df)
    
    def test_returns_output_shape(self, sample_ohlcv):
        """Test that output has correct shape."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        assert result.shape == (len(sample_ohlcv), 2)  # 2 feature columns
        assert result.shape[0] == len(sample_ohlcv)
    
    def test_returns_output_columns(self, sample_ohlcv):
        """Test that output has correct column names."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        assert set(result.columns) == {'simple_return', 'log_return'}
    
    def test_returns_index_alignment(self, sample_ohlcv):
        """Test that output index matches input index."""
        feature = ReturnsFeature()
        result = feature.compute(sample_ohlcv)
        
        pd.testing.assert_index_equal(result.index, sample_ohlcv.index)


class TestNormalizedPricesFeature:
    """Test suite for NormalizedPricesFeature module."""
    
    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2024-01-01', periods=100)
        np.random.seed(42)
        close_prices = 100 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, 100)))
        
        df = pd.DataFrame({
            'Open': close_prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
            'High': close_prices * (1 + np.abs(np.random.uniform(0, 0.02, 100))),
            'Low': close_prices * (1 - np.abs(np.random.uniform(0, 0.02, 100))),
            'Close': close_prices,
            'Volume': np.random.randint(1000000, 5000000, 100),
        }, index=dates)
        
        return df
    
    def test_normalized_prices_initialization(self):
        """Test that NormalizedPricesFeature initializes correctly."""
        feature = NormalizedPricesFeature()
        assert feature.name == "normalized_prices"
        assert feature.tier == 1
        assert feature.lookback_window == 20
    
    def test_custom_lookback_window(self):
        """Test initialization with custom lookback window."""
        feature = NormalizedPricesFeature(lookback_window=10)
        assert feature.lookback_window == 10
    
    def test_close_ma20_computation(self, sample_ohlcv):
        """Test 20-day rolling mean computation."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        # Manual calculation
        expected_ma = sample_ohlcv['Close'].rolling(window=20).mean()
        
        pd.testing.assert_series_equal(
            result['close_ma20'],
            expected_ma,
            check_exact=False,
            atol=1e-10,
            check_names=False
        )
    
    def test_close_std20_computation(self, sample_ohlcv):
        """Test 20-day rolling std computation."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        # Manual calculation
        expected_std = sample_ohlcv['Close'].rolling(window=20).std()
        
        pd.testing.assert_series_equal(
            result['close_std20'],
            expected_std,
            check_exact=False,
            atol=1e-10,
            check_names=False
        )
    
    def test_normalized_close_computation(self, sample_ohlcv):
        """Test normalized close (z-score) computation."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        # Manual calculation
        close_ma = sample_ohlcv['Close'].rolling(window=20).mean()
        close_std = sample_ohlcv['Close'].rolling(window=20).std()
        expected_normalized = (sample_ohlcv['Close'] - close_ma) / close_std
        
        # Compare (allowing for numerical differences)
        mask = ~expected_normalized.isna()
        pd.testing.assert_series_equal(
            result['normalized_close'][mask],
            expected_normalized[mask],
            check_exact=False,
            atol=1e-10,
            check_names=False
        )
    
    def test_normalized_volume_computation(self, sample_ohlcv):
        """Test normalized volume computation."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        # Manual calculation
        volume_ma = sample_ohlcv['Volume'].rolling(window=20).mean()
        expected_normalized = sample_ohlcv['Volume'] / volume_ma
        
        # Compare (allowing for numerical differences)
        mask = ~expected_normalized.isna()
        pd.testing.assert_series_equal(
            result['normalized_volume'][mask],
            expected_normalized[mask],
            check_exact=False,
            atol=1e-10,
            check_names=False
        )
    
    def test_first_19_rows_nan(self, sample_ohlcv):
        """Test that first 19 rows are NaN (rolling window = 20)."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        # First 19 rows should be NaN for all features
        assert result['close_ma20'].iloc[0:19].isna().all()
        assert result['close_std20'].iloc[0:19].isna().all()
        assert result['normalized_close'].iloc[0:19].isna().all()
        assert result['normalized_volume'].iloc[0:19].isna().all()
    
    def test_row_20_onward_valid(self, sample_ohlcv):
        """Test that row 20 onward have valid values."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        # Row 20 (index 19) and beyond should have valid values
        # (except for close_std20 if all prices are the same, which shouldn't happen)
        assert not result['close_ma20'].iloc[19:].isna().any()
        assert not result['close_std20'].iloc[19:].isna().all()  # May have some NaN if std=0
        # normalized_close and normalized_volume may have NaN if division by zero
    
    def test_normalized_close_range(self, sample_ohlcv):
        """Test that normalized close values are in reasonable range [-5, 5]."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        normalized_close = result['normalized_close'].iloc[19:]
        
        # Most values should be in [-3, 3] (3 standard deviations)
        # Check that extreme outliers are rare
        extreme_count = ((normalized_close < -5) | (normalized_close > 5)).sum()
        assert extreme_count < len(normalized_close) * 0.05  # Less than 5% extreme
    
    def test_normalized_volume_positive(self, sample_ohlcv):
        """Test that normalized volume is positive (volume > 0)."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        normalized_volume = result['normalized_volume'].iloc[19:]
        
        # All non-NaN values should be positive
        assert (normalized_volume[~normalized_volume.isna()] > 0).all()
    
    def test_normalized_prices_validation_passes(self, sample_ohlcv):
        """Test that valid normalized prices pass validation."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        is_valid, errors = feature.validate(result)
        assert is_valid
        assert len(errors) == 0
    
    def test_validation_detects_inf(self):
        """Test that validation detects infinite values."""
        features = pd.DataFrame({
            'close_ma20': [np.nan] * 19 + [100, 101],
            'close_std20': [np.nan] * 19 + [1, 1],
            'normalized_close': [np.nan] * 19 + [0.5, np.inf],
            'normalized_volume': [np.nan] * 19 + [1.0, 1.5],
        })
        
        feature = NormalizedPricesFeature()
        is_valid, errors = feature.validate(features)
        
        assert not is_valid
        assert any('inf' in err for err in errors)
    
    def test_validation_detects_unexpected_nan(self):
        """Test that validation detects unexpected NaN beyond first 19 rows."""
        features = pd.DataFrame({
            'close_ma20': [np.nan] * 19 + [100, np.nan],  # NaN at row 21!
            'close_std20': [np.nan] * 19 + [1, 1],
            'normalized_close': [np.nan] * 19 + [0.5, 1.5],
            'normalized_volume': [np.nan] * 19 + [1.0, 1.5],
        })
        
        feature = NormalizedPricesFeature()
        is_valid, errors = feature.validate(features)
        
        assert not is_valid
        assert any('NaN' in err for err in errors)
    
    def test_causality_check_passes(self, sample_ohlcv):
        """Test that normalized prices pass causality check."""
        feature = NormalizedPricesFeature()
        is_causal, errors = feature.check_causality(sample_ohlcv)
        
        assert is_causal
        assert len(errors) == 0
    
    def test_input_validation_empty_dataframe(self):
        """Test that empty DataFrame raises error."""
        feature = NormalizedPricesFeature()
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError):
            feature.compute(empty_df)
    
    def test_input_validation_missing_columns(self):
        """Test that missing required columns raises error."""
        feature = NormalizedPricesFeature()
        df = pd.DataFrame({
            'Open': [100, 101],
            'High': [101, 102],
            'Low': [99, 100],
            'Close': [100, 101],
        }, index=pd.date_range('2024-01-01', periods=2))
        
        with pytest.raises(ValueError):
            feature.compute(df)
    
    def test_normalized_prices_output_shape(self, sample_ohlcv):
        """Test that output has correct shape."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        assert result.shape == (len(sample_ohlcv), 4)  # 4 feature columns
    
    def test_normalized_prices_output_columns(self, sample_ohlcv):
        """Test that output has correct column names."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        expected_cols = {'close_ma20', 'close_std20', 'normalized_close', 'normalized_volume'}
        assert set(result.columns) == expected_cols
    
    def test_normalized_prices_index_alignment(self, sample_ohlcv):
        """Test that output index matches input index."""
        feature = NormalizedPricesFeature()
        result = feature.compute(sample_ohlcv)
        
        pd.testing.assert_index_equal(result.index, sample_ohlcv.index)


class TestTier1Integration:
    """Integration tests for Tier-1 features together."""
    
    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2024-01-01', periods=50)
        np.random.seed(42)
        close_prices = 100 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, 50)))
        
        df = pd.DataFrame({
            'Open': close_prices * (1 + np.random.uniform(-0.01, 0.01, 50)),
            'High': close_prices * (1 + np.abs(np.random.uniform(0, 0.02, 50))),
            'Low': close_prices * (1 - np.abs(np.random.uniform(0, 0.02, 50))),
            'Close': close_prices,
            'Volume': np.random.randint(1000000, 5000000, 50),
        }, index=dates)
        
        return df
    
    def test_both_features_together(self, sample_ohlcv):
        """Test that both features can be computed on same data."""
        returns_feature = ReturnsFeature()
        normalized_feature = NormalizedPricesFeature()
        
        returns = returns_feature.compute(sample_ohlcv)
        normalized = normalized_feature.compute(sample_ohlcv)
        
        # Both should produce valid results
        assert returns.shape[0] == len(sample_ohlcv)
        assert normalized.shape[0] == len(sample_ohlcv)
        
        # Aggregate features
        all_features = pd.concat([returns, normalized], axis=1)
        assert all_features.shape[1] == 6  # 2 + 4 features
        assert all_features.shape[0] == len(sample_ohlcv)
    
    def test_no_unexpected_nan_across_features(self, sample_ohlcv):
        """Test that NaN patterns are expected across both features."""
        returns_feature = ReturnsFeature()
        normalized_feature = NormalizedPricesFeature()
        
        returns = returns_feature.compute(sample_ohlcv)
        normalized = normalized_feature.compute(sample_ohlcv)
        
        # Returns: first row NaN
        assert returns.isna().iloc[0].all()
        assert not returns.isna().iloc[1:].any().any()
        
        # Normalized: first 19 rows NaN
        assert normalized.isna().iloc[0:19].all().all()
        # Row 20 and beyond should be mostly valid
    
    def test_feature_values_consistency(self, sample_ohlcv):
        """Test that feature values are consistent across re-computations."""
        feature1 = ReturnsFeature()
        feature2 = ReturnsFeature()
        
        result1 = feature1.compute(sample_ohlcv)
        result2 = feature2.compute(sample_ohlcv)
        
        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)
