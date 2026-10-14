"""
Utilities package for Stock Forecasting System.

Provides:
- Logging infrastructure (structured, JSON, dual-output)
- Reproducibility management (seed initialization)
- Data leakage detection (comprehensive checks)
- Error handling (custom exceptions, recovery strategies)
- Warnings management (non-critical issue tracking)
"""

from .logging_config import (
    configure_logging,
    get_logger,
    JSONFormatter,
    StructuredLogger
)

from .reproducibility import ReproducibilityManager, initialize_reproducibility

from .leakage_detector import (
    LeakageDetector,
    LeakageViolation
)

from .error_handler import (
    # Exception classes
    StockForecastingError,
    DataAcquisitionError,
    DataValidationError,
    DataLeakageError,
    FeatureComputationError,
    ConfigurationError,
    ReproducibilityError,
    
    # Enums
    ErrorSeverity,
    RecoveryAction,
    
    # Handlers
    ErrorHandler,
    WarningsManager,
    ErrorRecord
)

__all__ = [
    # Logging
    'configure_logging',
    'get_logger',
    'JSONFormatter',
    'StructuredLogger',
    
    # Reproducibility
    'ReproducibilityManager',
    'initialize_reproducibility',
    
    # Leakage Detection
    'LeakageDetector',
    'LeakageViolation',
    
    # Error Handling
    'StockForecastingError',
    'DataAcquisitionError',
    'DataValidationError',
    'DataLeakageError',
    'FeatureComputationError',
    'ConfigurationError',
    'ReproducibilityError',
    'ErrorSeverity',
    'RecoveryAction',
    'ErrorHandler',
    'WarningsManager',
    'ErrorRecord',
]
