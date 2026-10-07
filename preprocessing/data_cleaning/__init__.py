"""
Data cleaning module for OHLCV preprocessing.

Detects, corrects, validates, and adjusts historical stock price data.
"""

# Detectors
from .detectors import (
    MissingValueDetector,
    SpikeDetector,
    MissingValue,
    DateGap,
    PriceSpike
)

# Validators
from .validators import (
    OHLCValidator,
    DataQualityValidator,
    OHLCViolation
)

# Correctors
from .correctors import (
    ForwardFillCorrector,
    OHLCCorrector,
    SpikeCorrector,
    Correction,
    ForwardFillRecord,
    OHLCCorrectionRecord,
    SpikeCorrectionRecord
)

# Adjusters
from .adjusters import (
    SplitDividendAdjuster,
    StockAdjustment,
    AdjustmentRecord
)

# Orchestrator & Reporting
from .cleaner import (
    DataCleaner,
    CleaningReport,
    CleaningReportGenerator,
    AuditTrail
)

__all__ = [
    # Detectors
    'MissingValueDetector',
    'SpikeDetector',
    'MissingValue',
    'DateGap',
    'PriceSpike',
    # Validators
    'OHLCValidator',
    'DataQualityValidator',
    'OHLCViolation',
    # Correctors
    'ForwardFillCorrector',
    'OHLCCorrector',
    'SpikeCorrector',
    'Correction',
    'ForwardFillRecord',
    'OHLCCorrectionRecord',
    'SpikeCorrectionRecord',
    # Adjusters
    'SplitDividendAdjuster',
    'StockAdjustment',
    'AdjustmentRecord',
    # Orchestrator & Reporting
    'DataCleaner',
    'CleaningReport',
    'CleaningReportGenerator',
    'AuditTrail'
]
