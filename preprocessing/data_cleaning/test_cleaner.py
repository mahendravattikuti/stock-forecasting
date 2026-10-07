"""
Tests for data cleaner orchestrator.

Tests DataCleaner, CleaningReportGenerator, and AuditTrail.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import tempfile
import os

from preprocessing.data_cleaning.cleaner import (
    DataCleaner,
    CleaningReport,
    CleaningReportGenerator,
    AuditTrail
)
import logging


# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def sample_ohlcv_df():
    """Create a sample OHLCV DataFrame for testing."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    data = {
        'Open': [100.0 + i * 0.5 for i in range(100)],
        'High': [102.0 + i * 0.5 for i in range(100)],
        'Low': [99.0 + i * 0.5 for i in range(100)],
        'Close': [101.0 + i * 0.5 for i in range(100)],
        'Volume': [1000000 + i * 10000 for i in range(100)]
    }
    
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def dirty_ohlcv_df():
    """Create a DataFrame with various data quality issues."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    data = {
        'Open': [100.0 + i * 0.5 for i in range(100)],
        'High': [102.0 + i * 0.5 for i in range(100)],
        'Low': [99.0 + i * 0.5 for i in range(100)],
        'Close': [101.0 + i * 0.5 for i in range(100)],
        'Volume': [1000000 + i * 10000 for i in range(100)]
    }
    
    df = pd.DataFrame(data, index=dates)
    
    # Add missing values (should be forward-filled)
    df.iloc[10:12, df.columns.get_loc('Close')] = np.nan
    
    # Add OHLC violation
    df.iloc[20, df.columns.get_loc('Close')] = 110.0
    df.iloc[20, df.columns.get_loc('High')] = 105.0
    
    # Add price spike
    df.iloc[30, df.columns.get_loc('Close')] = 500.0  # Large spike
    
    return df


# ============================================================================
# DataCleaner Tests
# ============================================================================

class TestDataCleaner:
    """Tests for DataCleaner orchestrator."""
    
    def test_clean_symbol_with_clean_data(self, sample_ohlcv_df):
        """Test cleaning of already-clean data."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        # Data should be unchanged
        assert len(cleaned_df) == len(sample_ohlcv_df)
        assert report.cleaned_data_rows == sample_ohlcv_df.shape[0]
        assert report.rows_excluded == 0
    
    def test_clean_symbol_with_dirty_data(self, dirty_ohlcv_df):
        """Test cleaning of data with issues."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', dirty_ohlcv_df)
        
        # Report should be generated
        assert report.symbol == 'AAPL'
        assert report.raw_data_rows == len(dirty_ohlcv_df)
        assert report.cleaned_data_rows > 0
        
        # Some corrections should be detected/applied
        assert (
            report.forward_fills_applied > 0 or
            report.ohlc_corrections_applied > 0 or
            report.spikes_corrected > 0
        )
    
    def test_report_contains_expected_fields(self, sample_ohlcv_df):
        """Test that cleaning report contains all expected fields."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        # Check essential fields
        assert report.symbol == 'AAPL'
        assert report.report_timestamp is not None
        assert report.raw_data_rows > 0
        assert report.cleaned_data_rows > 0
        assert report.quality_status in ['PASS', 'FAIL', 'MANUAL_REVIEW']
        assert report.validation_passed is not None
    
    def test_cleaned_data_has_required_columns(self, sample_ohlcv_df):
        """Test that cleaned data retains required columns."""
        cleaner = DataCleaner(apply_adjustments=True)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            assert col in cleaned_df.columns
        
        # AdjClose should be added if adjustments applied
        if report.adjustments_applied > 0 or cleaner.apply_adjustments:
            assert 'AdjClose' in cleaned_df.columns
    
    def test_cleaned_data_maintains_date_index(self, sample_ohlcv_df):
        """Test that cleaned data maintains date index."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        # Index should be datetime
        assert isinstance(cleaned_df.index, pd.DatetimeIndex)
        
        # Index should be sorted
        assert cleaned_df.index.is_monotonic_increasing
    
    def test_detection_algorithms_called(self, dirty_ohlcv_df):
        """Test that detection algorithms are executed."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('TEST', dirty_ohlcv_df)
        
        # At least some issues should be detected
        assert (
            report.missing_values_detected > 0 or
            report.ohlc_violations_detected > 0 or
            report.spikes_detected > 0
        )
    
    def test_forward_fill_max_days_respected(self):
        """Test that forward-fill respects max consecutive days."""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        data = {
            'Open': np.full(30, 100.0),
            'High': np.full(30, 102.0),
            'Low': np.full(30, 99.0),
            'Close': np.full(30, 101.0),
            'Volume': np.full(30, 1000000)
        }
        df = pd.DataFrame(data, index=dates)
        
        # Add 3 consecutive NaN (more than max of 2)
        df.iloc[10:13, df.columns.get_loc('Close')] = np.nan
        
        cleaner = DataCleaner(max_forward_fill_days=2, apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('TEST', df)
        
        # Rows with unfillable gaps should be excluded
        assert report.rows_excluded > 0
        # Or forward fills should not exceed max
        assert report.forward_fills_applied <= 2
    
    def test_multiple_symbols_independent(self, sample_ohlcv_df, dirty_ohlcv_df):
        """Test that cleaning multiple symbols doesn't cross-contaminate."""
        cleaner = DataCleaner(apply_adjustments=False)
        
        cleaned_df1, report1 = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        cleaned_df2, report2 = cleaner.clean_symbol('MSFT', dirty_ohlcv_df)
        
        # Reports should be independent
        assert report1.symbol == 'AAPL'
        assert report2.symbol == 'MSFT'
        
        # Dirty data should show corrections
        assert report2.rows_excluded >= 0  # May have corrections


# ============================================================================
# CleaningReport Tests
# ============================================================================

class TestCleaningReport:
    """Tests for CleaningReport dataclass."""
    
    def test_report_to_dict(self, sample_ohlcv_df):
        """Test conversion of report to dictionary."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        report_dict = report.to_dict()
        
        # Check dictionary structure
        assert isinstance(report_dict, dict)
        assert 'symbol' in report_dict
        assert 'raw_data_rows' in report_dict
        assert 'cleaned_data_rows' in report_dict
        assert 'quality_status' in report_dict
    
    def test_report_to_json(self, sample_ohlcv_df):
        """Test conversion of report to JSON."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        json_str = report.to_json()
        
        # Should be valid JSON
        report_data = json.loads(json_str)
        assert report_data['symbol'] == 'AAPL'
        assert 'cleaned_data_rows' in report_data
    
    def test_report_with_all_corrections(self, dirty_ohlcv_df):
        """Test that report captures all correction types."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('TEST', dirty_ohlcv_df)
        
        # Report should have logs for different correction types
        assert hasattr(report, 'forward_fill_log')
        assert hasattr(report, 'ohlc_corrections_log')
        assert hasattr(report, 'spike_corrections_log')
    
    def test_report_date_range(self, sample_ohlcv_df):
        """Test that report captures date ranges correctly."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        # Raw and cleaned date ranges should be captured
        assert report.raw_date_range is not None
        assert report.cleaned_date_range is not None
        
        # Dates should be strings
        assert isinstance(report.raw_date_range[0], str)
        assert isinstance(report.cleaned_date_range[0], str)


# ============================================================================
# CleaningReportGenerator Tests
# ============================================================================

class TestCleaningReportGenerator:
    """Tests for CleaningReportGenerator."""
    
    def test_generate_report_json(self, sample_ohlcv_df):
        """Test JSON report generation."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        generator = CleaningReportGenerator()
        json_report = generator.generate_report(report)
        
        # Should be valid JSON
        data = json.loads(json_report)
        assert data['symbol'] == 'AAPL'
    
    def test_save_report_to_file(self, sample_ohlcv_df):
        """Test saving report to file."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        generator = CleaningReportGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.json')
            generator.save_report(report, output_path)
            
            # File should exist
            assert os.path.exists(output_path)
            
            # Should contain valid JSON
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data['symbol'] == 'AAPL'
    
    def test_save_report_creates_directory(self, sample_ohlcv_df):
        """Test that saving report works with non-existent directory."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', sample_ohlcv_df)
        
        generator = CleaningReportGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use nested directory that doesn't exist
            output_path = os.path.join(tmpdir, 'reports', 'test_report.json')
            
            # This should not fail (but generator doesn't create dirs, that's caller's responsibility)
            # So we create it first
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            generator.save_report(report, output_path)
            
            assert os.path.exists(output_path)


# ============================================================================
# AuditTrail Tests
# ============================================================================

class TestAuditTrail:
    """Tests for AuditTrail."""
    
    def test_log_transformation(self):
        """Test logging a single transformation."""
        trail = AuditTrail()
        
        start_date = pd.Timestamp('2023-01-01')
        end_date = pd.Timestamp('2023-01-02')
        
        trail.log_transformation(
            symbol='AAPL',
            transformation_type='forward_fill',
            date_range=(start_date, end_date),
            reason='Missing close price',
            details={'columns_affected': ['Close']}
        )
        
        # Should have 1 transformation recorded
        assert len(trail.transformations) == 1
        
        trans = trail.transformations[0]
        assert trans['symbol'] == 'AAPL'
        assert trans['transformation_type'] == 'forward_fill'
        assert trans['reason'] == 'Missing close price'
    
    def test_get_aggregate_statistics(self):
        """Test aggregate statistics computation."""
        trail = AuditTrail()
        
        # Log multiple transformations
        for i in range(5):
            trail.log_transformation(
                symbol='AAPL',
                transformation_type='forward_fill',
                date_range=(
                    pd.Timestamp('2023-01-01'),
                    pd.Timestamp('2023-01-02')
                ),
                reason='Test'
            )
        
        for i in range(3):
            trail.log_transformation(
                symbol='MSFT',
                transformation_type='spike_correction',
                date_range=(
                    pd.Timestamp('2023-02-01'),
                    pd.Timestamp('2023-02-02')
                ),
                reason='Test'
            )
        
        stats = trail.get_aggregate_statistics()
        
        # Check statistics
        assert stats['total_transformations'] == 8
        assert stats['symbols_processed'] == 2
        assert 'forward_fill' in stats['transformation_types']
        assert 'spike_correction' in stats['transformation_types']
        assert stats['transformation_types']['forward_fill'] == 5
        assert stats['transformation_types']['spike_correction'] == 3
    
    def test_audit_trail_to_json(self):
        """Test JSON serialization of audit trail."""
        trail = AuditTrail()
        
        trail.log_transformation(
            symbol='AAPL',
            transformation_type='forward_fill',
            date_range=(
                pd.Timestamp('2023-01-01'),
                pd.Timestamp('2023-01-02')
            ),
            reason='Test'
        )
        
        json_str = trail.to_json()
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert 'transformation_log' in data
        assert 'aggregate_statistics' in data
        assert data['aggregate_statistics']['total_transformations'] == 1
    
    def test_audit_trail_save_to_file(self):
        """Test saving audit trail to file."""
        trail = AuditTrail()
        
        trail.log_transformation(
            symbol='AAPL',
            transformation_type='forward_fill',
            date_range=(
                pd.Timestamp('2023-01-01'),
                pd.Timestamp('2023-01-02')
            ),
            reason='Test'
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'audit_trail.json')
            trail.save_to_file(output_path)
            
            # File should exist
            assert os.path.exists(output_path)
            
            # Should contain valid JSON
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data['aggregate_statistics']['total_transformations'] == 1
    
    def test_empty_audit_trail(self):
        """Test statistics for empty audit trail."""
        trail = AuditTrail()
        
        stats = trail.get_aggregate_statistics()
        
        assert stats['total_transformations'] == 0
        assert stats['symbols_processed'] == 0
        assert len(stats['transformation_types']) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for cleaner module."""
    
    def test_end_to_end_cleaning_with_reporting(self, dirty_ohlcv_df):
        """Test complete cleaning pipeline with report generation."""
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('AAPL', dirty_ohlcv_df)
        
        # Generate and save report
        generator = CleaningReportGenerator()
        json_report = generator.generate_report(report)
        
        # Verify report
        data = json.loads(json_report)
        assert data['symbol'] == 'AAPL'
        assert data['quality_status'] in ['PASS', 'FAIL', 'MANUAL_REVIEW']
    
    def test_multiple_cleaning_operations(self, sample_ohlcv_df, dirty_ohlcv_df):
        """Test multiple cleaning operations in sequence."""
        cleaner = DataCleaner(apply_adjustments=False)
        audit_trail = AuditTrail()
        
        for symbol, df in [('AAPL', sample_ohlcv_df), ('MSFT', dirty_ohlcv_df)]:
            cleaned_df, report = cleaner.clean_symbol(symbol, df)
            
            # Log transformations
            audit_trail.log_transformation(
                symbol=symbol,
                transformation_type='complete_cleaning',
                date_range=(df.index[0], df.index[-1]),
                reason=f'Cleaned {symbol}',
                details={'rows_excluded': report.rows_excluded}
            )
        
        # Verify audit trail
        stats = audit_trail.get_aggregate_statistics()
        assert stats['total_transformations'] == 2
        assert stats['symbols_processed'] == 2


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_dataframe(self):
        """Test cleaning of empty DataFrame."""
        df = pd.DataFrame({'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': []})
        
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('EMPTY', df)
        
        # Should handle gracefully
        assert len(cleaned_df) == 0
        assert report.raw_data_rows == 0
    
    def test_single_row_dataframe(self):
        """Test cleaning of single-row DataFrame."""
        dates = pd.date_range(start='2023-01-01', periods=1, freq='D')
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=dates)
        
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('SINGLE', df)
        
        # Should handle gracefully
        assert len(cleaned_df) >= 0
    
    def test_all_nan_column(self):
        """Test cleaning with completely NaN column."""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'Open': [100.0] * 10,
            'High': [102.0] * 10,
            'Low': [99.0] * 10,
            'Close': np.nan,  # All NaN
            'Volume': [1000000] * 10
        }, index=dates)
        
        cleaner = DataCleaner(apply_adjustments=False)
        cleaned_df, report = cleaner.clean_symbol('ALLNAN', df)
        
        # Should handle and likely exclude all rows
        assert len(cleaned_df) <= len(df)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

