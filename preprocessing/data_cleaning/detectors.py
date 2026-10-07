"""
Detection algorithms for data quality issues in OHLCV data.

Identifies missing values, spikes, and other anomalies.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


@dataclass
class MissingValue:
    """Represents a missing value anomaly."""
    date: pd.Timestamp
    column: str
    reason: str  # 'NaN', 'zero', 'negative'


@dataclass
class DateGap:
    """Represents a gap in trading dates."""
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    gap_days: int
    reason: str  # 'weekend', 'holiday', 'missing'


@dataclass
class PriceSpike:
    """Represents an unusual price movement."""
    date: pd.Timestamp
    column: str
    daily_return: float
    previous_close: float
    current_value: float
    severity: str  # 'low', 'medium', 'high'


class MissingValueDetector:
    """
    Detects missing values in OHLCV data.
    
    Identifies:
    - NaN values
    - Zero prices (invalid)
    - Negative prices (invalid)
    - Zero volume (suspicious)
    
    Examples
    --------
    >>> detector = MissingValueDetector()
    >>> missing = detector.detect_missing_values(df)
    >>> gaps = detector.detect_gaps(df)
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize MissingValueDetector.
        
        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.missing_values: List[MissingValue] = []
        self.date_gaps: List[DateGap] = []
    
    def detect_missing_values(self, df: pd.DataFrame) -> List[MissingValue]:
        """
        Detect NaN, zero, and negative values in OHLCV data.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with columns [Open, High, Low, Close, Volume]
        
        Returns
        -------
        List[MissingValue]
            List of detected missing value anomalies
        """
        self.missing_values = []
        
        price_columns = ['Open', 'High', 'Low', 'Close']
        volume_column = 'Volume'
        
        # Check for NaN values
        for col in price_columns + [volume_column]:
            if col not in df.columns:
                continue
            
            nan_indices = df[col].isna()
            for date, is_nan in nan_indices.items():
                if is_nan:
                    self.missing_values.append(
                        MissingValue(date=date, column=col, reason='NaN')
                    )
        
        # Check for zero or negative prices
        for col in price_columns:
            if col not in df.columns:
                continue
            
            invalid_mask = df[col] <= 0
            for date, is_invalid in invalid_mask.items():
                if is_invalid and not pd.isna(df.loc[date, col]):
                    reason = 'zero' if df.loc[date, col] == 0 else 'negative'
                    self.missing_values.append(
                        MissingValue(date=date, column=col, reason=reason)
                    )
        
        # Check for zero volume
        if volume_column in df.columns:
            zero_vol = df[volume_column] == 0
            for date, is_zero in zero_vol.items():
                if is_zero:
                    self.missing_values.append(
                        MissingValue(date=date, column=volume_column, reason='zero')
                    )
        
        self.logger.info(f"Detected {len(self.missing_values)} missing value anomalies")
        return self.missing_values
    
    def detect_gaps(self, df: pd.DataFrame) -> List[DateGap]:
        """
        Detect gaps in trading dates (missing trading days).
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with date index
        
        Returns
        -------
        List[DateGap]
            List of detected date gaps
        """
        self.date_gaps = []
        
        if len(df) < 2:
            return self.date_gaps
        
        # Get date differences
        dates = df.index.sort_values()
        date_diffs = dates.diff()[1:]  # Skip first NaT
        
        # Trading day is typically 1, gaps are > 1
        gap_threshold = pd.Timedelta(days=1)
        
        previous_date = dates[0]
        for i, current_date in enumerate(dates[1:], 1):
            diff = date_diffs[i]
            
            # Check if gap > 1 day
            if diff > gap_threshold:
                gap_days = diff.days
                self.date_gaps.append(
                    DateGap(
                        start_date=previous_date,
                        end_date=current_date,
                        gap_days=gap_days,
                        reason='missing'
                    )
                )
            
            previous_date = current_date
        
        self.logger.info(f"Detected {len(self.date_gaps)} date gaps")
        return self.date_gaps
    
    def detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive anomaly detection.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        
        Returns
        -------
        Dict[str, Any]
            Summary of detected anomalies
        """
        missing = self.detect_missing_values(df)
        gaps = self.detect_gaps(df)
        
        return {
            'missing_values': missing,
            'date_gaps': gaps,
            'total_missing': len(missing),
            'total_gaps': len(gaps)
        }
    
    def get_unfillable_ranges(self, max_consecutive_gaps: int = 2) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
        """
        Get date ranges that cannot be forward-filled (gaps > max_consecutive_gaps).
        
        Parameters
        ----------
        max_consecutive_gaps : int
            Maximum consecutive missing days to allow (default: 2)
        
        Returns
        -------
        List[Tuple[pd.Timestamp, pd.Timestamp]]
            List of (start_date, end_date) ranges that are unfillable
        """
        unfillable = []
        
        for gap in self.date_gaps:
            if gap.gap_days > max_consecutive_gaps:
                unfillable.append((gap.start_date, gap.end_date))
        
        return unfillable


class SpikeDetector:
    """
    Detects unusual price spikes in OHLCV data.
    
    Identifies single-day price movements exceeding a threshold (default: ±20%).
    
    Examples
    --------
    >>> detector = SpikeDetector(threshold=0.20)
    >>> spikes = detector.detect_spikes(df)
    """
    
    def __init__(
        self,
        threshold: float = 0.20,
        logger: logging.Logger = None
    ):
        """
        Initialize SpikeDetector.
        
        Parameters
        ----------
        threshold : float
            Daily return threshold for spike detection (default: 0.20 = ±20%)
        logger : logging.Logger, optional
            Logger instance
        """
        self.threshold = threshold
        self.logger = logger or logging.getLogger(__name__)
        self.spikes: List[PriceSpike] = []
    
    def detect_spikes(self, df: pd.DataFrame) -> List[PriceSpike]:
        """
        Detect price spikes in Close prices.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with Close column
        
        Returns
        -------
        List[PriceSpike]
            List of detected price spikes
        """
        self.spikes = []
        
        if 'Close' not in df.columns or len(df) < 2:
            return self.spikes
        
        close_prices = df['Close'].dropna()
        
        # Calculate daily returns
        returns = close_prices.pct_change()
        
        # Find spikes
        for date, ret in returns.items():
            if pd.isna(ret) or ret == 0:
                continue
            
            # Check if absolute return exceeds threshold
            if abs(ret) > self.threshold:
                idx = df.index.get_loc(date)
                prev_close = close_prices.iloc[idx - 1] if idx > 0 else close_prices.iloc[idx]
                current_close = close_prices.loc[date]
                
                # Categorize severity
                abs_ret = abs(ret)
                if abs_ret > 0.5:  # 50%+
                    severity = 'high'
                elif abs_ret > 0.3:  # 30%+
                    severity = 'medium'
                else:
                    severity = 'low'
                
                self.spikes.append(
                    PriceSpike(
                        date=date,
                        column='Close',
                        daily_return=ret,
                        previous_close=prev_close,
                        current_value=current_close,
                        severity=severity
                    )
                )
        
        self.logger.info(f"Detected {len(self.spikes)} price spikes")
        return self.spikes
    
    def get_spikes_by_severity(self, severity: str) -> List[PriceSpike]:
        """
        Get spikes of specific severity.
        
        Parameters
        ----------
        severity : str
            Severity level: 'low', 'medium', 'high'
        
        Returns
        -------
        List[PriceSpike]
            Filtered spikes
        """
        return [s for s in self.spikes if s.severity == severity]
