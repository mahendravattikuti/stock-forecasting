"""
Error handling infrastructure with custom exception hierarchy.

Defines custom exception classes for different error scenarios and provides
centralized error handling and recovery strategies.

As per Requirement 14: Error Handling and Logging
"""

import logging
import json
import traceback
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class RecoveryAction(Enum):
    """Possible recovery actions for errors."""
    RETRY = 'retry'
    SKIP = 'skip'
    CONTINUE = 'continue'
    HALT = 'halt'
    FALLBACK = 'fallback'


# ============================================================================
# Custom Exception Classes
# ============================================================================

class StockForecastingError(Exception):
    """Base exception for Stock Forecasting System."""
    
    def __init__(
        self,
        message: str,
        error_code: str = 'UNKNOWN',
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()


class DataAcquisitionError(StockForecastingError):
    """
    Raised when data acquisition fails.
    
    Covers: network errors, source unavailable, insufficient data,
    timeout, authentication failures.
    
    Severity: HIGH
    Common Recovery: RETRY, FALLBACK, SKIP
    """
    
    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        symbol: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = {'source': source, 'symbol': symbol, **(context or {})}
        super().__init__(message, 'DATA_ACQUISITION_ERROR', full_context)
        self.source = source
        self.symbol = symbol


class DataValidationError(StockForecastingError):
    """
    Raised when data validation fails.
    
    Covers: invalid schema, missing required columns, wrong data types,
    value out of range, inconsistent dates.
    
    Severity: HIGH
    Common Recovery: SKIP, CONTINUE
    """
    
    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        invalid_rows: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = {
            'symbol': symbol,
            'invalid_rows': invalid_rows,
            **(context or {})
        }
        super().__init__(message, 'DATA_VALIDATION_ERROR', full_context)
        self.symbol = symbol
        self.invalid_rows = invalid_rows


class DataLeakageError(StockForecastingError):
    """
    Raised when data leakage is detected.
    
    Covers: preprocessing artifacts fitted on non-training data,
    validation/test data used in training, future data in rolling windows,
    overlapping train/val/test splits.
    
    Severity: CRITICAL (always halts pipeline)
    Common Recovery: HALT
    """
    
    def __init__(
        self,
        message: str,
        leakage_type: Optional[str] = None,
        affected_component: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = {
            'leakage_type': leakage_type,
            'affected_component': affected_component,
            **(context or {})
        }
        super().__init__(message, 'DATA_LEAKAGE_ERROR', full_context)
        self.leakage_type = leakage_type
        self.affected_component = affected_component


class FeatureComputationError(StockForecastingError):
    """
    Raised when feature computation fails.
    
    Covers: NaN values, infinite values, computational errors,
    missing dependencies, invalid parameters.
    
    Severity: MEDIUM
    Common Recovery: SKIP, CONTINUE, RETRY
    """
    
    def __init__(
        self,
        message: str,
        feature_name: Optional[str] = None,
        symbol: Optional[str] = None,
        affected_rows: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = {
            'feature_name': feature_name,
            'symbol': symbol,
            'affected_rows': affected_rows,
            **(context or {})
        }
        super().__init__(message, 'FEATURE_COMPUTATION_ERROR', full_context)
        self.feature_name = feature_name
        self.symbol = symbol
        self.affected_rows = affected_rows


class ConfigurationError(StockForecastingError):
    """
    Raised when configuration is invalid.
    
    Covers: missing required config, invalid parameter values,
    conflicting settings, type mismatch.
    
    Severity: HIGH
    Common Recovery: HALT (needs manual fix)
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = {'config_key': config_key, **(context or {})}
        super().__init__(message, 'CONFIGURATION_ERROR', full_context)
        self.config_key = config_key


class ReproducibilityError(StockForecastingError):
    """
    Raised when reproducibility requirements are violated.
    
    Covers: seed not set, artifact version mismatch,
    configuration mismatch, non-deterministic behavior detected.
    
    Severity: MEDIUM
    Common Recovery: CONTINUE (with warning)
    """
    
    def __init__(
        self,
        message: str,
        reproducibility_aspect: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = {
            'reproducibility_aspect': reproducibility_aspect,
            **(context or {})
        }
        super().__init__(message, 'REPRODUCIBILITY_ERROR', full_context)
        self.reproducibility_aspect = reproducibility_aspect


# ============================================================================
# Error Handler
# ============================================================================

@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    timestamp: str
    error_type: str
    error_code: str
    message: str
    severity: str
    context: Dict[str, Any]
    recovery_action: str
    traceback: Optional[str] = None
    symbol: Optional[str] = None
    component: Optional[str] = None


class ErrorHandler:
    """
    Centralized error handling and recovery.
    
    Responsibilities:
    - Log errors with context
    - Decide recovery action (retry, skip, continue, halt)
    - Track error statistics
    - Generate error summary reports
    - Implement recovery strategies
    
    Examples
    --------
    >>> handler = ErrorHandler(logger)
    >>> try:
    ...     risky_operation()
    ... except DataAcquisitionError as e:
    ...     action = handler.handle_error(e, component='data_acquisition')
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize ErrorHandler.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for structured logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_records: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self.affected_symbols: Dict[str, List[str]] = {}  # error_type -> symbols
    
    def log_error(
        self,
        error: Exception,
        component: str,
        symbol: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorRecord:
        """
        Log an error with context.
        
        Parameters
        ----------
        error : Exception
            The exception that occurred
        component : str
            Component where error occurred (e.g., 'data_acquisition', 'feature_engineering')
        symbol : str, optional
            Stock symbol affected
        context : Dict[str, Any], optional
            Additional context information
        
        Returns
        -------
        ErrorRecord
            Record of the logged error
        """
        error_type = type(error).__name__
        error_code = getattr(error, 'error_code', 'UNKNOWN')
        
        # Determine severity
        severity = self._determine_severity(error)
        
        # Build error context
        error_context = {
            'component': component,
            'symbol': symbol,
            **(getattr(error, 'context', {})),
            **(context or {})
        }
        
        # Create error record
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            error_type=error_type,
            error_code=error_code,
            message=str(error),
            severity=severity,
            context=error_context,
            recovery_action='UNKNOWN',
            traceback=traceback.format_exc(),
            symbol=symbol,
            component=component
        )
        
        # Store record
        self.error_records.append(record)
        
        # Update counts
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Update affected symbols
        if symbol:
            if error_type not in self.affected_symbols:
                self.affected_symbols[error_type] = []
            if symbol not in self.affected_symbols[error_type]:
                self.affected_symbols[error_type].append(symbol)
        
        # Log to logger
        log_message = f"[{component}] {error_type}: {str(error)}"
        if symbol:
            log_message += f" | Symbol: {symbol}"
        
        if severity == 'CRITICAL':
            self.logger.critical(log_message)
        elif severity == 'HIGH':
            self.logger.error(log_message)
        elif severity == 'MEDIUM':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return record
    
    def handle_error(
        self,
        error: Exception,
        component: str,
        symbol: Optional[str] = None,
        retry_callback: Optional[Callable] = None,
        max_retries: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryAction:
        """
        Decide and execute error recovery action.
        
        Parameters
        ----------
        error : Exception
            The exception that occurred
        component : str
            Component where error occurred
        symbol : str, optional
            Stock symbol affected
        retry_callback : Callable, optional
            Function to call for RETRY action
        max_retries : int
            Maximum retry attempts (default: 3)
        context : Dict[str, Any], optional
            Additional context
        
        Returns
        -------
        RecoveryAction
            Action taken in response to error
        """
        # Log the error
        record = self.log_error(error, component, symbol, context)
        
        # Determine recovery action based on error type and severity
        action = self._determine_recovery_action(error, component)
        
        # Update record with action
        record.recovery_action = action.value
        
        # Execute recovery action
        if action == RecoveryAction.RETRY and retry_callback:
            self.logger.info(f"Retrying operation in {component}...")
            for attempt in range(max_retries):
                try:
                    self.logger.debug(f"Retry attempt {attempt + 1}/{max_retries}")
                    retry_callback()
                    action = RecoveryAction.CONTINUE
                    self.logger.info("Retry successful")
                    record.recovery_action = action.value
                    break
                except Exception as retry_error:
                    if attempt == max_retries - 1:
                        self.logger.error(f"All {max_retries} retry attempts failed")
                        action = RecoveryAction.HALT
                        record.recovery_action = action.value
                    else:
                        self.logger.warning(f"Retry attempt {attempt + 1} failed, retrying...")
        
        elif action == RecoveryAction.HALT:
            self.logger.critical(f"HALT: Cannot recover from {error.__class__.__name__} in {component}")
        
        elif action == RecoveryAction.SKIP:
            self.logger.warning(f"SKIP: Skipping symbol {symbol} due to error in {component}")
        
        elif action == RecoveryAction.CONTINUE:
            self.logger.info(f"CONTINUE: Continuing despite error in {component}")
        
        return action
    
    def _determine_severity(self, error: Exception) -> str:
        """
        Determine error severity from exception type.
        
        Parameters
        ----------
        error : Exception
            The exception
        
        Returns
        -------
        str
            Severity level: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
        """
        if isinstance(error, DataLeakageError):
            return 'CRITICAL'
        elif isinstance(error, (DataAcquisitionError, DataValidationError, ConfigurationError)):
            return 'HIGH'
        elif isinstance(error, (FeatureComputationError, ReproducibilityError)):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _determine_recovery_action(self, error: Exception, component: str) -> RecoveryAction:
        """
        Determine recovery action based on error type and component.
        
        Parameters
        ----------
        error : Exception
            The exception
        component : str
            Component where error occurred
        
        Returns
        -------
        RecoveryAction
            Recommended recovery action
        """
        # Data leakage is always critical -> halt
        if isinstance(error, DataLeakageError):
            return RecoveryAction.HALT
        
        # Configuration errors are unrecoverable -> halt
        if isinstance(error, ConfigurationError):
            return RecoveryAction.HALT
        
        # Acquisition errors -> retry
        if isinstance(error, DataAcquisitionError):
            return RecoveryAction.RETRY
        
        # Validation errors -> skip (exclude symbol) or continue
        if isinstance(error, DataValidationError):
            return RecoveryAction.SKIP
        
        # Feature computation errors -> skip or continue
        if isinstance(error, FeatureComputationError):
            return RecoveryAction.SKIP
        
        # Reproducibility errors -> continue with warning
        if isinstance(error, ReproducibilityError):
            return RecoveryAction.CONTINUE
        
        # Default
        return RecoveryAction.CONTINUE
    
    def generate_error_summary(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive error summary report.
        
        Parameters
        ----------
        output_file : str, optional
            Path to save error_summary.json
        
        Returns
        -------
        Dict[str, Any]
            Error summary report
        """
        summary = {
            'report_timestamp': datetime.now().isoformat(),
            'total_errors': len(self.error_records),
            'unique_error_types': len(self.error_counts),
            'error_type_counts': self.error_counts,
            'severity_distribution': self._count_by_severity(),
            'affected_symbols': self.affected_symbols,
            'errors': [
                {
                    'timestamp': record.timestamp,
                    'type': record.error_type,
                    'code': record.error_code,
                    'message': record.message,
                    'severity': record.severity,
                    'component': record.component,
                    'symbol': record.symbol,
                    'recovery_action': record.recovery_action,
                    'context': record.context
                }
                for record in self.error_records
            ]
        }
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"Error summary saved to {output_file}")
        
        return summary
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for record in self.error_records:
            counts[record.severity] = counts.get(record.severity, 0) + 1
        return counts
    
    def has_critical_errors(self) -> bool:
        """Check if any critical errors were recorded."""
        return any(record.severity == 'CRITICAL' for record in self.error_records)
    
    def get_errors_for_component(self, component: str) -> List[ErrorRecord]:
        """Get all errors for a specific component."""
        return [record for record in self.error_records if record.component == component]
    
    def get_errors_for_symbol(self, symbol: str) -> List[ErrorRecord]:
        """Get all errors affecting a specific symbol."""
        return [record for record in self.error_records if record.symbol == symbol]
    
    def clear_errors(self) -> None:
        """Clear all recorded errors."""
        self.error_records = []
        self.error_counts = {}
        self.affected_symbols = {}


class WarningsManager:
    """
    Manages non-critical warnings and issues.
    
    Tracks warnings about:
    - Symbols excluded from analysis
    - Data quality issues
    - Deprecated features
    - Performance degradation
    - Reproducibility concerns
    
    Examples
    --------
    >>> wm = WarningsManager(logger)
    >>> wm.log_warning('symbol_excluded', symbol='XYZ', reason='insufficient_data')
    >>> report = wm.generate_warnings_summary()
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize WarningsManager.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.warnings: List[Dict[str, Any]] = []
        self.warning_counts: Dict[str, int] = {}
    
    def log_warning(
        self,
        warning_type: str,
        message: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log a warning.
        
        Parameters
        ----------
        warning_type : str
            Type of warning (e.g., 'symbol_excluded', 'data_quality_issue')
        message : str, optional
            Human-readable warning message
        **kwargs
            Additional details
        """
        warning_record = {
            'timestamp': datetime.now().isoformat(),
            'type': warning_type,
            'message': message or warning_type,
            **kwargs
        }
        
        self.warnings.append(warning_record)
        self.warning_counts[warning_type] = self.warning_counts.get(warning_type, 0) + 1
        
        full_message = f"[{warning_type}] {message or warning_type}"
        if kwargs:
            full_message += f" | {json.dumps(kwargs)}"
        
        self.logger.warning(full_message)
    
    def generate_warnings_summary(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate warnings summary report.
        
        Parameters
        ----------
        output_file : str, optional
            Path to save warnings_summary.json
        
        Returns
        -------
        Dict[str, Any]
            Warnings summary
        """
        summary = {
            'report_timestamp': datetime.now().isoformat(),
            'total_warnings': len(self.warnings),
            'unique_warning_types': len(self.warning_counts),
            'warning_type_counts': self.warning_counts,
            'warnings': self.warnings
        }
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"Warnings summary saved to {output_file}")
        
        return summary
    
    def aggregate_warnings(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate warnings by type.
        
        Returns
        -------
        Dict[str, List[Dict[str, Any]]]
            Warnings grouped by type
        """
        aggregated: Dict[str, List[Dict[str, Any]]] = {}
        for warning in self.warnings:
            warning_type = warning['type']
            if warning_type not in aggregated:
                aggregated[warning_type] = []
            aggregated[warning_type].append(warning)
        return aggregated


if __name__ == '__main__':
    # Example usage
    from .logging_config import configure_logging
    
    logger = configure_logging()
    handler = ErrorHandler(logger)
    wm = WarningsManager(logger)
    
    # Simulate some errors
    try:
        raise DataAcquisitionError(
            "Failed to fetch data from IEX Cloud",
            source='iex_cloud',
            symbol='AAPL',
            context={'status_code': 429, 'retry_after': 60}
        )
    except DataAcquisitionError as e:
        action = handler.handle_error(e, component='data_acquisition', symbol='AAPL')
        print(f"Recovery action: {action.value}")
    
    # Log warnings
    wm.log_warning(
        'symbol_excluded',
        symbol='XYZ',
        reason='insufficient_data',
        min_required_days=2500,
        available_days=1800
    )
    
    # Generate reports
    error_report = handler.generate_error_summary()
    warnings_report = wm.generate_warnings_summary()
    
    print("\nError Summary:")
    print(json.dumps(error_report, indent=2))
    print("\nWarnings Summary:")
    print(json.dumps(warnings_report, indent=2))
