"""
Correction algorithms for fixing data quality issues in OHLCV data.

Applies corrections for missing values, OHLC relationship violations, and price spikes.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging


@dataclass
class Correction:
    """Represents a correction applied to data."""
    date: pd.Timestamp
    column: str
    reason: str
    previous_value: float
    corrected_value: float
    correction_type: str  # 'forward_fill', 'interpolation', 'removal', 'adjustment'


@dataclass
class ForwardFillRecord:
    """Record of a forward-fill correction."""
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    column: str
    consecutive_days: int
    reason: str


@dataclass
class OHLCCorrectionRecord:
    """Record of an OHLC relationship correction."""
    date: pd.Timestamp
    violation_type: str
    before_values: Dict[str, float]
    after_values: Dict[str, float]


@dataclass
class SpikeCorrectionRecord:
    """Record of a spike correction."""
    date: pd.Timestamp
    daily_return: float
    previous_close: float
    current_value: float
    action: str  # 'accepted', 'removed', 'interpolated'
    reason: str


class ForwardFillCorrector:
    """
    Corrects missing values by forward-filling OHLC data.
    
    Behavior:
    - Forward-fills OHLC (Open, High, Low, Close) up to max 2 consecutive days
    - For Volume: forward-fill or set to median of nearby days
    - Beyond 2 days: marks as unfillable, excludes date range
    - Logs all forward-fills with date, field, and reason
    
    Examples
    --------
    >>> corrector = ForwardFillCorrector(max_consecutive_days=2)
    >>> corrected_df, corrections = corrector.correct_missing_values(df)
    """
    
    def __init__(
        self,
        max_consecutive_days: int = 2,
        volume_strategy: str = 'median',
        logger: logging.Logger = None
    ):
        """
        Initialize ForwardFillCorrector.
        
        Parameters
        ----------
        max_consecutive_days : int
            Maximum consecutive days to forward-fill (default: 2)
        volume_strategy : str
            Strategy for filling volume: 'forward_fill' or 'median' (default: 'median')
        logger : logging.Logger, optional
            Logger instance
        """
        self.max_consecutive_days = max_consecutive_days
        self.volume_strategy = volume_strategy
        self.logger = logger or logging.getLogger(__name__)
        self.corrections: List[Correction] = []
        self.forward_fill_records: List[ForwardFillRecord] = []
    
    def correct_missing_values(
        self,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[Correction]]:
        """
        Correct missing values via forward-fill (max 2 days) or exclusion.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with potential missing values
        
        Returns
        -------
        Tuple[pd.DataFrame, List[Correction]]
            (corrected_df, list_of_corrections)
        """
        self.corrections = []
        self.forward_fill_records = []
        corrected_df = df.copy()
        
        price_columns = ['Open', 'High', 'Low', 'Close']
        volume_column = 'Volume'
        
        # Identify NaN positions for each column
        for col in price_columns:
            if col not in corrected_df.columns:
                continue
            
            nan_mask = corrected_df[col].isna()
            if not nan_mask.any():
                continue
            
            # Find consecutive NaN groups
            nan_groups = self._find_consecutive_nans(nan_mask)
            
            # Process each group
            rows_to_exclude = []
            for start_idx, end_idx in nan_groups:
                group_size = end_idx - start_idx + 1
                
                if group_size <= self.max_consecutive_days:
                    # Forward-fill
                    self._apply_forward_fill(
                        corrected_df, col, start_idx, end_idx
                    )
                    
                    # Record this forward-fill
                    start_date = corrected_df.index[start_idx]
                    end_date = corrected_df.index[end_idx]
                    self.forward_fill_records.append(
                        ForwardFillRecord(
                            start_date=start_date,
                            end_date=end_date,
                            column=col,
                            consecutive_days=group_size,
                            reason=f"Missing {col} for {group_size} consecutive days"
                        )
                    )
                    
                    self.logger.info(
                        f"Forward-filled {col} from {start_date} to {end_date} "
                        f"({group_size} days)"
                    )
                else:
                    # Mark as unfillable
                    for i in range(start_idx, end_idx + 1):
                        rows_to_exclude.append(corrected_df.index[i])
                    
                    start_date = corrected_df.index[start_idx]
                    end_date = corrected_df.index[end_idx]
                    self.logger.warning(
                        f"Cannot forward-fill {col} from {start_date} to {end_date}: "
                        f"{group_size} consecutive days exceeds max {self.max_consecutive_days}"
                    )
            
            # Exclude rows that cannot be forward-filled
            if rows_to_exclude:
                corrected_df = corrected_df.drop(rows_to_exclude)
        
        # Handle Volume column
        if volume_column in corrected_df.columns:
            corrected_df = self._correct_volume(corrected_df)
        
        self.logger.info(
            f"Forward-fill correction complete: "
            f"{len(self.corrections)} corrections, "
            f"{len(self.forward_fill_records)} forward-fill records"
        )
        
        return corrected_df, self.corrections
    
    def _find_consecutive_nans(self, nan_mask: pd.Series) -> List[Tuple[int, int]]:
        """
        Find groups of consecutive NaN indices.
        
        Parameters
        ----------
        nan_mask : pd.Series
            Boolean series where True indicates NaN
        
        Returns
        -------
        List[Tuple[int, int]]
            List of (start_idx, end_idx) for each consecutive NaN group
        """
        groups = []
        nan_indices = np.where(nan_mask.values)[0]
        
        if len(nan_indices) == 0:
            return groups
        
        start = nan_indices[0]
        prev = nan_indices[0]
        
        for idx in nan_indices[1:]:
            if idx != prev + 1:
                # Gap found, record previous group
                groups.append((start, prev))
                start = idx
            prev = idx
        
        # Record last group
        groups.append((start, prev))
        
        return groups
    
    def _apply_forward_fill(
        self,
        df: pd.DataFrame,
        column: str,
        start_idx: int,
        end_idx: int
    ) -> None:
        """
        Apply forward-fill to a specific column and index range.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to modify in-place
        column : str
            Column name to forward-fill
        start_idx : int
            Start index (inclusive)
        end_idx : int
            End index (inclusive)
        """
        if start_idx == 0:
            # No previous value to fill from
            return
        
        fill_value = df.iloc[start_idx - 1][column]
        
        if pd.isna(fill_value):
            # Previous value is also NaN, cannot fill
            return
        
        for i in range(start_idx, end_idx + 1):
            date = df.index[i]
            previous_value = df.iloc[i][column] if not pd.isna(df.iloc[i][column]) else None
            
            df.iloc[i, df.columns.get_loc(column)] = fill_value
            
            self.corrections.append(
                Correction(
                    date=date,
                    column=column,
                    reason=f"Forward-filled from {df.index[start_idx - 1].strftime('%Y-%m-%d')}",
                    previous_value=previous_value,
                    corrected_value=fill_value,
                    correction_type='forward_fill'
                )
            )
    
    def _correct_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Correct Volume column: forward-fill or set to median of nearby days.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with Volume column
        
        Returns
        -------
        pd.DataFrame
            DataFrame with corrected Volume
        """
        if 'Volume' not in df.columns:
            return df
        
        df_corrected = df.copy()
        nan_mask = df_corrected['Volume'].isna()
        
        if not nan_mask.any():
            return df_corrected
        
        if self.volume_strategy == 'forward_fill':
            df_corrected['Volume'].fillna(method='ffill', inplace=True)
        elif self.volume_strategy == 'median':
            # Use rolling median of ±5 days
            window_size = 5
            for idx in np.where(nan_mask.values)[0]:
                start = max(0, idx - window_size)
                end = min(len(df_corrected), idx + window_size + 1)
                
                nearby_volumes = df_corrected.iloc[start:end]['Volume'].dropna()
                if len(nearby_volumes) > 0:
                    median_vol = nearby_volumes.median()
                    df_corrected.iloc[idx, df_corrected.columns.get_loc('Volume')] = median_vol
                    
                    self.corrections.append(
                        Correction(
                            date=df_corrected.index[idx],
                            column='Volume',
                            reason=f"Set to median of nearby {len(nearby_volumes)} days",
                            previous_value=None,
                            corrected_value=median_vol,
                            correction_type='interpolation'
                        )
                    )
        
        return df_corrected


class OHLCCorrector:
    """
    Corrects OHLC relationship violations.
    
    Behavior:
    - Validates that High >= Close >= Low >= Open
    - Fixes violations using linear interpolation (weighted average of Open and Close)
    - Logs all corrections with date, violation type, and new values
    
    Examples
    --------
    >>> corrector = OHLCCorrector(fix_method='linear_interpolation')
    >>> corrected_df, corrections = corrector.correct_relationships(df)
    """
    
    def __init__(
        self,
        fix_method: str = 'linear_interpolation',
        logger: logging.Logger = None
    ):
        """
        Initialize OHLCCorrector.
        
        Parameters
        ----------
        fix_method : str
            Method for fixing violations: 'linear_interpolation' or 'removal' (default: 'linear_interpolation')
        logger : logging.Logger, optional
            Logger instance
        """
        self.fix_method = fix_method
        self.logger = logger or logging.getLogger(__name__)
        self.corrections: List[OHLCCorrectionRecord] = []
    
    def correct_relationships(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[OHLCCorrectionRecord]]:
        """
        Correct OHLC relationship violations.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with potential violations
        
        Returns
        -------
        Tuple[pd.DataFrame, List[OHLCCorrectionRecord]]
            (corrected_df, list_of_corrections)
        """
        self.corrections = []
        corrected_df = df.copy()
        
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in corrected_df.columns for col in required_cols):
            self.logger.warning("Missing required OHLC columns")
            return corrected_df, self.corrections
        
        rows_to_exclude = []
        
        for idx, (date, row) in enumerate(corrected_df.iterrows()):
            o, h, l, c = row['Open'], row['High'], row['Low'], row['Close']
            
            # Skip if any NaN
            if pd.isna([o, h, l, c]).any():
                continue
            
            # Check for violations
            violations = self._check_violations(o, h, l, c)
            
            if violations:
                before_values = {'Open': o, 'High': h, 'Low': l, 'Close': c}
                
                if self.fix_method == 'linear_interpolation':
                    # Use weighted average of Open and Close for adjustments
                    corrected_values = self._fix_via_interpolation(o, h, l, c)
                    
                    # Update DataFrame
                    corrected_df.loc[date, 'Open'] = corrected_values['Open']
                    corrected_df.loc[date, 'High'] = corrected_values['High']
                    corrected_df.loc[date, 'Low'] = corrected_values['Low']
                    corrected_df.loc[date, 'Close'] = corrected_values['Close']
                    
                    after_values = corrected_values
                    
                    for violation in violations:
                        self.corrections.append(
                            OHLCCorrectionRecord(
                                date=date,
                                violation_type=violation,
                                before_values=before_values,
                                after_values=after_values
                            )
                        )
                    
                    self.logger.info(
                        f"Corrected OHLC violations on {date}: {violations}"
                    )
                else:
                    # Mark for removal
                    rows_to_exclude.append(date)
                    self.logger.warning(
                        f"Excluding row {date} due to OHLC violations: {violations}"
                    )
        
        # Exclude rows with unfixable violations
        if rows_to_exclude:
            corrected_df = corrected_df.drop(rows_to_exclude)
        
        self.logger.info(
            f"OHLC correction complete: "
            f"{len(self.corrections)} corrections applied"
        )
        
        return corrected_df, self.corrections
    
    def _check_violations(self, o: float, h: float, l: float, c: float) -> List[str]:
        """
        Check for OHLC relationship violations.
        
        Parameters
        ----------
        o, h, l, c : float
            Open, High, Low, Close prices
        
        Returns
        -------
        List[str]
            List of violation types found
        """
        violations = []
        
        if h < c:
            violations.append('high_lt_close')
        
        if c < l:
            violations.append('close_lt_low')
        
        if l < o:
            violations.append('low_lt_open')
        
        if h < o:
            violations.append('high_lt_open')
        
        if h < l:
            violations.append('high_lt_low')
        
        return violations
    
    def _fix_via_interpolation(
        self,
        o: float,
        h: float,
        l: float,
        c: float
    ) -> Dict[str, float]:
        """
        Fix OHLC violations using linear interpolation.
        
        Strategy: Use weighted average of Open and Close as central price,
        then adjust High/Low to maintain valid relationships.
        
        Parameters
        ----------
        o, h, l, c : float
            Original Open, High, Low, Close
        
        Returns
        -------
        Dict[str, float]
            Corrected {'Open', 'High', 'Low', 'Close'} values
        """
        # Weighted average: 25% Open, 75% Close
        center_price = 0.25 * o + 0.75 * c
        
        # Use original High/Low as guidance, but enforce constraints
        # High should be >= max(Open, Close) and >= center
        new_high = max(h, o, c, center_price)
        
        # Low should be <= min(Open, Close) and <= center
        new_low = min(l, o, c, center_price)
        
        # Ensure Low <= Open <= Close <= High (or variant)
        # Relax to ensure consistency
        all_prices = sorted([o, center_price, c])
        
        return {
            'Open': all_prices[0],
            'High': max(all_prices),
            'Low': min(all_prices),
            'Close': all_prices[-1]
        }
    
    def validate_corrections(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that corrected DataFrame has no remaining violations.
        
        Parameters
        ----------
        df : pd.DataFrame
            Corrected DataFrame
        
        Returns
        -------
        Tuple[bool, List[str]]
            (all_valid, list_of_remaining_violations)
        """
        errors = []
        
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            return False, ["Missing required OHLC columns"]
        
        for date, row in df.iterrows():
            o, h, l, c = row['Open'], row['High'], row['Low'], row['Close']
            
            # Skip NaN
            if pd.isna([o, h, l, c]).any():
                continue
            
            violations = self._check_violations(o, h, l, c)
            if violations:
                errors.append(f"{date}: {violations}")
        
        return len(errors) == 0, errors


class SpikeCorrector:
    """
    Corrects price spikes via verification or removal/interpolation.
    
    Behavior:
    - For detected spikes: attempts multi-source verification (if available)
    - If spike confirmed by ≥3 sources: accepts as legitimate
    - Otherwise: removes or interpolates spike via linear interpolation
    - Logs spike action with date, return %, and reason
    
    Examples
    --------
    >>> corrector = SpikeCorrector()
    >>> corrected_df, corrections = corrector.correct_spikes(df, detected_spikes)
    """
    
    def __init__(
        self,
        fix_method: str = 'interpolation',
        logger: logging.Logger = None
    ):
        """
        Initialize SpikeCorrector.
        
        Parameters
        ----------
        fix_method : str
            Method for fixing spikes: 'removal' or 'interpolation' (default: 'interpolation')
        logger : logging.Logger, optional
            Logger instance
        """
        self.fix_method = fix_method
        self.logger = logger or logging.getLogger(__name__)
        self.corrections: List[SpikeCorrectionRecord] = []
    
    def correct_spikes(
        self,
        df: pd.DataFrame,
        detected_spikes: List[Any]
    ) -> Tuple[pd.DataFrame, List[SpikeCorrectionRecord]]:
        """
        Correct or validate detected price spikes.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        detected_spikes : List[Any]
            List of detected spike objects (with date, daily_return, etc.)
        
        Returns
        -------
        Tuple[pd.DataFrame, List[SpikeCorrectionRecord]]
            (corrected_df, list_of_spike_corrections)
        """
        self.corrections = []
        corrected_df = df.copy()
        
        if 'Close' not in corrected_df.columns:
            self.logger.warning("Close column not found")
            return corrected_df, self.corrections
        
        rows_to_remove = []
        
        for spike in detected_spikes:
            spike_date = spike.date
            spike_return = spike.daily_return
            
            if spike_date not in corrected_df.index:
                self.logger.warning(f"Spike date {spike_date} not in DataFrame")
                continue
            
            # Attempt multi-source verification (placeholder - would check other data sources)
            confirmed_sources = self._verify_spike_from_sources(spike, df)
            
            if confirmed_sources >= 3:
                # Accept spike as legitimate
                action = 'accepted'
                reason = f"Confirmed by {confirmed_sources} sources"
                
                self.corrections.append(
                    SpikeCorrectionRecord(
                        date=spike_date,
                        daily_return=spike_return,
                        previous_close=spike.previous_close,
                        current_value=spike.current_value,
                        action=action,
                        reason=reason
                    )
                )
                
                self.logger.info(
                    f"Spike on {spike_date} (return: {spike_return:.2%}) "
                    f"accepted: {reason}"
                )
            else:
                # Reject spike - remove or interpolate
                if self.fix_method == 'removal':
                    rows_to_remove.append(spike_date)
                    action = 'removed'
                else:
                    # Interpolate
                    corrected_df = self._interpolate_spike(
                        corrected_df, spike_date
                    )
                    action = 'interpolated'
                
                reason = f"Confirmed by only {confirmed_sources} sources (threshold: 3)"
                
                self.corrections.append(
                    SpikeCorrectionRecord(
                        date=spike_date,
                        daily_return=spike_return,
                        previous_close=spike.previous_close,
                        current_value=spike.current_value,
                        action=action,
                        reason=reason
                    )
                )
                
                self.logger.info(
                    f"Spike on {spike_date} (return: {spike_return:.2%}) "
                    f"{action}: {reason}"
                )
        
        # Remove rejected spikes
        if rows_to_remove:
            corrected_df = corrected_df.drop(rows_to_remove)
        
        self.logger.info(
            f"Spike correction complete: "
            f"{len(self.corrections)} spikes processed"
        )
        
        return corrected_df, self.corrections
    
    def _verify_spike_from_sources(self, spike: Any, df: pd.DataFrame) -> int:
        """
        Attempt to verify spike from multiple sources.
        
        This is a placeholder implementation that scores verification based on
        available data. In a full implementation, would check against:
        - Market-wide events (e.g., earnings announcements)
        - News feed data
        - SEC filings
        - Other data providers (yfinance, Alpha Vantage, etc.)
        
        Parameters
        ----------
        spike : Any
            Spike object with date and return information
        df : pd.DataFrame
            OHLCV DataFrame
        
        Returns
        -------
        int
            Number of confirming sources (0-3+)
        """
        # Base implementation: check if spike is within reasonable bounds
        confirmed = 0
        
        # Source 1: OHLC consistency
        # If High-Low spread is large enough, spike might be real
        if spike.date in df.index:
            row = df.loc[spike.date]
            if 'High' in row and 'Low' in row:
                spread = (row['High'] - row['Low']) / row['Low'] if row['Low'] != 0 else 0
                if spread > abs(spike.daily_return) * 0.5:
                    confirmed += 1
        
        # Source 2: Volume confirmation
        # Large volume might indicate real market movement
        if spike.date in df.index:
            row = df.loc[spike.date]
            if 'Volume' in row and len(df) > 20:
                vol_ma = df['Volume'].rolling(20).mean()
                if spike.date in vol_ma.index:
                    vol_ratio = row['Volume'] / vol_ma[spike.date] if vol_ma[spike.date] != 0 else 0
                    if vol_ratio > 1.5:
                        confirmed += 1
        
        # Source 3: Magnitude check
        # Very large moves are more likely to be real events
        if abs(spike.daily_return) > 0.3:  # 30%+
            confirmed += 1
        
        return confirmed
    
    def _interpolate_spike(
        self,
        df: pd.DataFrame,
        spike_date: pd.Timestamp
    ) -> pd.DataFrame:
        """
        Interpolate spike via linear interpolation.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with spike
        spike_date : pd.Timestamp
            Date of spike to interpolate
        
        Returns
        -------
        pd.DataFrame
            DataFrame with interpolated spike
        """
        df_corrected = df.copy()
        
        if spike_date not in df_corrected.index:
            return df_corrected
        
        idx = df_corrected.index.get_loc(spike_date)
        
        # Get surrounding prices
        if idx > 0 and idx < len(df_corrected) - 1:
            prev_close = df_corrected.iloc[idx - 1]['Close']
            next_close = df_corrected.iloc[idx + 1]['Close']
            
            # Linear interpolation
            interpolated_close = (prev_close + next_close) / 2
            
            # Update OHLC
            df_corrected.iloc[idx, df_corrected.columns.get_loc('Close')] = interpolated_close
            
            # Adjust High/Low to be consistent with interpolated Close
            if 'High' in df_corrected.columns:
                df_corrected.iloc[idx, df_corrected.columns.get_loc('High')] = max(
                    df_corrected.iloc[idx]['High'],
                    interpolated_close
                )
            
            if 'Low' in df_corrected.columns:
                df_corrected.iloc[idx, df_corrected.columns.get_loc('Low')] = min(
                    df_corrected.iloc[idx]['Low'],
                    interpolated_close
                )
        
        return df_corrected
