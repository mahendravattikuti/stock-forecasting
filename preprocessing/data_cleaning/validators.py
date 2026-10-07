"""
Validation rules for OHLCV data quality assurance.

Validates OHLC relationships, price bounds, and data integrity.
Includes quality assurance, reporting, and symbol exclusion management.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json


@dataclass
class OHLCViolation:
    """Represents an OHLCV relationship violation."""
    date: pd.Timestamp
    violation_type: str  # 'high_lt_close', 'low_gt_close', 'open_gt_high', etc.
    values: Dict[str, float]


class OHLCValidator:
    """
    Validates OHLC relationships and price constraints.
    
    Checks:
    - High >= Close >= Low >= Open
    - High >= Open, High >= Low
    - Low <= Open, Low <= Close
    - All values > 0
    
    Examples
    --------
    >>> validator = OHLCValidator()
    >>> violations = validator.validate_relationships(df)
    >>> stats = validator.compute_statistics(df)
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize OHLCValidator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.violations: List[OHLCViolation] = []
    
    def validate_relationships(self, df: pd.DataFrame) -> List[OHLCViolation]:
        """
        Validate OHLC relationships for each bar.
        
        Checks: High >= Close >= Low >= Open (general constraint)
        And specific relationships.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        
        Returns
        -------
        List[OHLCViolation]
            List of violations found
        """
        self.violations = []
        
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            self.logger.warning("Missing required OHLC columns")
            return self.violations
        
        for date, row in df.iterrows():
            o, h, l, c = row['Open'], row['High'], row['Low'], row['Close']
            
            # Skip if any NaN
            if pd.isna([o, h, l, c]).any():
                continue
            
            # High >= Close >= Low >= Open
            if h < c:
                self.violations.append(
                    OHLCViolation(
                        date=date,
                        violation_type='high_lt_close',
                        values={'High': h, 'Close': c}
                    )
                )
            
            if c < l:
                self.violations.append(
                    OHLCViolation(
                        date=date,
                        violation_type='close_lt_low',
                        values={'Close': c, 'Low': l}
                    )
                )
            
            if l < o:
                self.violations.append(
                    OHLCViolation(
                        date=date,
                        violation_type='low_lt_open',
                        values={'Low': l, 'Open': o}
                    )
                )
            
            # Additional checks
            if h < o:
                self.violations.append(
                    OHLCViolation(
                        date=date,
                        violation_type='high_lt_open',
                        values={'High': h, 'Open': o}
                    )
                )
            
            if h < l:
                self.violations.append(
                    OHLCViolation(
                        date=date,
                        violation_type='high_lt_low',
                        values={'High': h, 'Low': l}
                    )
                )
        
        self.logger.info(f"Found {len(self.violations)} OHLC violations")
        return self.violations
    
    def compute_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute summary statistics for validation.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        
        Returns
        -------
        Dict[str, Any]
            Statistics including min, max, mean, std per column
        """
        stats = {}
        
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in df.columns:
                continue
            
            data = df[col].dropna()
            if len(data) == 0:
                stats[col] = {'count': 0}
            else:
                stats[col] = {
                    'count': len(data),
                    'min': float(data.min()),
                    'max': float(data.max()),
                    'mean': float(data.mean()),
                    'median': float(data.median()),
                    'std': float(data.std()),
                    'null_count': df[col].isna().sum()
                }
        
        return stats
    
    def validate_statistics(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that statistics are sensible (no inf, all numbers valid).
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_valid, error_messages)
        """
        errors = []
        stats = self.compute_statistics(df)
        
        for col, col_stats in stats.items():
            if col_stats.get('count', 0) == 0:
                continue
            
            # Check for inf
            if np.isinf(col_stats.get('mean', 0)):
                errors.append(f"{col}: mean is infinite")
            
            # Check for negative volumes (should be > 0)
            if col == 'Volume' and col_stats.get('min', 0) < 0:
                errors.append(f"{col}: minimum is negative")
        
        return len(errors) == 0, errors
    
    def check_price_ordering(self, df: pd.DataFrame) -> Tuple[int, int]:
        """
        Check how many bars have valid Open <= Close and Low <= High.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        
        Returns
        -------
        Tuple[int, int]
            (valid_bars, total_bars)
        """
        if not all(col in df.columns for col in ['Open', 'Close', 'Low', 'High']):
            return 0, 0
        
        total = len(df)
        valid = 0
        
        for _, row in df.iterrows():
            o, c, l, h = row['Open'], row['Close'], row['Low'], row['High']
            
            # Skip if any NaN
            if pd.isna([o, c, l, h]).any():
                continue
            
            # Check valid ordering
            if o <= c and l <= h and l <= o <= h and l <= c <= h:
                valid += 1
        
        return valid, total


class DataQualityValidator:
    """
    Comprehensive data quality validation.
    
    Checks:
    - Minimum completeness threshold
    - OHLC relationship validity
    - Summary statistics validity
    - Multi-day price stasis
    
    Examples
    --------
    >>> validator = DataQualityValidator(min_trading_days=2500)
    >>> quality = validator.validate_quality(df)
    """
    
    def __init__(
        self,
        min_trading_days: int = 2500,
        min_completeness: float = 0.99,
        logger: logging.Logger = None
    ):
        """
        Initialize DataQualityValidator.
        
        Parameters
        ----------
        min_trading_days : int
            Minimum required trading days
        min_completeness : float
            Minimum data completeness ratio (0.99 = 99%)
        logger : logging.Logger, optional
            Logger instance
        """
        self.min_trading_days = min_trading_days
        self.min_completeness = min_completeness
        self.logger = logger or logging.getLogger(__name__)
        self.ohlc_validator = OHLCValidator(logger)
    
    def validate_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive quality validation.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        
        Returns
        -------
        Dict[str, Any]
            Quality assessment results
        """
        results = {
            'total_rows': len(df),
            'checks': {}
        }
        
        # Check 1: Minimum trading days
        has_min_days = len(df) >= self.min_trading_days
        results['checks']['min_trading_days'] = {
            'pass': has_min_days,
            'requirement': self.min_trading_days,
            'actual': len(df)
        }
        
        # Check 2: OHLC relationships
        valid_bars, total_bars = self.ohlc_validator.check_price_ordering(df)
        ohlc_pct = valid_bars / total_bars if total_bars > 0 else 0
        results['checks']['ohlc_relationships'] = {
            'pass': ohlc_pct >= self.min_completeness,
            'requirement': f"{self.min_completeness*100}%",
            'actual': f"{ohlc_pct*100:.2f}%",
            'valid': valid_bars,
            'total': total_bars
        }
        
        # Check 3: Statistics validity
        is_valid_stats, stat_errors = self.ohlc_validator.validate_statistics(df)
        results['checks']['statistics'] = {
            'pass': is_valid_stats,
            'errors': stat_errors
        }
        
        # Check 4: Multi-day stasis
        if 'Close' in df.columns:
            stasis_ranges = self._detect_price_stasis(df, min_days=5)
            results['checks']['price_stasis'] = {
                'detected': len(stasis_ranges) > 0,
                'ranges': stasis_ranges
            }
        
        # Overall pass/fail
        results['overall_pass'] = all(
            check.get('pass', False)
            for check in results['checks'].values()
            if isinstance(check, dict)
        )
        
        return results
    
    def _detect_price_stasis(self, df: pd.DataFrame, min_days: int = 5) -> List[Tuple]:
        """
        Detect periods where price doesn't change for multiple days.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        min_days : int
            Minimum consecutive days required to flag
        
        Returns
        -------
        List[Tuple]
            List of (start_date, end_date, num_days) stasis ranges
        """
        if 'Close' not in df.columns:
            return []
        
        stasis_ranges = []
        close = df['Close'].dropna()
        
        if len(close) < min_days:
            return stasis_ranges
        
        # Find consecutive same values
        stasis_start = None
        stasis_count = 1
        prev_value = close.iloc[0]
        
        for i in range(1, len(close)):
            curr_value = close.iloc[i]
            
            if curr_value == prev_value:
                if stasis_start is None:
                    stasis_start = close.index[i-1]
                stasis_count += 1
            else:
                # Stasis ended
                if stasis_count >= min_days and stasis_start is not None:
                    stasis_ranges.append((
                        stasis_start,
                        close.index[i-1],
                        stasis_count
                    ))
                stasis_start = None
                stasis_count = 1
            
            prev_value = curr_value
        
        # Check if stasis extends to end
        if stasis_count >= min_days and stasis_start is not None:
            stasis_ranges.append((
                stasis_start,
                close.index[-1],
                stasis_count
            ))
        
        return stasis_ranges



class ValidationReportGenerator:
    """
    Generates comprehensive validation reports for data quality assurance.
    
    Creates validation_report.json documenting pass/fail status per symbol,
    completeness metrics, excluded symbols, and manual review flags.
    
    Examples
    --------
    >>> generator = ValidationReportGenerator(logger=logger)
    >>> report = generator.generate_validation_report(
    ...     validation_results, excluded_symbols, output_path
    ... )
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize ValidationReportGenerator.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_validation_report(
        self,
        validation_results: Dict[str, Dict[str, Any]],
        excluded_symbols: Dict[str, str],
        output_path: str = "results/validation_report.json"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.
        
        Parameters
        ----------
        validation_results : Dict[str, Dict[str, Any]]
            Results from DataQualityValidator.validate_quality() per symbol
        excluded_symbols : Dict[str, str]
            Dictionary mapping excluded symbol to exclusion reason
        output_path : str
            Path to write validation_report.json
        
        Returns
        -------
        Dict[str, Any]
            Validation report with pass/fail per symbol, completeness %, excluded symbols
        """
        report = {
            'report_timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'total_symbols': len(validation_results) + len(excluded_symbols),
                'symbols_passed': 0,
                'symbols_excluded': len(excluded_symbols),
                'symbols_manual_review': 0
            },
            'symbols': {},
            'excluded_symbols': {},
            'manual_review_flags': []
        }
        
        # Process validation results
        for symbol, result in validation_results.items():
            overall_pass = result.get('overall_pass', False)
            
            if overall_pass:
                report['summary']['symbols_passed'] += 1
            else:
                report['summary']['symbols_manual_review'] += 1
                report['manual_review_flags'].append({
                    'symbol': symbol,
                    'reason': 'failed validation checks',
                    'details': result.get('checks', {})
                })
            
            # Extract completeness percentage
            ohlc_check = result.get('checks', {}).get('ohlc_relationships', {})
            completeness_pct = 0.0
            if 'actual' in ohlc_check:
                # Parse percentage string like "99.50%"
                pct_str = ohlc_check['actual']
                if isinstance(pct_str, str) and '%' in pct_str:
                    completeness_pct = float(pct_str.replace('%', ''))
            
            report['symbols'][symbol] = {
                'pass': overall_pass,
                'completeness_percent': completeness_pct,
                'checks': result.get('checks', {})
            }
        
        # Process excluded symbols
        for symbol, reason in excluded_symbols.items():
            report['excluded_symbols'][symbol] = reason
        
        # Write report to file
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Validation report written to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to write validation report: {e}")
            raise
        
        return report


class SymbolExclusionManager:
    """
    Manages symbol exclusion with logging and summary generation.
    
    Tracks excluded symbols, logs exclusion reasons with dates,
    and generates exclusion_summary.json for audit purposes.
    
    Examples
    --------
    >>> manager = SymbolExclusionManager(logger=logger)
    >>> manager.exclude_symbol("AAPL", "insufficient_data")
    >>> summary = manager.generate_exclusion_summary()
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize SymbolExclusionManager.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self.excluded_symbols: Dict[str, Dict[str, Any]] = {}
    
    def exclude_symbol(
        self,
        symbol: str,
        reason: str,
        exclusion_date: str = None,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Record exclusion of a symbol with reason and date.
        
        Parameters
        ----------
        symbol : str
            Stock symbol to exclude
        reason : str
            Reason for exclusion (e.g., 'insufficient_data', 'invalid_ohlc', etc.)
        exclusion_date : str, optional
            Date of exclusion (ISO format); defaults to current date
        details : Dict[str, Any], optional
            Additional details about exclusion (e.g., actual data points, threshold)
        """
        if exclusion_date is None:
            exclusion_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        self.excluded_symbols[symbol] = {
            'reason': reason,
            'exclusion_date': exclusion_date,
            'details': details or {}
        }
        
        self.logger.info(f"Excluded symbol {symbol}: {reason}")
    
    def get_excluded_symbols(self) -> Dict[str, str]:
        """
        Get all excluded symbols with reasons.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping symbol to exclusion reason
        """
        return {
            symbol: data['reason']
            for symbol, data in self.excluded_symbols.items()
        }
    
    def is_excluded(self, symbol: str) -> bool:
        """
        Check if a symbol is excluded.
        
        Parameters
        ----------
        symbol : str
            Stock symbol to check
        
        Returns
        -------
        bool
            True if symbol is excluded, False otherwise
        """
        return symbol in self.excluded_symbols
    
    def generate_exclusion_summary(
        self,
        output_path: str = "results/exclusion_summary.json"
    ) -> Dict[str, Any]:
        """
        Generate JSON summary of all excluded symbols and reasons.
        
        Parameters
        ----------
        output_path : str
            Path to write exclusion_summary.json
        
        Returns
        -------
        Dict[str, Any]
            Summary of exclusions organized by reason
        """
        # Organize exclusions by reason
        by_reason: Dict[str, List[str]] = {}
        for symbol, data in self.excluded_symbols.items():
            reason = data['reason']
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(symbol)
        
        summary = {
            'summary_timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_excluded': len(self.excluded_symbols),
            'excluded_by_reason': by_reason,
            'detailed_exclusions': self.excluded_symbols
        }
        
        # Write summary to file
        try:
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            self.logger.info(f"Exclusion summary written to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to write exclusion summary: {e}")
            raise
        
        return summary
