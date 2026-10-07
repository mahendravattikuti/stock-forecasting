"""
Validation rules for OHLCV data quality assurance.

Validates OHLC relationships, price bounds, and data integrity.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging


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
