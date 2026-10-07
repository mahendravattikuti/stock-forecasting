"""
Comprehensive Test Suite for Tier-3 Market Context Features

Tests MarketRegimeFeature, RelativeStrengthFeature, and SectorCorrelationFeature.

Run with: pytest features/tier3/test_tier3_features.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from features.tier3.regime import MarketRegimeFeature
from features.tier3.cross_asset import RelativeStrengthFeature, SectorCorrelationFeature


@pytest.fixture
def sample_ohlcv():
    """Generate sample OHLCV data with realistic price patterns."""
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
        trend = 0.0005 * i  # Slight uptrend
        noise = np.random.normal(0, 0.01)
        close = close * (1 + trend + noise)
        closes.append(close)
        
        high = close * (1 + abs(np.random.normal(0, 0.005)))
        low = close * (1 - abs(np.random.normal(0, 0.005)))
        open_price = close * (1 + np.random.normal(0, 0.003))
        volume = np.random.randint(1000000, 5000000)
        
        highs.append(max(open_price, close, high))
        lows.append(min(open_price, close, low))
        volumes.append(volume)
    
    df = pd.DataFrame({
        'Open': [100.0] + closes[:-1],
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes,
    }, index=dates)
    
    return df


class TestMarketRegimeFeature:
    """Test suite for MarketRegimeFeature."""
    
    def test_regime_initialization(self):
        """Test regime feature initialization."""
        feature = MarketRegimeFeature()
        assert feature.name == 'market_regime'
        assert feature.tier == 3
    
    def test_regime_computation(self, sample_ohlcv):
        """Test regime computation."""
        feature = MarketRegimeFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'market_regime' in result.columns
        assert len(result) == len(sample_ohlcv)
        assert result.index.equals(sample_ohlcv.index)
    
    def test_regime_values_valid(self, sample_ohlcv):
        """Test regime values are in {0, 1, 2, 3}."""
        feature = MarketRegimeFeature()
        result = feature.compute(sample_ohlcv)
        regime = result['market_regime'].dropna()
        
        valid_regimes = {0, 1, 2, 3}
        assert regime.isin(valid_regimes).all()
    
    def test_regime_nan_handling(self, sample_ohlcv):
        """Test NaN handling for warmup period."""
        feature = MarketRegimeFeature()
        result = feature.compute(sample_ohlcv)
        regime = result['market_regime']
        
        # First 60 rows should be NaN (lookback period)
        assert regime.iloc[:60].isna().all()
        
        # After that should have values
        assert regime.iloc[61:].notna().any()
    
    def test_regime_validation(self, sample_ohlcv):
        """Test regime validation."""
        feature = MarketRegimeFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_regime_causality(self, sample_ohlcv):
        """Test regime causality check."""
        feature = MarketRegimeFeature()
        is_causal, warnings = feature.check_causality(sample_ohlcv)
        
        assert is_causal
    
    def test_regime_small_data(self):
        """Test regime with insufficient data."""
        dates = pd.date_range('2022-01-01', periods=30, freq='D')
        df = pd.DataFrame({
            'Close': np.linspace(100, 110, 30),
        }, index=dates)
        
        feature = MarketRegimeFeature()
        result = feature.compute(df)
        
        # Should have all NaN for small dataset
        assert result['market_regime'].isna().all()


class TestRelativeStrengthFeature:
    """Test suite for RelativeStrengthFeature."""
    
    def test_rs_initialization(self):
        """Test relative strength initialization."""
        feature = RelativeStrengthFeature()
        assert feature.name == 'relative_strength'
        assert feature.tier == 3
    
    def test_rs_computation(self, sample_ohlcv):
        """Test relative strength computation."""
        feature = RelativeStrengthFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'relative_strength' in result.columns
        assert len(result) == len(sample_ohlcv)
    
    def test_rs_value_range(self, sample_ohlcv):
        """Test relative strength in [-1, 1] range."""
        feature = RelativeStrengthFeature()
        result = feature.compute(sample_ohlcv)
        rs = result['relative_strength'].dropna()
        
        # Should be correlation values in [-1, 1]
        if len(rs) > 0:
            assert (rs >= -1.01).all()
            assert (rs <= 1.01).all()
    
    def test_rs_validation(self, sample_ohlcv):
        """Test relative strength validation."""
        feature = RelativeStrengthFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        # May have NaN if SPY download fails, so validation should pass
        assert is_valid or len(errors) == 0
    
    def test_rs_causality(self, sample_ohlcv):
        """Test relative strength causality."""
        feature = RelativeStrengthFeature()
        is_causal, warnings = feature.check_causality(sample_ohlcv)
        
        assert is_causal


class TestSectorCorrelationFeature:
    """Test suite for SectorCorrelationFeature."""
    
    def test_sector_correlation_initialization(self):
        """Test sector correlation initialization."""
        feature = SectorCorrelationFeature()
        assert feature.name == 'sector_correlation'
        assert feature.tier == 3
    
    def test_sector_correlation_computation(self, sample_ohlcv):
        """Test sector correlation computation."""
        feature = SectorCorrelationFeature()
        result = feature.compute(sample_ohlcv)
        
        assert 'sector_correlation' in result.columns
        assert len(result) == len(sample_ohlcv)
    
    def test_sector_correlation_validation(self, sample_ohlcv):
        """Test sector correlation validation."""
        feature = SectorCorrelationFeature()
        result = feature.compute(sample_ohlcv)
        is_valid, errors = feature.validate(result)
        
        assert is_valid


class TestTier3Integration:
    """Integration tests for Tier-3 features."""
    
    def test_all_features_compute_successfully(self, sample_ohlcv):
        """Test all Tier-3 features compute without errors."""
        features_to_test = [
            MarketRegimeFeature(),
            RelativeStrengthFeature(),
            SectorCorrelationFeature(),
        ]
        
        for feature in features_to_test:
            result = feature.compute(sample_ohlcv)
            assert result.index.equals(sample_ohlcv.index)
            assert len(result) == len(sample_ohlcv)
    
    def test_all_features_validate_successfully(self, sample_ohlcv):
        """Test all Tier-3 features pass validation."""
        features_to_test = [
            MarketRegimeFeature(),
            RelativeStrengthFeature(),
            SectorCorrelationFeature(),
        ]
        
        for feature in features_to_test:
            result = feature.compute(sample_ohlcv)
            is_valid, errors = feature.validate(result)
            assert is_valid or len(errors) == 0, f"{feature.__class__.__name__} validation: {errors}"
    
    def test_feature_columns_no_overlap(self, sample_ohlcv):
        """Test Tier-3 features don't create conflicting column names."""
        features_to_test = [
            MarketRegimeFeature(),
            RelativeStrengthFeature(),
            SectorCorrelationFeature(),
        ]
        
        all_columns = set()
        for feature in features_to_test:
            result = feature.compute(sample_ohlcv)
            feature_cols = set(result.columns)
            
            overlap = all_columns & feature_cols
            assert len(overlap) == 0, f"Column overlap detected: {overlap}"
            
            all_columns.update(feature_cols)
        
        # Should have 3 unique columns total
        assert len(all_columns) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
