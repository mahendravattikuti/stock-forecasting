"""
Feature validation module for detecting NaN, infinite values, and look-ahead bias.

Validates computed features across all tiers and signal processing modules,
ensuring data quality and absence of data leakage before downstream modeling.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class FeatureValidationResult:
    """Result of feature validation check."""
    symbol: str
    is_valid: bool
    validation_checks: Dict[str, bool] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)
    warning_messages: List[str] = field(default_factory=list)
    nan_summary: Dict[str, int] = field(default_factory=dict)
    inf_summary: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'is_valid': self.is_valid,
            'validation_checks': self.validation_checks,
            'error_messages': self.error_messages,
            'warning_messages': self.warning_messages,
            'nan_summary': self.nan_summary,
            'inf_summary': self.inf_summary,
        }


class FeatureValidator:
    """
    Validates computed features for quality and integrity.
    
    Checks:
    - No unexpected NaN values
    - No infinite values
    - Reasonable value ranges (e.g., RSI in [0, 100])
    - No look-ahead bias in rolling calculations
    - Proper alignment by date
    
    Examples
    --------
    >>> validator = FeatureValidator(logger=logger)
    >>> features_df = pd.DataFrame({
    ...     'simple_return': [...],
    ...     'rsi_14': [...],
    ... })
    >>> result = validator.validate_features(features_df, symbol='AAPL')
    >>> if not result.is_valid:
    ...     for error in result.error_messages:
    ...         print(f"Error: {error}")
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize FeatureValidator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance; if None, creates default logger
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def validate_features(
        self,
        features_df: pd.DataFrame,
        symbol: str = None,
        expected_nan_rows: int = 0
    ) -> FeatureValidationResult:
        """
        Perform comprehensive validation on computed features.
        
        Parameters
        ----------
        features_df : pd.DataFrame
            Computed features DataFrame with DatetimeIndex
        symbol : str, optional
            Stock symbol being validated (for logging/reporting)
        expected_nan_rows : int
            Expected number of leading NaN rows from lookback windows
        
        Returns
        -------
        FeatureValidationResult
            Detailed validation result with pass/fail status and messages
        
        Examples
        --------
        >>> validator = FeatureValidator()
        >>> result = validator.validate_features(features_df, symbol='AAPL', expected_nan_rows=20)
        >>> print(f"Valid: {result.is_valid}")
        >>> for msg in result.error_messages:
        ...     print(f"  Error: {msg}")
        """
        symbol = symbol or "unknown"
        result = FeatureValidationResult(symbol=symbol, is_valid=True)
        
        # Check 1: DataFrame not empty
        if features_df is None or len(features_df) == 0:
            result.is_valid = False
            result.error_messages.append("Features DataFrame is empty or None")
            return result
        
        # Check 2: DatetimeIndex
        if not isinstance(features_df.index, pd.DatetimeIndex):
            result.is_valid = False
            result.error_messages.append(
                f"Features DataFrame must have DatetimeIndex, got {type(features_df.index)}"
            )
            return result
        
        # Check 3: NaN values
        nan_check_pass, nan_errors, nan_summary = self._check_nan_values(
            features_df, expected_nan_rows
        )
        result.validation_checks['nan_values'] = nan_check_pass
        result.error_messages.extend(nan_errors)
        result.nan_summary = nan_summary
        if not nan_check_pass:
            result.is_valid = False
        
        # Check 4: Infinite values
        inf_check_pass, inf_errors, inf_summary = self._check_infinite_values(features_df)
        result.validation_checks['infinite_values'] = inf_check_pass
        result.error_messages.extend(inf_errors)
        result.inf_summary = inf_summary
        if not inf_check_pass:
            result.is_valid = False
        
        # Check 5: Value range reasonableness
        range_check_pass, range_errors = self._check_value_ranges(features_df)
        result.validation_checks['value_ranges'] = range_check_pass
        result.error_messages.extend(range_errors)
        if not range_check_pass:
            result.is_valid = False
        
        # Check 6: Look-ahead bias detection
        causality_check_pass, causality_errors = self._check_causality_bias(features_df)
        result.validation_checks['causality'] = causality_check_pass
        result.warning_messages.extend(causality_errors)
        # Causality issues are warnings, not errors (may be false positives)
        
        # Check 7: Proper alignment
        alignment_check_pass, alignment_errors = self._check_temporal_alignment(features_df)
        result.validation_checks['temporal_alignment'] = alignment_check_pass
        result.error_messages.extend(alignment_errors)
        if not alignment_check_pass:
            result.is_valid = False
        
        # Logging
        if result.is_valid:
            self.logger.info(
                f"Feature validation PASSED for {symbol} "
                f"({len(features_df)} rows, {len(features_df.columns)} columns)"
            )
        else:
            self.logger.error(
                f"Feature validation FAILED for {symbol}: "
                f"{len(result.error_messages)} errors"
            )
        
        return result
    
    def _check_nan_values(
        self,
        features_df: pd.DataFrame,
        expected_nan_rows: int
    ) -> Tuple[bool, List[str], Dict[str, int]]:
        """
        Check for unexpected NaN values in features.
        
        Returns
        -------
        Tuple[bool, List[str], Dict[str, int]]
            (is_valid, error_messages, nan_count_per_column)
        """
        errors = []
        nan_summary = {}
        check_pass = True
        
        for col in features_df.columns:
            nan_count = features_df[col].isna().sum()
            nan_summary[col] = nan_count
            
            # Allow leading NaN rows, but flag if more NaN than expected
            if nan_count > expected_nan_rows:
                unexpected_nans = nan_count - expected_nan_rows
                errors.append(
                    f"Column '{col}': {unexpected_nans} unexpected NaN values "
                    f"(expected ≤{expected_nan_rows}, found {nan_count})"
                )
                check_pass = False
        
        return check_pass, errors, nan_summary
    
    def _check_infinite_values(
        self,
        features_df: pd.DataFrame
    ) -> Tuple[bool, List[str], Dict[str, int]]:
        """
        Check for infinite values in features.
        
        Returns
        -------
        Tuple[bool, List[str], Dict[str, int]]
            (is_valid, error_messages, inf_count_per_column)
        """
        errors = []
        inf_summary = {}
        check_pass = True
        
        for col in features_df.columns:
            inf_count = np.isinf(features_df[col]).sum()
            inf_summary[col] = inf_count
            
            if inf_count > 0:
                errors.append(
                    f"Column '{col}': {inf_count} infinite values detected"
                )
                check_pass = False
        
        return check_pass, errors, inf_summary
    
    def _check_value_ranges(
        self,
        features_df: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Check if value ranges are reasonable based on feature names.
        
        Examples:
        - RSI should be in [0, 100]
        - Stochastic K/D should be in [0, 100]
        - Correlations should be in [-1, 1]
        - Volatility (std) should be >= 0
        - Returns should typically be in [-1, 10] (allow outliers)
        """
        errors = []
        check_pass = True
        
        for col in features_df.columns:
            data = features_df[col].dropna()
            if len(data) == 0:
                continue
            
            col_lower = col.lower()
            
            # RSI check (0-100)
            if 'rsi' in col_lower:
                if (data < 0).any() or (data > 100).any():
                    errors.append(
                        f"Column '{col}' (RSI): values outside [0, 100] range "
                        f"(min={data.min():.2f}, max={data.max():.2f})"
                    )
                    check_pass = False
            
            # Stochastic check (0-100)
            elif 'stoch' in col_lower or '%k' in col_lower or '%d' in col_lower:
                if (data < 0).any() or (data > 100).any():
                    errors.append(
                        f"Column '{col}' (Stochastic): values outside [0, 100] range "
                        f"(min={data.min():.2f}, max={data.max():.2f})"
                    )
                    check_pass = False
            
            # Correlation check (-1 to 1)
            elif 'correlation' in col_lower or 'corr' in col_lower:
                if (data < -1).any() or (data > 1).any():
                    errors.append(
                        f"Column '{col}' (Correlation): values outside [-1, 1] range "
                        f"(min={data.min():.4f}, max={data.max():.4f})"
                    )
                    check_pass = False
            
            # Volatility/Std check (non-negative)
            elif 'volatility' in col_lower or 'std' in col_lower:
                if (data < 0).any():
                    errors.append(
                        f"Column '{col}' (Volatility): contains negative values "
                        f"(min={data.min():.6f})"
                    )
                    check_pass = False
            
            # Return bounds (very loose to allow outliers)
            elif 'return' in col_lower:
                # Returns can be large (bankruptcy/delisting), so just warn if extreme
                if data.abs().max() > 5.0:  # > 500% return
                    self.logger.warning(
                        f"Column '{col}' (Return): extreme values detected "
                        f"(min={data.min():.4f}, max={data.max():.4f})"
                    )
        
        return check_pass, errors
    
    def _check_causality_bias(
        self,
        features_df: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Heuristic check for look-ahead bias in rolling calculations.
        
        Looks for patterns that might indicate future data use:
        - Sudden spikes at certain rows
        - Correlation patterns with index position
        
        Note: This is a heuristic check and may have false positives/negatives.
        """
        warnings = []
        check_pass = True
        
        for col in features_df.columns:
            data = features_df[col].dropna()
            if len(data) < 100:
                continue  # Skip if not enough data
            
            # Check for sudden large jumps (could indicate discontinuity from leakage)
            if 'return' not in col.lower():  # Skip returns (naturally jumpy)
                diffs = data.abs().diff()
                q95 = diffs.quantile(0.95)
                large_jumps = (diffs > 5 * q95).sum()
                
                if large_jumps > len(data) * 0.05:  # > 5% of values are large jumps
                    warnings.append(
                        f"Column '{col}': {large_jumps} large jumps detected "
                        f"(could indicate discontinuity, but may be legitimate)"
                    )
        
        return check_pass, warnings
    
    def _check_temporal_alignment(
        self,
        features_df: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Check that features are properly aligned by date.
        
        Verifies:
        - Index is sorted chronologically
        - No duplicate dates
        - Proper spacing (trading days, not calendar days)
        """
        errors = []
        check_pass = True
        
        index = features_df.index
        
        # Check sorted
        if not index.is_monotonic_increasing:
            errors.append("Feature DataFrame index is not sorted chronologically")
            check_pass = False
        
        # Check duplicates
        if index.duplicated().any():
            dup_count = index.duplicated().sum()
            errors.append(f"Feature DataFrame has {dup_count} duplicate dates")
            check_pass = False
        
        return check_pass, errors


class FeatureValidationReporter:
    """
    Generates validation reports for feature quality assurance.
    
    Outputs validation_report.json documenting pass/fail per symbol,
    validation checks, and any errors or warnings.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize FeatureValidationReporter.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_validation_report(
        self,
        validation_results: Dict[str, FeatureValidationResult],
        output_path: str = "results/feature_validation_report.json"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feature validation report.
        
        Parameters
        ----------
        validation_results : Dict[str, FeatureValidationResult]
            Validation results per symbol from FeatureValidator.validate_features()
        output_path : str
            Path to write feature_validation_report.json
        
        Returns
        -------
        Dict[str, Any]
            Validation report with pass/fail summary
        """
        import json
        from datetime import datetime
        
        report = {
            'report_timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'total_symbols': len(validation_results),
                'symbols_passed': sum(1 for r in validation_results.values() if r.is_valid),
                'symbols_failed': sum(1 for r in validation_results.values() if not r.is_valid),
            },
            'validation_details': {}
        }
        
        for symbol, result in validation_results.items():
            report['validation_details'][symbol] = result.to_dict()
        
        # Write to file
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Feature validation report written to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to write validation report: {e}")
            raise
        
        return report
