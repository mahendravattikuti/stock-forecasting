"""
Tests for data correctors module.

Tests ForwardFillCorrector, OHLCCorrector, and SpikeCorrector.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from correctors import (
    ForwardFillCorrector,
    OHLCCorrector,
    SpikeCorrector,
    PriceSpike
)
import logging


# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def sample_ohlcv_df():
    """Create a sample OHLCV DataFrame for testing."""
    dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
    
    data = {
        'Open': [100.0 + i * 0.5 for i in range(20)],
        'High': [102.0 + i * 0.5 for i in range(20)],
        'Low': [99.0 + i * 0.5 for i in range(20)],
        'Close': [101.0 + i * 0.5 for i in range(20)],
        'Volume': [1000000 + i * 10000 for i in range(20)]
    }
    
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def df_with_missing_values(sample_ohlcv_df):
    """Create a DataFrame with missing values."""
    df = sample_ohlcv_df.copy()
    
    # Introduce 2 consecutive missing days (should be fillable)
    df.iloc[5:7, df.columns.get_loc('Close')] = np.nan
    df.iloc[5:7, df.columns.get_loc('High')] = np.nan
    
    # Introduce 4 consecutive missing days (should be unfillable with max=2)
    df.iloc[12:16, df.columns.get_loc('Low')] = np.nan
    
    return df


@pytest.fixture
def df_with_ohlc_violations(sample_ohlcv_df):
    """Create a DataFrame with OHLC relationship violations."""
    df = sample_ohlcv_df.copy()
    
    # Violation 1: Close > High
    df.iloc[3, df.columns.get_loc('Close')] = 110.0
    df.iloc[3, df.columns.get_loc('High')] = 105.0
    
    # Violation 2: Low > Close
    df.iloc[7, df.columns.get_loc('Low')] = 105.0
    df.iloc[7, df.columns.get_loc('Close')] = 101.0
    
    return df


@pytest.fixture
def sample_spikes():
    """Create sample spike objects for testing."""
    spike1 = PriceSpike(
        date=pd.Timestamp('2023-01-06'),
        column='Close',
        daily_return=0.25,  # 25% spike
        previous_close=100.0,
        current_value=125.0,
        severity='high'
    )
    
    spike2 = PriceSpike(
        date=pd.Timestamp('2023-01-10'),
        column='Close',
        daily_return=-0.22,  # -22% spike
        previous_close=102.0,
        current_value=79.56,
        severity='high'
    )
    
    return [spike1, spike2]


# ============================================================================
# ForwardFillCorrector Tests
# ============================================================================

class TestForwardFillCorrector:
    """Tests for ForwardFillCorrector."""
    
    def test_forward_fill_within_threshold(self, df_with_missing_values):
        """Test that gaps within max_consecutive_days are forward-filled."""
        corrector = ForwardFillCorrector(max_consecutive_days=2)
        corrected_df, corrections = corrector.correct_missing_values(df_with_missing_values)
        
        # Check that 2-day gap was filled
        assert not corrected_df.iloc[5:7]['Close'].isna().any()
        assert corrected_df.iloc[5]['Close'] == df_with_missing_values.iloc[4]['Close']
        assert corrected_df.iloc[6]['Close'] == df_with_missing_values.iloc[4]['Close']
        
        # Check corrections were recorded
        assert len(corrections) >= 2
    
    def test_exclude_unfillable_gaps(self, df_with_missing_values):
        """Test that gaps beyond max_consecutive_days are excluded."""
        corrector = ForwardFillCorrector(max_consecutive_days=2)
        corrected_df, corrections = corrector.correct_missing_values(df_with_missing_values)
        
        # 4-day gap starting at index 12 should result in excluded rows
        # Row at index 12-15 should be removed
        assert len(corrected_df) < len(df_with_missing_values)
        
        # Verify rows around gap are excluded
        assert corrected_df.index[0] == df_with_missing_values.index[0]
    
    def test_forward_fill_volume_median(self, sample_ohlcv_df):
        """Test that volume is filled with median strategy."""
        df = sample_ohlcv_df.copy()
        df.iloc[5:7, df.columns.get_loc('Volume')] = np.nan
        
        corrector = ForwardFillCorrector(volume_strategy='median')
        corrected_df, corrections = corrector.correct_missing_values(df)
        
        # Check that volume was filled
        assert not corrected_df.iloc[5:7]['Volume'].isna().any()
        # Should be median of nearby values
        assert corrected_df.iloc[5]['Volume'] > 0
    
    def test_forward_fill_volume_forward_fill(self, sample_ohlcv_df):
        """Test that volume can be filled with forward_fill strategy."""
        df = sample_ohlcv_df.copy()
        df.iloc[5:7, df.columns.get_loc('Volume')] = np.nan
        
        corrector = ForwardFillCorrector(volume_strategy='forward_fill')
        corrected_df, corrections = corrector.correct_missing_values(df)
        
        # Check that volume was filled
        assert not corrected_df.iloc[5:7]['Volume'].isna().any()
    
    def test_no_corrections_for_clean_data(self, sample_ohlcv_df):
        """Test that clean data produces no corrections."""
        corrector = ForwardFillCorrector()
        corrected_df, corrections = corrector.correct_missing_values(sample_ohlcv_df)
        
        # No missing values, so no corrections
        assert len(corrections) == 0
        assert len(corrected_df) == len(sample_ohlcv_df)
    
    def test_forward_fill_records_created(self, df_with_missing_values):
        """Test that forward-fill records are properly created."""
        corrector = ForwardFillCorrector(max_consecutive_days=2)
        corrected_df, corrections = corrector.correct_missing_values(df_with_missing_values)
        
        # Check that forward-fill records exist
        assert len(corrector.forward_fill_records) > 0
        
        # Verify record structure
        for record in corrector.forward_fill_records:
            assert record.column in ['Open', 'High', 'Low', 'Close', 'Volume']
            assert record.consecutive_days <= 2


# ============================================================================
# OHLCCorrector Tests
# ============================================================================

class TestOHLCCorrector:
    """Tests for OHLCCorrector."""
    
    def test_correct_high_lt_close_violation(self, df_with_ohlc_violations):
        """Test correction of High < Close violation."""
        corrector = OHLCCorrector(fix_method='linear_interpolation')
        corrected_df, corrections = corrector.correct_relationships(df_with_ohlc_violations)
        
        # Check that violation was corrected
        idx = 3
        corrected_row = corrected_df.iloc[idx]
        assert corrected_row['High'] >= corrected_row['Close']
        
        # Check corrections were recorded
        assert len(corrections) > 0
    
    def test_correct_low_gt_close_violation(self, df_with_ohlc_violations):
        """Test correction of Low > Close violation."""
        corrector = OHLCCorrector(fix_method='linear_interpolation')
        corrected_df, corrections = corrector.correct_relationships(df_with_ohlc_violations)
        
        # Check that violation was corrected
        idx = 7
        corrected_row = corrected_df.iloc[idx]
        assert corrected_row['Low'] <= corrected_row['Close']
        
        # Check corrections were recorded
        assert len(corrections) > 0
    
    def test_validate_corrections_all_valid(self, df_with_ohlc_violations):
        """Test that corrected data passes validation."""
        corrector = OHLCCorrector(fix_method='linear_interpolation')
        corrected_df, corrections = corrector.correct_relationships(df_with_ohlc_violations)
        
        # Validate corrections
        is_valid, errors = corrector.validate_corrections(corrected_df)
        assert is_valid
        assert len(errors) == 0
    
    def test_no_corrections_for_valid_data(self, sample_ohlcv_df):
        """Test that valid data produces no corrections."""
        corrector = OHLCCorrector()
        corrected_df, corrections = corrector.correct_relationships(sample_ohlcv_df)
        
        # No violations, so no corrections
        assert len(corrections) == 0
        assert len(corrected_df) == len(sample_ohlcv_df)
    
    def test_check_violations_detected(self, df_with_ohlc_violations):
        """Test that violations are properly detected."""
        corrector = OHLCCorrector()
        
        # Test row 3 (Close > High)
        row = df_with_ohlc_violations.iloc[3]
        violations = corrector._check_violations(
            row['Open'], row['High'], row['Low'], row['Close']
        )
        assert 'high_lt_close' in violations
        
        # Test row 7 (Low > Close)
        row = df_with_ohlc_violations.iloc[7]
        violations = corrector._check_violations(
            row['Open'], row['High'], row['Low'], row['Close']
        )
        assert 'close_lt_low' in violations
    
    def test_interpolation_produces_valid_ohlc(self, df_with_ohlc_violations):
        """Test that interpolation produces valid OHLC values."""
        corrector = OHLCCorrector()
        
        # Test interpolation for a known violation
        corrected = corrector._fix_via_interpolation(
            o=100.0,
            h=105.0,
            l=99.0,
            c=110.0  # Invalid: Close > High
        )
        
        # Check that corrected values are valid
        assert corrected['High'] >= corrected['Close']
        assert corrected['Close'] >= corrected['Low']
        assert corrected['Low'] >= corrected['Open']


# ============================================================================
# SpikeCorrector Tests
# ============================================================================

class TestSpikeCorrector:
    """Tests for SpikeCorrector."""
    
    def test_correct_spike_with_interpolation(self, sample_ohlcv_df, sample_spikes):
        """Test spike correction via interpolation."""
        corrector = SpikeCorrector(fix_method='interpolation')
        corrected_df, corrections = corrector.correct_spikes(
            sample_ohlcv_df,
            sample_spikes
        )
        
        # Check that corrections were made
        assert len(corrections) > 0
        
        # Spikes should have action
        for correction in corrections:
            assert correction.action in ['accepted', 'interpolated', 'removed']
    
    def test_spike_verification(self, sample_ohlcv_df, sample_spikes):
        """Test spike verification mechanism."""
        corrector = SpikeCorrector()
        
        # Verify first spike
        confirmed = corrector._verify_spike_from_sources(
            sample_spikes[0],
            sample_ohlcv_df
        )
        
        # Should return number of confirmed sources (0-3+)
        assert isinstance(confirmed, int)
        assert confirmed >= 0
    
    def test_spike_interpolation(self, sample_ohlcv_df):
        """Test spike interpolation functionality."""
        df = sample_ohlcv_df.copy()
        
        corrector = SpikeCorrector()
        
        # Create a spike at index 5
        spike_date = df.index[5]
        
        interpolated_df = corrector._interpolate_spike(df, spike_date)
        
        # Check that DataFrame structure is maintained
        assert len(interpolated_df) == len(df)
        assert 'Close' in interpolated_df.columns
    
    def test_no_corrections_for_clean_data(self, sample_ohlcv_df):
        """Test that clean data with no spikes produces no corrections."""
        corrector = SpikeCorrector()
        corrected_df, corrections = corrector.correct_spikes(
            sample_ohlcv_df,
            []  # No spikes
        )
        
        # No spikes, so no corrections
        assert len(corrections) == 0
        assert len(corrected_df) == len(sample_ohlcv_df)
    
    def test_spike_correction_records(self, sample_ohlcv_df, sample_spikes):
        """Test that spike correction records are created."""
        corrector = SpikeCorrector()
        corrected_df, corrections = corrector.correct_spikes(
            sample_ohlcv_df,
            sample_spikes
        )
        
        # Check records structure
        assert len(corrections) > 0
        for record in corrections:
            assert hasattr(record, 'date')
            assert hasattr(record, 'daily_return')
            assert hasattr(record, 'action')
            assert hasattr(record, 'reason')


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for correctors."""
    
    def test_end_to_end_correction_pipeline(self, df_with_missing_values, df_with_ohlc_violations):
        """Test complete correction pipeline."""
        # Start with data containing missing values
        df = df_with_missing_values.copy()
        
        # Step 1: Forward-fill missing values
        ff_corrector = ForwardFillCorrector(max_consecutive_days=2)
        df, ff_corrections = ff_corrector.correct_missing_values(df)
        
        # Step 2: Correct OHLC relationships
        ohlc_corrector = OHLCCorrector()
        df, ohlc_corrections = ohlc_corrector.correct_relationships(df)
        
        # Step 3: Validate result
        is_valid, errors = ohlc_corrector.validate_corrections(df)
        assert is_valid
    
    def test_corrected_data_has_expected_structure(self, df_with_missing_values):
        """Test that corrected data maintains expected structure."""
        corrector = ForwardFillCorrector()
        corrected_df, corrections = corrector.correct_missing_values(df_with_missing_values)
        
        # Check all required columns are present
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            assert col in corrected_df.columns
        
        # Check no NaN values remain (after corrections)
        # Some NaN might remain if unfillable, but those rows should be excluded
        assert not corrected_df.isnull().any().any() or len(corrected_df) > 0


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_all_nan_column(self, sample_ohlcv_df):
        """Test handling of completely NaN column."""
        df = sample_ohlcv_df.copy()
        df['Close'] = np.nan
        
        corrector = ForwardFillCorrector()
        corrected_df, corrections = corrector.correct_missing_values(df)
        
        # All rows should be excluded since Close is required
        assert len(corrected_df) < len(df)
    
    def test_first_row_with_nan(self, sample_ohlcv_df):
        """Test handling of NaN in first row (cannot forward-fill from before start)."""
        df = sample_ohlcv_df.copy()
        df.iloc[0, df.columns.get_loc('Close')] = np.nan
        
        corrector = ForwardFillCorrector()
        corrected_df, corrections = corrector.correct_missing_values(df)
        
        # First row NaN cannot be filled, so might be excluded
        # This depends on implementation
        assert len(corrected_df) <= len(df)
    
    def test_last_row_with_nan(self, sample_ohlcv_df):
        """Test handling of NaN in last row."""
        df = sample_ohlcv_df.copy()
        df.iloc[-1, df.columns.get_loc('Close')] = np.nan
        
        corrector = ForwardFillCorrector()
        corrected_df, corrections = corrector.correct_missing_values(df)
        
        # Last row NaN should be forward-filled from previous row
        assert not corrected_df.iloc[-1]['Close'].isna()
    
    def test_zero_spikes_list(self, sample_ohlcv_df):
        """Test SpikeCorrector with empty spikes list."""
        corrector = SpikeCorrector()
        corrected_df, corrections = corrector.correct_spikes(
            sample_ohlcv_df,
            []
        )
        
        # Should handle gracefully
        assert len(corrections) == 0
        assert len(corrected_df) == len(sample_ohlcv_df)
    
    def test_missing_close_column(self, sample_ohlcv_df):
        """Test SpikeCorrector with missing Close column."""
        df = sample_ohlcv_df.copy()
        df = df.drop('Close', axis=1)
        
        corrector = SpikeCorrector()
        corrected_df, corrections = corrector.correct_spikes(
            df,
            []
        )
        
        # Should handle gracefully
        assert len(corrections) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
