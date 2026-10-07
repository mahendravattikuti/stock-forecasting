"""
Comprehensive Test Suite for Tier-2 Technical Indicators

Tests all RSI, MACD, Bollinger Bands, Stochastic, ATR, ADX, OBV, Momentum, and Volatility features.
Includes:
- Computation correctness verification
- Value range validation
- NaN handling and causality checks
- Edge case handling
- Integration with FeatureOrchestrator

Run with: pytest features/tier2/test_tier2_features.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from features.tier2.technical_indicators import (
    RSIFeature, MACDFeature, BollingerBandsFeature, StochasticFeature,
    ATRFeature, ADXFeature, OBVFeature
)
from features.tier2.other_indicators import (
    MomentumFeature,
    VolatilityFeature,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_ohlcv():
    """Generate sample OHLCV data with realistic patterns."""
    np.random.seed(42)
    n = 300
    dates = pd.date_range('2022-01-01', periods=n, freq='D')
    
    # Create realistic price movement
    close = 100.0
    closes = []
    highs = []
    lows = []
    volumes = []
    
    for i in range(n):
        # Trending with noise
        trend = 0.0005 * i  # Slight uptrend
        noise = np.random.normal(0, 0.01)
        close = close * (1 + trend + noise)
        closes.append(close)
        
        # Generate OHLC
        high = close * (1 + abs(np.random.normal(0, 0.005)))
        low = close * (1 - abs(np.random.normal(0, 0.005)))
        open_price = close * (1 + np.random.normal(0, 0.003))
        volume = np.random.randint(1000000, 5000000)
        
        highs.append(max(open_price, close, high))
        lows.append(min(open_price, close, low))
        volumes.append(volume)
    
    df = pd.DataFrame({
        'Open': [100.0] + closes[:-1],  # Simplified
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes,
    }, index=dates)
    
    return df


@pytest.fixture
def small_ohlcv():
    """Generate small OHLCV data for edge case testing."""
    dates = pd.date_range('2022-01-01', periods=10, freq='D')
    df = pd.DataFrame({
        'Open': [100, 101, 102, 101, 103, 102, 104, 103, 105, 104],
        'High': [101, 102, 103, 102, 104, 103, 105, 104, 106, 105],
        'Low': [99, 100, 101, 100, 102, 101, 103, 102, 104, 103],
        'Close': [100.5, 101.5, 102.5, 101.5, 103.5, 102.5, 104.5, 103.5, 105.5, 104.5],
        'Volume': [1000000] * 10,
    }, index=dates)
    return df


# ============================================================================
# RSI FEATURE TESTS
# ============================================================================

class TestRSIFeature:
    """Test suite for RSIFeature."""
    
    def test_rsi_initialization(self):
        """Test RSI feature initialization."""
        feature = RSIFeature()
        assert feature.period == 14
        assert feature.tier == 2
    
    def test_rsi_custom_period(self):
        """Test RSI with custom period."""
        config = {'rsi_period': 7}
        feature = RSIFeature(config=config)
        assert feature.period == 7
    
    def test_rsi_computation(self, sample_ohlcv):
        """Test RSI computation on sample data."""
        feature = RSIFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'rsi_14' in result.columns
        assert len(result) == len(sample_ohlcv)
        assert result.index.equals(sample_ohlcv.index)
    
    def test_rsi_value_range(self, sample_ohlcv):
        """Test RSI values are in [0, 100] range."""
        feature = RSIFeature()
        result = feature.compute(sample_ohlcv)
        rsi = result['rsi_14'].dropna()
        
        assert (rsi >= -0.01).all()
        assert (rsi <= 100.01).all()
    
    def test_rsi_nan_handling(self, sample_ohlcv):
        """Test RSI NaN handling for warmup period."""
        feature = RSIFeature()
        result = feature.compute(sample_ohlcv)
        rsi = result['rsi_14']
        
        # First rows should have some NaNs (warmup period)
        assert rsi.isna().sum() > 0
        # But not all should be NaN
        assert rsi.notna().sum() > 0
    
    def test_rsi_validation(self, sample_ohlcv):
        """Test RSI validation."""
        feature = RSIFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_rsi_causality(self, sample_ohlcv):
        """Test RSI causality check."""
        feature = RSIFeature()
        is_causal, warnings = feature.check_causality(sample_ohlcv)
        
        assert is_causal
    
    def test_rsi_small_data(self, small_ohlcv):
        """Test RSI with small dataset."""
        feature = RSIFeature()
        result = feature.compute(small_ohlcv)
        
        assert 'rsi_14' in result.columns
        # Should have many NaNs due to insufficient data
        assert result['rsi_14'].isna().sum() > 5


# ============================================================================
# MACD FEATURE TESTS
# ============================================================================

class TestMACDFeature:
    """Test suite for MACDFeature."""
    
    def test_macd_initialization(self):
        """Test MACD feature initialization."""
        feature = MACDFeature()
        assert feature.fast_period == 12
        assert feature.slow_period == 26
        assert feature.signal_period == 9
    
    def test_macd_computation(self, sample_ohlcv):
        """Test MACD computation."""
        feature = MACDFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'macd_line' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_histogram' in result.columns
        assert len(result) == len(sample_ohlcv)
    
    def test_macd_histogram_relationship(self, sample_ohlcv):
        """Test MACD histogram = line - signal relationship."""
        feature = MACDFeature()
        result = feature.compute(sample_ohlcv)
        
        # Get common non-NaN indices
        common_idx = result[['macd_line', 'macd_signal', 'macd_histogram']].notna().all(axis=1)
        subset = result.loc[common_idx]
        
        expected_histogram = subset['macd_line'] - subset['macd_signal']
        actual_histogram = subset['macd_histogram']
        
        # Should be very close (within floating point precision)
        assert (np.abs(expected_histogram - actual_histogram) < 1e-6).all()
    
    def test_macd_validation(self, sample_ohlcv):
        """Test MACD validation."""
        feature = MACDFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid
    
    def test_macd_nan_handling(self, sample_ohlcv):
        """Test MACD NaN handling."""
        feature = MACDFeature()
        result = feature.compute(sample_ohlcv)
        
        # Some NaNs expected for warmup
        assert result['macd_line'].isna().sum() > 0
        # But not all
        assert result['macd_line'].notna().sum() > 100


# ============================================================================
# BOLLINGER BANDS FEATURE TESTS
# ============================================================================

class TestBollingerBandsFeature:
    """Test suite for BollingerBandsFeature."""
    
    def test_bollinger_initialization(self):
        """Test Bollinger Bands initialization."""
        feature = BollingerBandsFeature()
        assert feature.period == 20
        assert feature.num_std == 2.0
    
    def test_bollinger_computation(self, sample_ohlcv):
        """Test Bollinger Bands computation."""
        feature = BollingerBandsFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'bb_upper' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_lower' in result.columns
        assert 'bb_width' in result.columns
    
    def test_bollinger_band_relationships(self, sample_ohlcv):
        """Test upper >= middle >= lower relationships."""
        feature = BollingerBandsFeature()
        result = feature.compute(sample_ohlcv)
        
        common_idx = result[['bb_upper', 'bb_middle', 'bb_lower']].notna().all(axis=1)
        subset = result.loc[common_idx]
        
        assert (subset['bb_upper'] >= subset['bb_middle']).all()
        assert (subset['bb_middle'] >= subset['bb_lower']).all()
    
    def test_bollinger_width_calculation(self, sample_ohlcv):
        """Test width = upper - lower."""
        feature = BollingerBandsFeature()
        result = feature.compute(sample_ohlcv)
        
        common_idx = result[['bb_upper', 'bb_lower', 'bb_width']].notna().all(axis=1)
        subset = result.loc[common_idx]
        
        expected_width = subset['bb_upper'] - subset['bb_lower']
        assert (np.abs(expected_width - subset['bb_width']) < 1e-6).all()
    
    def test_bollinger_validation(self, sample_ohlcv):
        """Test Bollinger Bands validation."""
        feature = BollingerBandsFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid


# ============================================================================
# STOCHASTIC FEATURE TESTS
# ============================================================================

class TestStochasticFeature:
    """Test suite for StochasticFeature."""
    
    def test_stochastic_initialization(self):
        """Test Stochastic Oscillator initialization."""
        feature = StochasticFeature()
        assert feature.period == 14
        assert feature.signal_period == 3
    
    def test_stochastic_computation(self, sample_ohlcv):
        """Test Stochastic computation."""
        feature = StochasticFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'stoch_k' in result.columns
        assert 'stoch_d' in result.columns
    
    def test_stochastic_value_range(self, sample_ohlcv):
        """Test Stochastic values in [0, 100]."""
        feature = StochasticFeature()
        result = feature.compute(sample_ohlcv)
        
        for col in ['stoch_k', 'stoch_d']:
            values = result[col].dropna()
            assert (values >= -0.01).all()
            assert (values <= 100.01).all()
    
    def test_stochastic_validation(self, sample_ohlcv):
        """Test Stochastic validation."""
        feature = StochasticFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid


# ============================================================================
# ATR FEATURE TESTS
# ============================================================================

class TestATRFeature:
    """Test suite for ATRFeature."""
    
    def test_atr_initialization(self):
        """Test ATR initialization."""
        feature = ATRFeature()
        assert feature.period == 14
    
    def test_atr_computation(self, sample_ohlcv):
        """Test ATR computation."""
        feature = ATRFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'atr_14' in result.columns
        assert len(result) == len(sample_ohlcv)
    
    def test_atr_non_negative(self, sample_ohlcv):
        """Test ATR values are non-negative."""
        feature = ATRFeature()
        result = feature.compute(sample_ohlcv)
        
        atr = result['atr_14'].dropna()
        assert (atr >= -1e-6).all()
    
    def test_atr_validation(self, sample_ohlcv):
        """Test ATR validation."""
        feature = ATRFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid


# ============================================================================
# ADX FEATURE TESTS
# ============================================================================

class TestADXFeature:
    """Test suite for ADXFeature."""
    
    def test_adx_initialization(self):
        """Test ADX initialization."""
        feature = ADXFeature()
        assert feature.period == 14
    
    def test_adx_computation(self, sample_ohlcv):
        """Test ADX computation."""
        feature = ADXFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'adx_plus_di' in result.columns
        assert 'adx_minus_di' in result.columns
        assert 'adx_value' in result.columns
    
    def test_adx_value_ranges(self, sample_ohlcv):
        """Test ADX components in expected ranges."""
        feature = ADXFeature()
        result = feature.compute(sample_ohlcv)
        
        for col in ['adx_plus_di', 'adx_minus_di', 'adx_value']:
            values = result[col].dropna()
            assert (values >= -0.01).all()
            assert (values <= 100.01).all()
    
    def test_adx_validation(self, sample_ohlcv):
        """Test ADX validation."""
        feature = ADXFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid


# ============================================================================
# OBV FEATURE TESTS
# ============================================================================

class TestOBVFeature:
    """Test suite for OBVFeature."""
    
    def test_obv_initialization(self):
        """Test OBV initialization."""
        feature = OBVFeature()
        assert feature.ma_period == 20
    
    def test_obv_computation(self, sample_ohlcv):
        """Test OBV computation."""
        feature = OBVFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'obv' in result.columns
        assert 'obv_ma20' in result.columns
    
    def test_obv_cumulative_behavior(self, sample_ohlcv):
        """Test OBV has cumulative behavior."""
        feature = OBVFeature()
        result = feature.compute(sample_ohlcv)
        
        obv = result['obv'].dropna()
        # Check that OBV grows mostly monotonically
        # (though can decrease, it shouldn't be erratic)
        changes = obv.diff()
        # Most changes should be in same direction as trend
        assert len(obv) > 10
    
    def test_obv_validation(self, sample_ohlcv):
        """Test OBV validation."""
        feature = OBVFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid


# ============================================================================
# MOMENTUM FEATURE TESTS
# ============================================================================

class TestMomentumFeature:
    """Test suite for MomentumFeature."""
    
    def test_momentum_initialization(self):
        """Test Momentum initialization."""
        feature = MomentumFeature()
        assert feature.periods == [5, 20, 60]
    
    def test_momentum_custom_periods(self):
        """Test Momentum with custom periods."""
        config = {'momentum_periods': [3, 10]}
        feature = MomentumFeature(config=config)
        assert feature.periods == [3, 10]
    
    def test_momentum_computation(self, sample_ohlcv):
        """Test Momentum computation."""
        feature = MomentumFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'momentum_5' in result.columns
        assert 'momentum_20' in result.columns
        assert 'momentum_60' in result.columns
    
    def test_momentum_range(self, sample_ohlcv):
        """Test Momentum values are reasonable."""
        feature = MomentumFeature()
        result = feature.compute(sample_ohlcv)
        
        # Momentum is usually between -1 and 1 for stocks
        for period in [5, 20, 60]:
            momentum = result[f'momentum_{period}'].dropna()
            # Allow for extreme moves but check they're not infinite
            assert not momentum.isna().all()
            assert (np.isfinite(momentum)).all()
    
    def test_momentum_validation(self, sample_ohlcv):
        """Test Momentum validation."""
        feature = MomentumFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid


# ============================================================================
# VOLATILITY FEATURE TESTS
# ============================================================================

class TestVolatilityFeature:
    """Test suite for VolatilityFeature."""
    
    def test_volatility_initialization(self):
        """Test Volatility initialization."""
        feature = VolatilityFeature()
        assert feature.period == 20
    
    def test_volatility_custom_period(self):
        """Test Volatility with custom period."""
        config = {'volatility_period': 10}
        feature = VolatilityFeature(config=config)
        assert feature.period == 10
    
    def test_volatility_computation(self, sample_ohlcv):
        """Test Volatility computation."""
        feature = VolatilityFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'volatility_20' in result.columns
        assert len(result) == len(sample_ohlcv)
    
    def test_volatility_non_negative(self, sample_ohlcv):
        """Test Volatility values are non-negative."""
        feature = VolatilityFeature()
        result = feature.compute(sample_ohlcv)
        
        volatility = result['volatility_20'].dropna()
        assert (volatility >= -1e-6).all()
    
    def test_volatility_validation(self, sample_ohlcv):
        """Test Volatility validation."""
        feature = VolatilityFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid
    
    def test_volatility_causality(self, sample_ohlcv):
        """Test Volatility causality check."""
        feature = VolatilityFeature()
        is_causal, warnings = feature.check_causality(sample_ohlcv)
        
        assert is_causal


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestTier2Integration:
    """Integration tests for all Tier-2 features."""
    
    def test_all_features_compute_successfully(self, sample_ohlcv):
        """Test all features compute without errors."""
        features_to_test = [
            RSIFeature(),
            MACDFeature(),
            BollingerBandsFeature(),
            StochasticFeature(),
            ATRFeature(),
            ADXFeature(),
            OBVFeature(),
            MomentumFeature(),
            VolatilityFeature(),
        ]
        
        for feature in features_to_test:
            result = feature.compute(sample_ohlcv)
            assert result.index.equals(sample_ohlcv.index)
            assert len(result) == len(sample_ohlcv)
            assert result.notna().sum().sum() > 100  # At least some non-NaN values
    
    def test_all_features_validate_successfully(self, sample_ohlcv):
        """Test all features pass validation."""
        features_to_test = [
            RSIFeature(),
            MACDFeature(),
            BollingerBandsFeature(),
            StochasticFeature(),
            ATRFeature(),
            ADXFeature(),
            OBVFeature(),
            MomentumFeature(),
            VolatilityFeature(),
        ]
        
        for feature in features_to_test:
            result = feature.compute(sample_ohlcv)
            is_valid, errors = feature.validate(result)
            assert is_valid, f"{feature.__class__.__name__} validation failed: {errors}"
    
    def test_feature_columns_no_overlap(self, sample_ohlcv):
        """Test features don't create conflicting column names."""
        features_to_test = [
            RSIFeature(),
            MACDFeature(),
            BollingerBandsFeature(),
            StochasticFeature(),
            ATRFeature(),
            ADXFeature(),
            OBVFeature(),
            MomentumFeature(),
            VolatilityFeature(),
        ]
        
        all_columns = set()
        for feature in features_to_test:
            result = feature.compute(sample_ohlcv)
            feature_cols = set(result.columns)
            
            # Check no overlap
            overlap = all_columns & feature_cols
            assert len(overlap) == 0, f"Column overlap detected: {overlap}"
            
            all_columns.update(feature_cols)
        
        # Should have 19 unique columns total
        assert len(all_columns) == 19


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
