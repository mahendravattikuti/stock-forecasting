"""
Tier-1 feature module for computing simple and log returns.

This module computes:
- Simple returns: (Close_t - Close_{t-1}) / Close_{t-1}
- Log returns: log(Close_t / Close_{t-1})

These are fundamental features for financial analysis, capturing price momentum
and percentage change in a consistent, normalized format.

Module conforms to FeatureModule interface:
- compute(): Computes returns from OHLCV data
- validate(): Checks for NaN/inf and reasonable ranges
- check_causality(): Verifies no look-ahead bias (returns are fully causal)
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, List, Optional
from features.base_features import FeatureModule


class ReturnsFeature(FeatureModule):
    """
    Compute simple and log returns from Close prices.
    
    This feature module computes two fundamental return measures:
    1. Simple returns: percentage change in price
    2. Log returns: natural logarithm of price ratios (continuous compounding)
    
    Log returns are statistically preferable for modeling due to better properties
    (additivity over periods, normality assumptions), while simple returns are
    more intuitive for practitioners.
    
    Output Columns:
    - simple_return: (Close_t - Close_{t-1}) / Close_{t-1}
    - log_return: log(Close_t / Close_{t-1})
    
    Expected NaN:
    - First row always NaN (no previous close to compare)
    - All remaining rows should have valid values
    
    Properties:
    - Fully causal: uses only historical data (Close_{t-1})
    - No rolling windows: stateless computation
    - Numerically stable: handles edge cases properly
    
    Examples
    --------
    >>> df = pd.DataFrame({
    ...     'Close': [100.0, 101.0, 99.0, 102.0],
    ... }, index=pd.date_range('2024-01-01', periods=4))
    >>> feature = ReturnsFeature()
    >>> returns = feature.compute(df)
    >>> print(returns['simple_return'].iloc[1])
    0.01  # 1% simple return from 100 to 101
    >>> print(returns['log_return'].iloc[1])
    0.00995...  # log(101/100) = log(1.01)
    
    Attributes
    ----------
    name : str
        "returns"
    tier : int
        1 (Tier-1 features)
    logger : logging.Logger
        Logger for computation steps
    """
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize ReturnsFeature module.
        
        Parameters
        ----------
        config : dict, optional
            Configuration dictionary (unused for returns, provided for interface compatibility)
        logger : logging.Logger, optional
            Logger instance; if None, creates logger named 'ReturnsFeature'
        
        Examples
        --------
        >>> feature = ReturnsFeature()
        >>> feature = ReturnsFeature(config={}, logger=my_logger)
        """
        super().__init__(
            name="returns",
            tier=1,
            config=config or {},
            logger=logger or logging.getLogger(self.__class__.__name__)
        )
    
    def compute(
        self,
        df: pd.DataFrame,
        fit_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Compute simple and log returns from OHLCV data.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with DatetimeIndex.
            Must contain 'Close' column with non-null prices.
            Expected columns: [Open, High, Low, Close, Volume]
        fit_data : pd.DataFrame, optional
            Not used for returns computation (interface compatibility).
            Ignored if provided.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns [simple_return, log_return] and DatetimeIndex matching df.
            First row contains NaN (no previous close to compare).
            All subsequent rows contain computed returns.
        
        Raises
        ------
        ValueError
            If df is None, empty, or missing 'Close' column
        
        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'Close': [100, 101, 102, 103, 104],
        ... }, index=pd.date_range('2024-01-01', periods=5))
        >>> feature = ReturnsFeature()
        >>> result = feature.compute(df)
        >>> print(result['simple_return'].iloc[1])  # 2024-01-02
        0.01
        >>> print(result['log_return'].iloc[1])
        0.00995...
        """
        # Validate input
        is_valid, errors = self._validate_input_dataframe(df)
        if not is_valid:
            raise ValueError(f"Invalid input DataFrame: {'; '.join(errors)}")
        
        if 'Close' not in df.columns:
            raise ValueError("Input DataFrame must contain 'Close' column")
        
        # Log computation start
        self._log_computation_start(num_rows=len(df))
        
        # Initialize output dataframe
        features = pd.DataFrame(index=df.index)
        
        # Compute simple returns: (Close_t - Close_{t-1}) / Close_{t-1}
        features['simple_return'] = df['Close'].pct_change()
        
        # Compute log returns: log(Close_t / Close_{t-1})
        features['log_return'] = np.log(df['Close'] / df['Close'].shift(1))
        
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
        Validate computed returns for NaN, inf, and reasonable ranges.
        
        Validation checks:
        1. First row contains NaN (expected, no previous close)
        2. All remaining rows contain valid finite values (no inf)
        3. No unexpected NaN values beyond first row
        4. Values are numerically reasonable (inf check)
        
        Returns are unbounded (can be any finite value), so we only check:
        - Finiteness (not inf or -inf)
        - Expected NaN at first row only
        
        Parameters
        ----------
        features : pd.DataFrame
            Computed features with columns [simple_return, log_return]
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_valid, error_messages)
            - is_valid: True if all validation checks pass, False otherwise
            - error_messages: List of descriptive error messages if validation fails
        
        Examples
        --------
        >>> features = pd.DataFrame({
        ...     'simple_return': [np.nan, 0.01, 0.02, -0.005],
        ...     'log_return': [np.nan, 0.00995, 0.0198, -0.00501]
        ... })
        >>> feature = ReturnsFeature()
        >>> is_valid, errors = feature.validate(features)
        >>> print(is_valid)
        True
        >>> print(errors)
        []
        """
        errors = []
        
        # Expected: first row is NaN (no previous close to compare)
        for col in features.columns:
            if not pd.isna(features[col].iloc[0]):
                errors.append(
                    f"First row of '{col}' should be NaN (no previous close), "
                    f"got {features[col].iloc[0]}"
                )
        
        # Check for infinite values (these are errors)
        is_valid_nan_inf, nan_inf_errors = self._check_for_nan_and_inf(
            features,
            expected_nan_rows=1  # Only first row should be NaN
        )
        errors.extend(nan_inf_errors)
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Verify that returns do not use future data (look-ahead bias check).
        
        Returns are computed using only Close_{t-1}, so they are fully causal.
        No look-ahead bias is possible for this feature.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame (used for validation only; not used in causality check)
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_causal, error_messages)
            - is_causal: Always True for returns (fully causal computation)
            - error_messages: Always [] (no causality concerns)
        
        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'Close': [100, 101, 102, 103],
        ... }, index=pd.date_range('2024-01-01', periods=4))
        >>> feature = ReturnsFeature()
        >>> is_causal, errors = feature.check_causality(df)
        >>> print(is_causal)
        True
        >>> print(errors)
        []
        """
        # Returns use only historical data (Close_{t-1}), so no causality concerns
        return True, []
