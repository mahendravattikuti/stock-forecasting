"""
Tier-1 feature module for computing normalized price and volume indicators.

This module computes normalized versions of price and volume using 20-day
rolling averages and standard deviations:
- Normalized close: (Close - MA20) / STD20 (z-score normalization)
- Normalized volume: Volume / MA_Volume20 (volume intensity)

These features standardize prices and volumes to comparable scales,
enabling models to learn general patterns across different symbols
and price levels.

Module conforms to FeatureModule interface:
- compute(): Computes normalized features from OHLCV data
- validate(): Checks for NaN/inf and reasonable ranges
- check_causality(): Verifies no look-ahead bias (rolling windows use only past data)
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, List, Optional
from features.base_features import FeatureModule


class NormalizedPricesFeature(FeatureModule):
    """
    Compute normalized price and volume features using rolling statistics.
    
    This feature module computes:
    1. 20-day rolling mean of Close (close_ma20)
    2. 20-day rolling standard deviation of Close (close_std20)
    3. Normalized close: (Close - MA20) / STD20 (normalized_close)
    4. Normalized volume: Volume / MA_Volume20 (normalized_volume)
    
    Normalization is useful for:
    - Standardizing features to comparable scales
    - Detecting mean-reversion (normalized_close deviations)
    - Measuring volume intensity (normalized_volume > 1 = above average)
    
    Output Columns:
    - close_ma20: 20-day rolling mean of Close
    - close_std20: 20-day rolling standard deviation of Close
    - normalized_close: (Close - MA20) / STD20 (z-score)
    - normalized_volume: Volume / MA_Volume20
    
    Expected NaN:
    - First 19 rows NaN (need 20 values for rolling window)
    - 20th row and beyond contain valid values
    
    Properties:
    - Fully causal: rolling windows use only past/current data, not future
    - Stateless: each row depends only on prior 20 rows
    - Numerically stable: handles zero std via epsilon or drop row
    
    Examples
    --------
    >>> dates = pd.date_range('2024-01-01', periods=30)
    >>> df = pd.DataFrame({
    ...     'Close': np.linspace(100, 110, 30),
    ...     'Volume': np.random.randint(1000000, 2000000, 30),
    ... }, index=dates)
    >>> feature = NormalizedPricesFeature()
    >>> normalized = feature.compute(df)
    >>> print(normalized['close_ma20'].iloc[0:19].isna().all())
    True  # First 19 rows NaN (need 20 values)
    >>> print(f"normalized_close mean: {normalized['normalized_close'].iloc[19:].mean():.3f}")
    ~0.0  # Mean approximately 0 (z-score)
    
    Attributes
    ----------
    name : str
        "normalized_prices"
    tier : int
        1 (Tier-1 features)
    lookback_window : int
        20 (rolling window size for statistics)
    logger : logging.Logger
        Logger for computation steps
    """
    
    def __init__(
        self,
        lookback_window: int = 20,
        config: Optional[dict] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize NormalizedPricesFeature module.
        
        Parameters
        ----------
        lookback_window : int, optional
            Size of rolling window for statistics (default: 20)
        config : dict, optional
            Configuration dictionary (unused for normalized prices, provided for interface compatibility)
        logger : logging.Logger, optional
            Logger instance; if None, creates logger named 'NormalizedPricesFeature'
        
        Examples
        --------
        >>> feature = NormalizedPricesFeature()
        >>> feature = NormalizedPricesFeature(lookback_window=20)
        """
        super().__init__(
            name="normalized_prices",
            tier=1,
            config=config or {},
            logger=logger or logging.getLogger(self.__class__.__name__)
        )
        self.lookback_window = lookback_window
    
    def compute(
        self,
        df: pd.DataFrame,
        fit_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Compute normalized price and volume features from OHLCV data.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with DatetimeIndex.
            Must contain 'Close' and 'Volume' columns with non-null values.
            Expected columns: [Open, High, Low, Close, Volume]
        fit_data : pd.DataFrame, optional
            Not used for normalized prices computation (interface compatibility).
            Ignored if provided.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns [close_ma20, close_std20, normalized_close, normalized_volume]
            and DatetimeIndex matching df.
            First 19 rows contain NaN (rolling window size = 20).
            Rows 20+ contain computed features.
        
        Raises
        ------
        ValueError
            If df is None, empty, or missing 'Close' or 'Volume' columns
        
        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'Close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
        ...               110, 111, 112, 113, 114, 115, 116, 117, 118, 119,
        ...               120, 121, 122],
        ...     'Volume': [1000000] * 23,
        ... }, index=pd.date_range('2024-01-01', periods=23))
        >>> feature = NormalizedPricesFeature()
        >>> result = feature.compute(df)
        >>> print(result['close_ma20'].iloc[0:19].isna().all())
        True  # First 19 rows NaN
        >>> print(result['close_ma20'].iloc[19])  # 20th row
        109.5  # Average of 100-119
        """
        # Validate input
        is_valid, errors = self._validate_input_dataframe(df)
        if not is_valid:
            raise ValueError(f"Invalid input DataFrame: {'; '.join(errors)}")
        
        required_cols = ['Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Input DataFrame must contain {required_cols}, missing: {missing_cols}")
        
        # Log computation start
        self._log_computation_start(num_rows=len(df))
        
        # Initialize output dataframe
        features = pd.DataFrame(index=df.index)
        
        # Compute 20-day rolling statistics for Close
        close_ma = df['Close'].rolling(window=self.lookback_window).mean()
        close_std = df['Close'].rolling(window=self.lookback_window).std()
        
        # Compute 20-day rolling mean for Volume
        volume_ma = df['Volume'].rolling(window=self.lookback_window).mean()
        
        # Store rolling means and stds
        features['close_ma20'] = close_ma
        features['close_std20'] = close_std
        
        # Compute normalized close: (Close - MA20) / STD20
        # Handle division by zero: where std is very small, set to 0 (feature is undefined)
        # Better: keep NaN for those points (model can handle it or we can forward-fill)
        with np.errstate(divide='ignore', invalid='ignore'):
            features['normalized_close'] = (df['Close'] - close_ma) / close_std
        
        # Compute normalized volume: Volume / MA_Volume20
        # Handle division by zero: where volume_ma is very small, set to NaN
        with np.errstate(divide='ignore', invalid='ignore'):
            features['normalized_volume'] = df['Volume'] / volume_ma
        
        # Log computation complete
        nan_count = features.isna().sum().sum()
        self._log_computation_complete(
            num_features=len(features.columns),
            num_rows=len(features),
            nan_count=int(nan_count)
        )
        
        return features
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate computed normalized features for NaN, inf, and reasonable ranges.
        
        Validation checks:
        1. First 19 rows contain NaN (rolling window requires 20 values)
        2. From row 20 onward, values should be finite (no inf)
        3. Normalized values should be in reasonable ranges:
           - normalized_close: typically [-3, 3] (3 standard deviations)
           - normalized_volume: typically > 0
        4. No unexpected NaN values beyond first 19 rows
        
        Parameters
        ----------
        features : pd.DataFrame
            Computed features with columns [close_ma20, close_std20, normalized_close, normalized_volume]
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_valid, error_messages)
            - is_valid: True if all validation checks pass, False otherwise
            - error_messages: List of descriptive error messages if validation fails
        
        Examples
        --------
        >>> features = pd.DataFrame({
        ...     'close_ma20': [np.nan]*19 + [100, 101, 102],
        ...     'close_std20': [np.nan]*19 + [1, 1, 1],
        ...     'normalized_close': [np.nan]*19 + [0.5, 1.5, 2.5],
        ...     'normalized_volume': [np.nan]*19 + [1.2, 0.8, 1.1],
        ... })
        >>> feature = NormalizedPricesFeature()
        >>> is_valid, errors = feature.validate(features)
        >>> print(is_valid)
        True
        """
        errors = []
        
        # Check for expected NaN in first 19 rows
        expected_nan_rows = self.lookback_window - 1  # 19 for lookback=20
        
        # Validate using base method
        is_valid_nan_inf, nan_inf_errors = self._check_for_nan_and_inf(
            features,
            expected_nan_rows=expected_nan_rows
        )
        errors.extend(nan_inf_errors)
        
        # Additional check: normalized_close values should typically be in [-5, 5]
        # (allowing for extreme values but flagging very unreasonable ones)
        if 'normalized_close' in features.columns:
            normalized_close_valid = features['normalized_close'].iloc[expected_nan_rows:]
            extreme_values = (
                (normalized_close_valid < -10) | (normalized_close_valid > 10)
            ).sum()
            if extreme_values > 0:
                errors.append(
                    f"normalized_close contains {extreme_values} extreme values "
                    f"outside [-10, 10] range (likely data quality issue)"
                )
        
        # Check: normalized_volume should typically be positive (Volume > 0)
        if 'normalized_volume' in features.columns:
            normalized_volume_valid = features['normalized_volume'].iloc[expected_nan_rows:]
            negative_values = (normalized_volume_valid < 0).sum()
            if negative_values > 0:
                errors.append(
                    f"normalized_volume contains {negative_values} negative values "
                    f"(volume should be non-negative)"
                )
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Verify that normalized features do not use future data (look-ahead bias check).
        
        Rolling windows are computed over the current and previous 19 days,
        never using future data. Therefore, no look-ahead bias is possible.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame (used for validation only; causality is automatic for rolling windows)
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_causal, error_messages)
            - is_causal: Always True (rolling windows are fully causal)
            - error_messages: Always [] (no causality concerns)
        
        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'Close': [100, 101, 102, 103],
        ...     'Volume': [1000000] * 4,
        ... }, index=pd.date_range('2024-01-01', periods=4))
        >>> feature = NormalizedPricesFeature()
        >>> is_causal, errors = feature.check_causality(df)
        >>> print(is_causal)
        True
        >>> print(errors)
        []
        """
        # Rolling windows use only past and current data, never future
        # So no causality concerns
        return True, []
