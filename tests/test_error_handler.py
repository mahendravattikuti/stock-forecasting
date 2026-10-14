"""
Unit tests for error handling infrastructure.

Tests custom exception classes, error handler, and warnings manager.
"""

import pytest
import json
import logging
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.error_handler import (
    StockForecastingError,
    DataAcquisitionError,
    DataValidationError,
    DataLeakageError,
    FeatureComputationError,
    ConfigurationError,
    ReproducibilityError,
    ErrorHandler,
    WarningsManager,
    RecoveryAction,
    ErrorRecord
)


class TestExceptionHierarchy:
    """Test suite for custom exception classes."""
    
    def test_base_exception(self):
        """Test: Base StockForecastingError."""
        error = StockForecastingError(
            "Test error",
            error_code="TEST_ERROR",
            context={'symbol': 'AAPL'}
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.context == {'symbol': 'AAPL'}
        assert error.timestamp is not None
    
    def test_data_acquisition_error(self):
        """Test: DataAcquisitionError with source and symbol."""
        error = DataAcquisitionError(
            "Failed to fetch data",
            source='iex_cloud',
            symbol='AAPL',
            context={'status_code': 429}
        )
        
        assert error.error_code == 'DATA_ACQUISITION_ERROR'
        assert error.source == 'iex_cloud'
        assert error.symbol == 'AAPL'
        assert error.context['status_code'] == 429
    
    def test_data_validation_error(self):
        """Test: DataValidationError."""
        error = DataValidationError(
            "Missing column: 'Close'",
            symbol='MSFT',
            invalid_rows=10
        )
        
        assert error.error_code == 'DATA_VALIDATION_ERROR'
        assert error.symbol == 'MSFT'
        assert error.invalid_rows == 10
    
    def test_data_leakage_error(self):
        """Test: DataLeakageError (critical)."""
        error = DataLeakageError(
            "Training data overlaps with validation",
            leakage_type='temporal_overlap',
            affected_component='data_splitting'
        )
        
        assert error.error_code == 'DATA_LEAKAGE_ERROR'
        assert error.leakage_type == 'temporal_overlap'
        assert error.affected_component == 'data_splitting'
    
    def test_feature_computation_error(self):
        """Test: FeatureComputationError."""
        error = FeatureComputationError(
            "NaN values in RSI calculation",
            feature_name='rsi_14',
            symbol='TSLA',
            affected_rows=5
        )
        
        assert error.error_code == 'FEATURE_COMPUTATION_ERROR'
        assert error.feature_name == 'rsi_14'
        assert error.symbol == 'TSLA'
        assert error.affected_rows == 5
    
    def test_configuration_error(self):
        """Test: ConfigurationError."""
        error = ConfigurationError(
            "Missing required config: IEX_CLOUD_TOKEN",
            config_key='IEX_CLOUD_TOKEN'
        )
        
        assert error.error_code == 'CONFIGURATION_ERROR'
        assert error.config_key == 'IEX_CLOUD_TOKEN'
    
    def test_reproducibility_error(self):
        """Test: ReproducibilityError."""
        error = ReproducibilityError(
            "Random seed not initialized",
            reproducibility_aspect='seed_initialization'
        )
        
        assert error.error_code == 'REPRODUCIBILITY_ERROR'
        assert error.reproducibility_aspect == 'seed_initialization'


class TestErrorHandler:
    """Test suite for ErrorHandler."""
    
    @pytest.fixture
    def logger(self):
        """Create logger for tests."""
        return logging.getLogger('test_error_handler')
    
    @pytest.fixture
    def handler(self, logger):
        """Create ErrorHandler instance."""
        return ErrorHandler(logger)
    
    # ========================================================================
    # Test: Error Logging
    # ========================================================================
    
    def test_log_data_acquisition_error(self, handler):
        """Test: Log data acquisition error."""
        error = DataAcquisitionError(
            "Network timeout",
            source='iex_cloud',
            symbol='AAPL'
        )
        
        record = handler.log_error(error, 'data_acquisition', symbol='AAPL')
        
        assert record.error_type == 'DataAcquisitionError'
        assert record.component == 'data_acquisition'
        assert record.symbol == 'AAPL'
        assert record.severity == 'HIGH'
        assert len(handler.error_records) == 1
    
    def test_log_data_leakage_error(self, handler):
        """Test: Log data leakage error (critical)."""
        error = DataLeakageError("Temporal overlap detected")
        
        record = handler.log_error(error, 'data_splitting')
        
        assert record.severity == 'CRITICAL'
        assert handler.error_counts['DataLeakageError'] == 1
    
    def test_log_feature_computation_error(self, handler):
        """Test: Log feature computation error."""
        error = FeatureComputationError(
            "NaN in rolling mean",
            feature_name='momentum',
            symbol='GOOGL'
        )
        
        record = handler.log_error(error, 'feature_engineering', symbol='GOOGL')
        
        assert record.severity == 'MEDIUM'
        assert record.symbol == 'GOOGL'
    
    def test_error_count_tracking(self, handler):
        """Test: Track error counts by type."""
        for i in range(3):
            error = DataAcquisitionError("Attempt failed")
            handler.log_error(error, 'data_acquisition')
        
        error = DataValidationError("Schema mismatch")
        handler.log_error(error, 'data_validation')
        
        assert handler.error_counts['DataAcquisitionError'] == 3
        assert handler.error_counts['DataValidationError'] == 1
        assert len(handler.error_records) == 4
    
    def test_affected_symbols_tracking(self, handler):
        """Test: Track affected symbols."""
        error1 = DataAcquisitionError("Failed")
        handler.log_error(error1, 'data_acquisition', symbol='AAPL')
        
        error2 = DataAcquisitionError("Failed")
        handler.log_error(error2, 'data_acquisition', symbol='MSFT')
        
        error3 = DataValidationError("Invalid")
        handler.log_error(error3, 'validation', symbol='AAPL')
        
        assert 'AAPL' in handler.affected_symbols['DataAcquisitionError']
        assert 'MSFT' in handler.affected_symbols['DataAcquisitionError']
        assert 'AAPL' in handler.affected_symbols['DataValidationError']
    
    # ========================================================================
    # Test: Error Handling and Recovery Actions
    # ========================================================================
    
    def test_handle_data_leakage_error_returns_halt(self, handler):
        """Test: Data leakage error -> HALT."""
        error = DataLeakageError("Temporal overlap")
        
        action = handler.handle_error(error, 'data_splitting')
        
        assert action == RecoveryAction.HALT
    
    def test_handle_configuration_error_returns_halt(self, handler):
        """Test: Configuration error -> HALT."""
        error = ConfigurationError("Missing API token")
        
        action = handler.handle_error(error, 'config')
        
        assert action == RecoveryAction.HALT
    
    def test_handle_data_acquisition_error_returns_retry(self, handler):
        """Test: Data acquisition error -> RETRY."""
        error = DataAcquisitionError("Network timeout")
        
        action = handler.handle_error(error, 'data_acquisition')
        
        assert action == RecoveryAction.RETRY
    
    def test_handle_data_validation_error_returns_skip(self, handler):
        """Test: Data validation error -> SKIP."""
        error = DataValidationError("Schema mismatch")
        
        action = handler.handle_error(error, 'validation', symbol='AAPL')
        
        assert action == RecoveryAction.SKIP
    
    def test_handle_feature_computation_error_returns_skip(self, handler):
        """Test: Feature computation error -> SKIP."""
        error = FeatureComputationError("NaN in calculation")
        
        action = handler.handle_error(error, 'feature_engineering')
        
        assert action == RecoveryAction.SKIP
    
    def test_handle_reproducibility_error_returns_continue(self, handler):
        """Test: Reproducibility error -> CONTINUE."""
        error = ReproducibilityError("Seed not set")
        
        action = handler.handle_error(error, 'initialization')
        
        assert action == RecoveryAction.CONTINUE
    
    def test_retry_logic_success(self, handler):
        """Test: Retry succeeds on subsequent attempt."""
        error = DataAcquisitionError("Network timeout")
        
        retry_count = {'attempts': 0}
        
        def retry_callback():
            retry_count['attempts'] += 1
            if retry_count['attempts'] < 2:
                raise DataAcquisitionError("Still failing")
            # Success on second attempt
        
        action = handler.handle_error(
            error,
            'data_acquisition',
            retry_callback=retry_callback,
            max_retries=3
        )
        
        assert action == RecoveryAction.CONTINUE
        assert retry_count['attempts'] == 2
    
    def test_retry_logic_exhaustion(self, handler):
        """Test: Retry exhaustion -> HALT."""
        error = DataAcquisitionError("Network timeout")
        
        def retry_callback():
            raise DataAcquisitionError("Still failing")
        
        action = handler.handle_error(
            error,
            'data_acquisition',
            retry_callback=retry_callback,
            max_retries=2
        )
        
        assert action == RecoveryAction.HALT
    
    # ========================================================================
    # Test: Error Report Generation
    # ========================================================================
    
    def test_generate_error_summary(self, handler):
        """Test: Generate comprehensive error summary."""
        error1 = DataAcquisitionError("Failed")
        handler.log_error(error1, 'data_acquisition', symbol='AAPL')
        
        error2 = DataLeakageError("Overlap")
        handler.log_error(error2, 'data_splitting')
        
        summary = handler.generate_error_summary()
        
        assert summary['total_errors'] == 2
        assert summary['unique_error_types'] == 2
        assert 'DataAcquisitionError' in summary['error_type_counts']
        assert 'DataLeakageError' in summary['error_type_counts']
        assert summary['severity_distribution']['CRITICAL'] == 1
        assert summary['severity_distribution']['HIGH'] == 1
    
    def test_generate_error_summary_to_file(self, handler):
        """Test: Save error summary to JSON file."""
        error = DataAcquisitionError("Failed")
        handler.log_error(error, 'data_acquisition', symbol='AAPL')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'error_summary.json'
            summary = handler.generate_error_summary(str(output_file))
            
            assert output_file.exists()
            
            # Verify JSON is valid and readable
            with open(output_file) as f:
                loaded = json.load(f)
            
            assert loaded['total_errors'] == 1
            assert 'DataAcquisitionError' in loaded['error_type_counts']
    
    def test_critical_errors_detection(self, handler):
        """Test: Detect presence of critical errors."""
        assert handler.has_critical_errors() is False
        
        error = DataLeakageError("Temporal overlap")
        handler.log_error(error, 'data_splitting')
        
        assert handler.has_critical_errors() is True
    
    def test_get_errors_for_component(self, handler):
        """Test: Retrieve errors for specific component."""
        error1 = DataAcquisitionError("Failed")
        handler.log_error(error1, 'data_acquisition')
        
        error2 = DataValidationError("Invalid")
        handler.log_error(error2, 'data_validation')
        
        acq_errors = handler.get_errors_for_component('data_acquisition')
        val_errors = handler.get_errors_for_component('data_validation')
        
        assert len(acq_errors) == 1
        assert len(val_errors) == 1
        assert acq_errors[0].error_type == 'DataAcquisitionError'
    
    def test_get_errors_for_symbol(self, handler):
        """Test: Retrieve errors for specific symbol."""
        error1 = DataAcquisitionError("Failed")
        handler.log_error(error1, 'data_acquisition', symbol='AAPL')
        
        error2 = DataAcquisitionError("Failed")
        handler.log_error(error2, 'data_acquisition', symbol='MSFT')
        
        aapl_errors = handler.get_errors_for_symbol('AAPL')
        msft_errors = handler.get_errors_for_symbol('MSFT')
        
        assert len(aapl_errors) == 1
        assert len(msft_errors) == 1
    
    def test_clear_errors(self, handler):
        """Test: Clear all error records."""
        error = DataAcquisitionError("Failed")
        handler.log_error(error, 'data_acquisition')
        
        assert len(handler.error_records) == 1
        
        handler.clear_errors()
        
        assert len(handler.error_records) == 0
        assert len(handler.error_counts) == 0
        assert len(handler.affected_symbols) == 0


class TestWarningsManager:
    """Test suite for WarningsManager."""
    
    @pytest.fixture
    def logger(self):
        """Create logger for tests."""
        return logging.getLogger('test_warnings')
    
    @pytest.fixture
    def warnings_mgr(self, logger):
        """Create WarningsManager instance."""
        return WarningsManager(logger)
    
    # ========================================================================
    # Test: Warning Logging
    # ========================================================================
    
    def test_log_warning(self, warnings_mgr):
        """Test: Log a warning."""
        warnings_mgr.log_warning(
            'symbol_excluded',
            message='Insufficient data',
            symbol='XYZ',
            reason='insufficient_days',
            min_required=2500,
            available=1800
        )
        
        assert len(warnings_mgr.warnings) == 1
        assert warnings_mgr.warning_counts['symbol_excluded'] == 1
        
        warning = warnings_mgr.warnings[0]
        assert warning['type'] == 'symbol_excluded'
        assert warning['symbol'] == 'XYZ'
    
    def test_log_multiple_warnings(self, warnings_mgr):
        """Test: Log multiple warnings."""
        for i in range(3):
            warnings_mgr.log_warning(
                'symbol_excluded',
                symbol=f'SYMBOL{i}'
            )
        
        warnings_mgr.log_warning('data_quality_issue', description='Low volume')
        
        assert len(warnings_mgr.warnings) == 4
        assert warnings_mgr.warning_counts['symbol_excluded'] == 3
        assert warnings_mgr.warning_counts['data_quality_issue'] == 1
    
    # ========================================================================
    # Test: Warnings Summary
    # ========================================================================
    
    def test_generate_warnings_summary(self, warnings_mgr):
        """Test: Generate warnings summary."""
        warnings_mgr.log_warning('symbol_excluded', symbol='AAA')
        warnings_mgr.log_warning('symbol_excluded', symbol='BBB')
        warnings_mgr.log_warning('data_quality_issue')
        
        summary = warnings_mgr.generate_warnings_summary()
        
        assert summary['total_warnings'] == 3
        assert summary['unique_warning_types'] == 2
        assert 'symbol_excluded' in summary['warning_type_counts']
        assert summary['warning_type_counts']['symbol_excluded'] == 2
    
    def test_generate_warnings_summary_to_file(self, warnings_mgr):
        """Test: Save warnings summary to JSON file."""
        warnings_mgr.log_warning('symbol_excluded', symbol='AAPL')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'warnings_summary.json'
            summary = warnings_mgr.generate_warnings_summary(str(output_file))
            
            assert output_file.exists()
            
            # Verify JSON is valid
            with open(output_file) as f:
                loaded = json.load(f)
            
            assert loaded['total_warnings'] == 1
    
    def test_aggregate_warnings(self, warnings_mgr):
        """Test: Aggregate warnings by type."""
        warnings_mgr.log_warning('symbol_excluded', symbol='AAA')
        warnings_mgr.log_warning('symbol_excluded', symbol='BBB')
        warnings_mgr.log_warning('data_quality_issue')
        
        aggregated = warnings_mgr.aggregate_warnings()
        
        assert len(aggregated['symbol_excluded']) == 2
        assert len(aggregated['data_quality_issue']) == 1


class TestErrorReportComparison:
    """Test suite for comparing error and warning reports together."""
    
    @pytest.fixture
    def logger(self):
        """Create logger."""
        return logging.getLogger('test_comparison')
    
    def test_error_and_warning_reports_integration(self, logger):
        """Test: Generate both error and warning reports."""
        handler = ErrorHandler(logger)
        wm = WarningsManager(logger)
        
        # Log some errors
        error = DataAcquisitionError("Failed")
        handler.log_error(error, 'data_acquisition', symbol='AAPL')
        
        # Log some warnings
        wm.log_warning('symbol_excluded', symbol='XYZ', reason='insufficient_data')
        
        error_summary = handler.generate_error_summary()
        warnings_summary = wm.generate_warnings_summary()
        
        assert error_summary['total_errors'] == 1
        assert warnings_summary['total_warnings'] == 1
        
        # Both should have timestamp
        assert 'report_timestamp' in error_summary
        assert 'report_timestamp' in warnings_summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
