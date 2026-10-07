"""
Main data cleaning orchestrator for OHLCV data.

Integrates all cleaning components (detectors, correctors, validators, adjusters)
into a unified workflow with comprehensive logging and reporting.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
import logging

from preprocessing.data_cleaning.detectors import (
    MissingValueDetector,
    SpikeDetector,
    MissingValue,
    DateGap,
    PriceSpike
)
from preprocessing.data_cleaning.correctors import (
    ForwardFillCorrector,
    OHLCCorrector,
    SpikeCorrector,
    Correction,
    ForwardFillRecord,
    OHLCCorrectionRecord,
    SpikeCorrectionRecord
)
from preprocessing.data_cleaning.validators import (
    OHLCValidator,
    DataQualityValidator,
    OHLCViolation
)
from preprocessing.data_cleaning.adjusters import (
    SplitDividendAdjuster,
    AdjustmentRecord
)


@dataclass
class CleaningReport:
    """Comprehensive report of data cleaning for a symbol."""
    symbol: str
    report_timestamp: str
    
    # Raw data stats
    raw_data_rows: int
    raw_date_range: Tuple[str, str]
    
    # Detection results
    missing_values_detected: int
    date_gaps_detected: int
    spikes_detected: int
    ohlc_violations_detected: int
    
    # Cleaning actions
    forward_fills_applied: int
    spikes_corrected: int
    ohlc_corrections_applied: int
    adjustments_applied: int
    rows_excluded: int
    
    # Cleaned data stats
    cleaned_data_rows: int
    cleaned_date_range: Optional[Tuple[str, str]]
    
    # Validation results
    validation_passed: bool
    validation_errors: List[str] = field(default_factory=list)
    completeness_percent: float = 0.0
    
    # Data quality assessment
    quality_status: str = 'UNKNOWN'  # PASS, FAIL, MANUAL_REVIEW
    quality_notes: str = ''
    
    # Detailed records
    missing_values_log: List[Dict[str, Any]] = field(default_factory=list)
    date_gaps_log: List[Dict[str, Any]] = field(default_factory=list)
    forward_fill_log: List[Dict[str, Any]] = field(default_factory=list)
    spike_corrections_log: List[Dict[str, Any]] = field(default_factory=list)
    ohlc_corrections_log: List[Dict[str, Any]] = field(default_factory=list)
    adjustments_log: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class DataCleaner:
    """
    Main orchestrator for data cleaning pipeline.
    
    Coordinates detection, correction, validation, and adjustment of OHLCV data.
    Produces cleaned DataFrames and comprehensive cleaning reports.
    
    Workflow:
    1. Detect missing values, gaps, spikes, OHLC violations
    2. Correct forward-fillable missing values
    3. Correct OHLC relationship violations
    4. Correct/verify price spikes
    5. Apply stock split/dividend adjustments
    6. Validate cleaned data quality
    7. Generate comprehensive report
    
    Examples
    --------
    >>> cleaner = DataCleaner()
    >>> cleaned_df, report = cleaner.clean_symbol('AAPL', raw_df)
    >>> print(report.quality_status)
    >>> print(f"Rows retained: {report.cleaned_data_rows} / {report.raw_data_rows}")
    """
    
    def __init__(
        self,
        max_forward_fill_days: int = 2,
        spike_threshold: float = 0.20,
        min_completeness: float = 0.99,
        apply_adjustments: bool = True,
        logger: logging.Logger = None
    ):
        """
        Initialize DataCleaner.
        
        Parameters
        ----------
        max_forward_fill_days : int
            Maximum consecutive days to forward-fill (default: 2)
        spike_threshold : float
            Daily return threshold for spike detection (default: 0.20 = ±20%)
        min_completeness : float
            Minimum data completeness ratio (default: 0.99 = 99%)
        apply_adjustments : bool
            Whether to apply stock split/dividend adjustments (default: True)
        logger : logging.Logger, optional
            Logger instance
        """
        self.max_forward_fill_days = max_forward_fill_days
        self.spike_threshold = spike_threshold
        self.min_completeness = min_completeness
        self.apply_adjustments = apply_adjustments
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.missing_detector = MissingValueDetector(logger=self.logger)
        self.spike_detector = SpikeDetector(
            threshold=spike_threshold,
            logger=self.logger
        )
        self.forward_fill_corrector = ForwardFillCorrector(
            max_consecutive_days=max_forward_fill_days,
            logger=self.logger
        )
        self.ohlc_corrector = OHLCCorrector(logger=self.logger)
        self.spike_corrector = SpikeCorrector(logger=self.logger)
        self.ohlc_validator = OHLCValidator(logger=self.logger)
        self.quality_validator = DataQualityValidator(
            min_completeness=min_completeness,
            logger=self.logger
        )
        self.adjuster = SplitDividendAdjuster(logger=self.logger)
    
    def clean_symbol(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        Clean OHLCV data for a single symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol (e.g., 'AAPL')
        df : pd.DataFrame
            Raw OHLCV DataFrame with Date index
        
        Returns
        -------
        Tuple[pd.DataFrame, CleaningReport]
            (cleaned_df, cleaning_report)
        """
        self.logger.info(f"Starting data cleaning for {symbol}")
        
        # Initialize report
        report = CleaningReport(
            symbol=symbol,
            report_timestamp=datetime.utcnow().isoformat() + 'Z',
            raw_data_rows=len(df),
            raw_date_range=(
                str(df.index.min().date()),
                str(df.index.max().date())
            ) if len(df) > 0 else (None, None),
            missing_values_detected=0,
            date_gaps_detected=0,
            spikes_detected=0,
            ohlc_violations_detected=0,
            forward_fills_applied=0,
            spikes_corrected=0,
            ohlc_corrections_applied=0,
            adjustments_applied=0,
            rows_excluded=0,
            cleaned_data_rows=0,
            cleaned_date_range=None,
            validation_passed=False
        )
        
        # Step 1: Detection
        self.logger.debug("Step 1: Running detection algorithms")
        cleaned_df = df.copy()
        
        # Detect missing values
        missing_values = self.missing_detector.detect_missing_values(cleaned_df)
        date_gaps = self.missing_detector.detect_gaps(cleaned_df)
        report.missing_values_detected = len(missing_values)
        report.date_gaps_detected = len(date_gaps)
        report.missing_values_log = [
            {
                'date': str(mv.date.date()),
                'column': mv.column,
                'reason': mv.reason
            }
            for mv in missing_values
        ]
        report.date_gaps_log = [
            {
                'start_date': str(dg.start_date.date()),
                'end_date': str(dg.end_date.date()),
                'gap_days': dg.gap_days,
                'reason': dg.reason
            }
            for dg in date_gaps
        ]
        
        # Detect spikes
        spikes = self.spike_detector.detect_spikes(cleaned_df)
        report.spikes_detected = len(spikes)
        
        # Detect OHLC violations
        violations = self.ohlc_validator.validate_relationships(cleaned_df)
        report.ohlc_violations_detected = len(violations)
        
        # Step 2: Correction - Forward fill
        self.logger.debug("Step 2a: Applying forward-fill corrections")
        cleaned_df, ff_corrections = self.forward_fill_corrector.correct_missing_values(
            cleaned_df
        )
        report.forward_fills_applied = len(ff_corrections)
        report.forward_fill_log = [
            {
                'start_date': str(ffr.start_date.date()),
                'end_date': str(ffr.end_date.date()),
                'column': ffr.column,
                'consecutive_days': ffr.consecutive_days,
                'reason': ffr.reason
            }
            for ffr in self.forward_fill_corrector.forward_fill_records
        ]
        
        # Step 2b: Correction - OHLC violations
        self.logger.debug("Step 2b: Correcting OHLC relationship violations")
        rows_before_ohlc = len(cleaned_df)
        cleaned_df, ohlc_corrections = self.ohlc_corrector.correct_relationships(
            cleaned_df
        )
        rows_after_ohlc = len(cleaned_df)
        report.ohlc_corrections_applied = len(ohlc_corrections)
        report.rows_excluded += rows_before_ohlc - rows_after_ohlc
        report.ohlc_corrections_log = [
            {
                'date': str(oc.date.date()),
                'violation_type': oc.violation_type,
                'before_values': oc.before_values,
                'after_values': oc.after_values
            }
            for oc in ohlc_corrections
        ]
        
        # Step 2c: Correction - Spikes
        self.logger.debug("Step 2c: Correcting detected spikes")
        rows_before_spikes = len(cleaned_df)
        cleaned_df, spike_corrections = self.spike_corrector.correct_spikes(
            cleaned_df,
            spikes
        )
        rows_after_spikes = len(cleaned_df)
        report.spikes_corrected = len(spike_corrections)
        report.rows_excluded += rows_before_spikes - rows_after_spikes
        report.spike_corrections_log = [
            {
                'date': str(sc.date.date()),
                'daily_return': float(sc.daily_return),
                'previous_close': float(sc.previous_close),
                'current_value': float(sc.current_value),
                'action': sc.action,
                'reason': sc.reason
            }
            for sc in spike_corrections
        ]
        
        # Step 3: Adjustments (splits/dividends)
        self.logger.debug("Step 3: Applying stock split/dividend adjustments")
        if self.apply_adjustments:
            cleaned_df, adjustment_records = self.adjuster.adjust_prices(
                symbol,
                cleaned_df
            )
            report.adjustments_applied = len(adjustment_records)
            report.adjustments_log = [
                {
                    'date': str(ar.date.date()),
                    'type': ar.adjustment_type,
                    'factor': float(ar.factor),
                    'before_close': float(ar.before_close) if ar.before_close else None,
                    'after_close': float(ar.after_close),
                    'description': ar.description
                }
                for ar in adjustment_records
            ]
        
        # Step 4: Validation
        self.logger.debug("Step 4: Validating cleaned data")
        quality_assessment = self.quality_validator.validate_quality(cleaned_df)
        
        # Extract validation status
        validation_passed = quality_assessment.get('overall_pass', False)
        report.validation_passed = validation_passed
        
        # Extract completeness
        ohlc_check = quality_assessment.get('checks', {}).get('ohlc_relationships', {})
        if 'actual' in ohlc_check:
            # Parse percentage string
            actual_pct = ohlc_check['actual']
            if isinstance(actual_pct, str):
                actual_pct = float(actual_pct.rstrip('%'))
            report.completeness_percent = actual_pct
        
        # Check for validation errors
        for check_name, check_result in quality_assessment.get('checks', {}).items():
            if isinstance(check_result, dict):
                if not check_result.get('pass', False):
                    if 'actual' in check_result:
                        report.validation_errors.append(
                            f"{check_name}: {check_result.get('actual', 'failed')}"
                        )
        
        # Determine quality status
        if validation_passed:
            report.quality_status = 'PASS'
            report.quality_notes = f"Data quality excellent; {report.cleaned_data_rows} rows retained"
        else:
            if len(report.validation_errors) > 0:
                report.quality_status = 'FAIL'
                report.quality_notes = f"Data quality issues detected: {len(report.validation_errors)} errors"
            else:
                report.quality_status = 'MANUAL_REVIEW'
                report.quality_notes = "Data requires manual review"
        
        # Final stats
        report.cleaned_data_rows = len(cleaned_df)
        report.cleaned_date_range = (
            str(cleaned_df.index.min().date()),
            str(cleaned_df.index.max().date())
        ) if len(cleaned_df) > 0 else (None, None)
        
        self.logger.info(
            f"Cleaning complete for {symbol}: "
            f"{report.cleaned_data_rows} rows retained from {report.raw_data_rows}; "
            f"quality_status={report.quality_status}"
        )
        
        return cleaned_df, report


class CleaningReportGenerator:
    """
    Generates cleaning reports in JSON format.
    
    Examples
    --------
    >>> generator = CleaningReportGenerator()
    >>> json_report = generator.generate_report(cleaning_report)
    >>> generator.save_report(cleaning_report, 'results/cleaning_reports/AAPL.json')
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize CleaningReportGenerator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_report(self, report: CleaningReport) -> str:
        """
        Generate JSON report from CleaningReport object.
        
        Parameters
        ----------
        report : CleaningReport
            Cleaning report object
        
        Returns
        -------
        str
            JSON string representation
        """
        return report.to_json()
    
    def save_report(
        self,
        report: CleaningReport,
        output_path: str
    ) -> None:
        """
        Save cleaning report to JSON file.
        
        Parameters
        ----------
        report : CleaningReport
            Cleaning report object
        output_path : str
            Path to output JSON file
        """
        try:
            with open(output_path, 'w') as f:
                f.write(self.generate_report(report))
            self.logger.info(f"Saved cleaning report to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save cleaning report to {output_path}: {e}")


class AuditTrail:
    """
    Tracks all data transformations in data cleaning pipeline.
    
    Maintains detailed log of every transformation with timestamp, symbol,
    date range, and before/after values for audit and reproducibility.
    
    Examples
    --------
    >>> trail = AuditTrail()
    >>> trail.log_transformation('AAPL', 'forward_fill', start_date, end_date, 'missing_close')
    >>> aggregate = trail.get_aggregate_statistics()
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize AuditTrail.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.transformations: List[Dict[str, Any]] = []
    
    def log_transformation(
        self,
        symbol: str,
        transformation_type: str,
        date_range: Tuple[pd.Timestamp, pd.Timestamp],
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a data transformation.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
        transformation_type : str
            Type of transformation (e.g., 'forward_fill', 'spike_correction')
        date_range : Tuple[pd.Timestamp, pd.Timestamp]
            (start_date, end_date) of transformation
        reason : str
            Reason for transformation
        details : Optional[Dict[str, Any]]
            Additional details about transformation
        """
        start_date, end_date = date_range
        
        transformation = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'symbol': symbol,
            'transformation_type': transformation_type,
            'date_range_start': str(start_date.date()),
            'date_range_end': str(end_date.date()),
            'reason': reason
        }
        
        if details:
            transformation.update(details)
        
        self.transformations.append(transformation)
    
    def get_aggregate_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics of all transformations.
        
        Returns
        -------
        Dict[str, Any]
            Statistics including counts by type, symbols processed, etc.
        """
        if not self.transformations:
            return {
                'total_transformations': 0,
                'symbols_processed': 0,
                'transformation_types': {}
            }
        
        # Count by transformation type
        type_counts = {}
        for trans in self.transformations:
            trans_type = trans.get('transformation_type', 'unknown')
            type_counts[trans_type] = type_counts.get(trans_type, 0) + 1
        
        # Unique symbols
        symbols = set(trans.get('symbol') for trans in self.transformations)
        
        return {
            'total_transformations': len(self.transformations),
            'symbols_processed': len(symbols),
            'transformation_types': type_counts,
            'unique_symbols': sorted(symbols)
        }
    
    def to_json(self) -> str:
        """
        Serialize audit trail to JSON.
        
        Returns
        -------
        str
            JSON representation of audit trail
        """
        return json.dumps(
            {
                'audit_timestamp': datetime.utcnow().isoformat() + 'Z',
                'aggregate_statistics': self.get_aggregate_statistics(),
                'transformation_log': self.transformations
            },
            indent=2,
            default=str
        )
    
    def save_to_file(self, output_path: str) -> None:
        """
        Save audit trail to JSON file.
        
        Parameters
        ----------
        output_path : str
            Path to output JSON file
        """
        try:
            with open(output_path, 'w') as f:
                f.write(self.to_json())
            self.logger.info(f"Saved audit trail to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save audit trail to {output_path}: {e}")

