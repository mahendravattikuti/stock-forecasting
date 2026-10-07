"""
Quality assurance test suite for data quality validation.

Tests DataQualityValidator, ValidationReportGenerator, and SymbolExclusionManager.
Validates edge cases, pass/fail criteria, and report generation.
"""

import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from datetime import datetime, timedelta
import logging

from validators import (
    DataQualityValidator,
    ValidationReportGenerator,
    SymbolExclusionManager,
    OHLCValidator
)


# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestDataQualityValidator:
    """Test suite for DataQualityValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance with test parameters."""
        return DataQualityValidator(
            min_trading_days=2500,
            min_completeness=0.99,
            logger=logger
        )
    
    @pytest.fixture
    def valid_dataframe(self):
        """Create a valid OHLCV DataFrame with 2,500+ trading days."""
        dates = pd.date_range('2010-01-01', periods=2500, freq='D')
        
        # Create valid OHLCV data: Open < Close, Low < High
        data = {
            'Open': np.random.uniform(100, 105, 2500),
            'High': np.random.uniform(105, 110, 2500),
            'Low': np.random.uniform(95, 100, 2500),
            'Close': np.random.uniform(100, 105, 2500),
            'Volume': np.random.uniform(1000000, 5000000, 2500)
        }
        
        df = pd.DataFrame(data, index=dates)
        
        # Enforce OHLC ordering: Low <= Open <= Close <= High
        df['Low'] = df[['Open', 'High', 'Low', 'Close']].min(axis=1)
        df['High'] = df[['Open', 'High', 'Low', 'Close']].max(axis=1)
        
        return df
    
    @pytest.fixture
    def insufficient_data_dataframe(self):
        """Create DataFrame with insufficient trading days (< 2500)."""
        dates = pd.date_range('2010-01-01', periods=2499, freq='D')
        
        data = {
            'Open': np.random.uniform(100, 105, 2499),
            'High': np.random.uniform(105, 110, 2499),
            'Low': np.random.uniform(95, 100, 2499),
            'Close': np.random.uniform(100, 105, 2499),
            'Volume': np.random.uniform(1000000, 5000000, 2499)
        }
        
        df = pd.DataFrame(data, index=dates)
        df['Low'] = df[['Open', 'High', 'Low', 'Close']].min(axis=1)
        df['High'] = df[['Open', 'High', 'Low', 'Close']].max(axis=1)
        
        return df
    
    @pytest.fixture
    def stasis_dataframe(self):
        """Create DataFrame with multi-day price stasis (5+ unchanged closes)."""
        dates = pd.date_range('2010-01-01', periods=2500, freq='D')
        
        data = {
            'Open': np.full(2500, 100.0),
            'High': np.full(2500, 105.0),
            'Low': np.full(2500, 95.0),
            'Close': np.full(2500, 100.0),  # All same close
            'Volume': np.full(2500, 1000000.0)
        }
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def test_valid_data_passes(self, validator, valid_dataframe):
        """Test that valid data passes all quality checks."""
        result = validator.validate_quality(valid_dataframe)
        
        assert result['overall_pass'] is True, "Valid data should pass"
        assert result['checks']['min_trading_days']['pass'] is True
        assert result['checks']['ohlc_relationships']['pass'] is True
        assert result['checks']['statistics']['pass'] is True
    
    def test_insufficient_data_fails(self, validator, insufficient_data_dataframe):
        """Test that data with insufficient trading days fails validation."""
        result = validator.validate_quality(insufficient_data_dataframe)
        
        assert result['overall_pass'] is False, "Insufficient data should fail"
        assert result['checks']['min_trading_days']['pass'] is False
        assert result['checks']['min_trading_days']['actual'] == 2499
    
    def test_exactly_min_threshold_passes(self, validator):
        """Test edge case: exactly 2,500 trading days should pass."""
        dates = pd.date_range('2010-01-01', periods=2500, freq='D')
        
        data = {
            'Open': np.random.uniform(100, 105, 2500),
            'High': np.random.uniform(105, 110, 2500),
            'Low': np.random.uniform(95, 100, 2500),
            'Close': np.random.uniform(100, 105, 2500),
            'Volume': np.random.uniform(1000000, 5000000, 2500)
        }
        
        df = pd.DataFrame(data, index=dates)
        df['Low'] = df[['Open', 'High', 'Low', 'Close']].min(axis=1)
        df['High'] = df[['Open', 'High', 'Low', 'Close']].max(axis=1)
        
        result = validator.validate_quality(df)
        
        assert result['checks']['min_trading_days']['pass'] is True
        assert result['checks']['min_trading_days']['actual'] == 2500
    
    def test_stasis_detection(self, validator, stasis_dataframe):
        """Test that multi-day price stasis is properly detected."""
        result = validator.validate_quality(stasis_dataframe)
        
        stasis_check = result['checks']['price_stasis']
        assert stasis_check['detected'] is True, "Stasis should be detected"
        assert len(stasis_check['ranges']) > 0, "Should have at least one stasis range"
        
        # With all closes identical, entire series is stasis
        start, end, num_days = stasis_check['ranges'][0]
        assert num_days >= 5, "Stasis range should be >= 5 days"
    
    def test_invalid_ohlc_relationships(self, validator):
        """Test detection of invalid OHLC relationships."""
        dates = pd.date_range('2010-01-01', periods=100, freq='D')
        
        data = {
            'Open': np.full(100, 100.0),
            'High': np.full(100, 95.0),  # Invalid: High < Open
            'Low': np.full(100, 90.0),
            'Close': np.full(100, 98.0),
            'Volume': np.full(100, 1000000.0)
        }
        
        df = pd.DataFrame(data, index=dates)
        
        # Only checking OHLC relationships (not row count)
        valid_bars, total_bars = validator.ohlc_validator.check_price_ordering(df)
        ohlc_pct = valid_bars / total_bars if total_bars > 0 else 0
        
        assert ohlc_pct < 0.99, "Invalid OHLC should result in low completeness"
    
    def test_statistics_validity_check(self, validator, valid_dataframe):
        """Test that summary statistics are validated."""
        result = validator.validate_quality(valid_dataframe)
        
        stats_check = result['checks']['statistics']
        assert stats_check['pass'] is True, "Valid statistics should pass"
        assert len(stats_check['errors']) == 0, "Should have no error messages"
    
    def test_nan_values_in_dataframe(self, validator):
        """Test handling of NaN values."""
        dates = pd.date_range('2010-01-01', periods=2500, freq='D')
        
        data = {
            'Open': np.random.uniform(100, 105, 2500),
            'High': np.random.uniform(105, 110, 2500),
            'Low': np.random.uniform(95, 100, 2500),
            'Close': np.random.uniform(100, 105, 2500),
            'Volume': np.random.uniform(1000000, 5000000, 2500)
        }
        
        df = pd.DataFrame(data, index=dates)
        df.loc[df.index[:10], 'Close'] = np.nan  # Add NaN values
        
        result = validator.validate_quality(df)
        
        # Should still pass min_trading_days since len(df) = 2500
        assert result['checks']['min_trading_days']['pass'] is True
    
    def test_completeness_percentage_calculation(self, validator):
        """Test that completeness percentage is correctly calculated."""
        dates = pd.date_range('2010-01-01', periods=2500, freq='D')
        
        # Create data with mostly valid OHLC
        data = {
            'Open': np.full(2500, 100.0),
            'High': np.full(2500, 105.0),
            'Low': np.full(2500, 95.0),
            'Close': np.full(2500, 100.0),
            'Volume': np.full(2500, 1000000.0)
        }
        
        df = pd.DataFrame(data, index=dates)
        
        result = validator.validate_quality(df)
        ohlc_check = result['checks']['ohlc_relationships']
        
        assert 'actual' in ohlc_check
        assert '%' in ohlc_check['actual'], "Completeness should be percentage string"


class TestValidationReportGenerator:
    """Test suite for ValidationReportGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a report generator instance."""
        return ValidationReportGenerator(logger=logger)
    
    @pytest.fixture
    def sample_validation_results(self):
        """Create sample validation results for multiple symbols."""
        return {
            'AAPL': {
                'overall_pass': True,
                'total_rows': 2500,
                'checks': {
                    'min_trading_days': {'pass': True, 'actual': 2500},
                    'ohlc_relationships': {
                        'pass': True,
                        'actual': '99.50%',
                        'valid': 2488,
                        'total': 2500
                    },
                    'statistics': {'pass': True, 'errors': []},
                    'price_stasis': {'detected': False, 'ranges': []}
                }
            },
            'MSFT': {
                'overall_pass': False,
                'total_rows': 2400,
                'checks': {
                    'min_trading_days': {'pass': False, 'actual': 2400},
                    'ohlc_relationships': {'pass': True, 'actual': '98.50%'},
                    'statistics': {'pass': True, 'errors': []},
                    'price_stasis': {'detected': False, 'ranges': []}
                }
            }
        }
    
    @pytest.fixture
    def excluded_symbols(self):
        """Create sample excluded symbols."""
        return {
            'DELISTED': 'symbol_delisted',
            'BADDATA': 'insufficient_data'
        }
    
    def test_report_generation(self, generator, sample_validation_results, excluded_symbols):
        """Test that validation report is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'validation_report.json')
            
            report = generator.generate_validation_report(
                sample_validation_results,
                excluded_symbols,
                output_path
            )
            
            assert report['summary']['total_symbols'] == 4  # 2 results + 2 excluded
            assert report['summary']['symbols_passed'] == 1
            assert report['summary']['symbols_excluded'] == 2
            assert 'AAPL' in report['symbols']
            assert 'MSFT' in report['symbols']
            assert 'DELISTED' in report['excluded_symbols']
    
    def test_report_file_creation(self, generator, sample_validation_results, excluded_symbols):
        """Test that report JSON file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'validation_report.json')
            
            generator.generate_validation_report(
                sample_validation_results,
                excluded_symbols,
                output_path
            )
            
            assert os.path.exists(output_path), "Report file should be created"
            
            # Verify file is valid JSON
            with open(output_path, 'r') as f:
                loaded_report = json.load(f)
            
            assert loaded_report['summary']['symbols_passed'] == 1
    
    def test_completeness_percentage_extraction(self, generator):
        """Test extraction of completeness percentage from OHLC check."""
        validation_results = {
            'TEST': {
                'overall_pass': True,
                'checks': {
                    'min_trading_days': {'pass': True},
                    'ohlc_relationships': {
                        'pass': True,
                        'actual': '99.75%'
                    },
                    'statistics': {'pass': True, 'errors': []},
                    'price_stasis': {'detected': False, 'ranges': []}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'validation_report.json')
            
            report = generator.generate_validation_report(validation_results, {}, output_path)
            
            completeness = report['symbols']['TEST']['completeness_percent']
            assert completeness == 99.75
    
    def test_manual_review_flags(self, generator, sample_validation_results, excluded_symbols):
        """Test that failed symbols are flagged for manual review."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'validation_report.json')
            
            report = generator.generate_validation_report(
                sample_validation_results,
                excluded_symbols,
                output_path
            )
            
            # MSFT failed validation
            manual_review_symbols = [
                flag['symbol'] for flag in report['manual_review_flags']
            ]
            assert 'MSFT' in manual_review_symbols


class TestSymbolExclusionManager:
    """Test suite for SymbolExclusionManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create an exclusion manager instance."""
        return SymbolExclusionManager(logger=logger)
    
    def test_exclude_symbol(self, manager):
        """Test excluding a symbol."""
        manager.exclude_symbol('AAPL', 'insufficient_data')
        
        excluded = manager.get_excluded_symbols()
        assert 'AAPL' in excluded
        assert excluded['AAPL'] == 'insufficient_data'
    
    def test_exclude_multiple_symbols(self, manager):
        """Test excluding multiple symbols."""
        manager.exclude_symbol('AAPL', 'insufficient_data')
        manager.exclude_symbol('MSFT', 'invalid_ohlc')
        manager.exclude_symbol('GOOGL', 'price_stasis')
        
        excluded = manager.get_excluded_symbols()
        assert len(excluded) == 3
        assert excluded['AAPL'] == 'insufficient_data'
        assert excluded['MSFT'] == 'invalid_ohlc'
        assert excluded['GOOGL'] == 'price_stasis'
    
    def test_is_excluded(self, manager):
        """Test checking if symbol is excluded."""
        manager.exclude_symbol('AAPL', 'insufficient_data')
        
        assert manager.is_excluded('AAPL') is True
        assert manager.is_excluded('MSFT') is False
    
    def test_exclusion_summary_generation(self, manager):
        """Test generating exclusion summary."""
        manager.exclude_symbol('AAPL', 'insufficient_data')
        manager.exclude_symbol('MSFT', 'insufficient_data')
        manager.exclude_symbol('GOOGL', 'invalid_ohlc')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'exclusion_summary.json')
            
            summary = manager.generate_exclusion_summary(output_path)
            
            assert summary['total_excluded'] == 3
            assert 'insufficient_data' in summary['excluded_by_reason']
            assert 'invalid_ohlc' in summary['excluded_by_reason']
            assert len(summary['excluded_by_reason']['insufficient_data']) == 2
    
    def test_exclusion_summary_file_creation(self, manager):
        """Test that exclusion summary JSON file is created."""
        manager.exclude_symbol('AAPL', 'insufficient_data')
        manager.exclude_symbol('MSFT', 'invalid_ohlc')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'exclusion_summary.json')
            
            manager.generate_exclusion_summary(output_path)
            
            assert os.path.exists(output_path), "Summary file should be created"
            
            # Verify file is valid JSON
            with open(output_path, 'r') as f:
                loaded_summary = json.load(f)
            
            assert loaded_summary['total_excluded'] == 2
    
    def test_exclusion_with_details(self, manager):
        """Test excluding symbol with additional details."""
        details = {
            'actual_days': 2400,
            'required_days': 2500,
            'shortfall': 100
        }
        
        manager.exclude_symbol(
            'AAPL',
            'insufficient_data',
            details=details
        )
        
        excluded_data = manager.excluded_symbols['AAPL']
        assert excluded_data['details'] == details
    
    def test_exclusion_date_tracking(self, manager):
        """Test that exclusion dates are tracked."""
        manager.exclude_symbol('AAPL', 'insufficient_data')
        
        excluded_data = manager.excluded_symbols['AAPL']
        assert 'exclusion_date' in excluded_data
        
        # Date should be recent (within last minute)
        exclusion_date = datetime.strptime(
            excluded_data['exclusion_date'],
            '%Y-%m-%d'
        )
        now = datetime.utcnow()
        delta = (now - exclusion_date).days
        assert delta <= 1, "Exclusion date should be recent"


class TestIntegrationDataQualityWorkflow:
    """Integration tests for complete data quality validation workflow."""
    
    def test_end_to_end_validation_workflow(self):
        """Test complete workflow: validate, generate report, exclude."""
        # Create sample data
        validator = DataQualityValidator(min_trading_days=2500, logger=logger)
        generator = ValidationReportGenerator(logger=logger)
        manager = SymbolExclusionManager(logger=logger)
        
        # Validate symbols
        dates = pd.date_range('2010-01-01', periods=2500, freq='D')
        
        valid_data = {
            'Open': np.random.uniform(100, 105, 2500),
            'High': np.random.uniform(105, 110, 2500),
            'Low': np.random.uniform(95, 100, 2500),
            'Close': np.random.uniform(100, 105, 2500),
            'Volume': np.random.uniform(1000000, 5000000, 2500)
        }
        
        df = pd.DataFrame(valid_data, index=dates)
        df['Low'] = df[['Open', 'High', 'Low', 'Close']].min(axis=1)
        df['High'] = df[['Open', 'High', 'Low', 'Close']].max(axis=1)
        
        # Run validation
        validation_results = {'AAPL': validator.validate_quality(df)}
        
        # Exclude bad symbols
        manager.exclude_symbol('BADCO', 'insufficient_data')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate reports
            report_path = os.path.join(tmpdir, 'validation_report.json')
            summary_path = os.path.join(tmpdir, 'exclusion_summary.json')
            
            report = generator.generate_validation_report(
                validation_results,
                manager.get_excluded_symbols(),
                report_path
            )
            
            summary = manager.generate_exclusion_summary(summary_path)
            
            # Verify workflow results
            assert report['summary']['symbols_passed'] == 1
            assert report['summary']['symbols_excluded'] == 1
            assert summary['total_excluded'] == 1
            assert os.path.exists(report_path)
            assert os.path.exists(summary_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
