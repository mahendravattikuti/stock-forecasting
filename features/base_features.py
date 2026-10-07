"""
Abstract base class for all feature modules.

Defines the interface that all feature computation modules must implement,
including compute(), validate(), and check_causality() methods.

Each feature module handles a specific feature or feature group (e.g., returns,
RSI, market regime) and is responsible for:
- Computing features from OHLCV data
- Validating computed features for NaN/inf/leakage
- Verifying no look-ahead bias in rolling calculations
- Logging all operations
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import logging
from typing import Tuple, List, Optional, Dict, Any


class FeatureModule(ABC):
    """
    Abstract base class for all feature modules.
    
    Defines the interface that all feature computation modules must implement.
    Each subclass is responsible for computing one or more features from OHLCV data,
    validating computed features, and ensuring no data leakage or look-ahead bias.
    
    Attributes
    ----------
    name : str
        Unique identifier for the feature module
    tier : int
        Feature tier: 1 (Tier-1), 2 (Tier-2), 3 (Tier-3), 4 (Signal Processing)
    config : dict
        Configuration parameters specific to this module
    logger : logging.Logger
        Logger instance for this module
    
    Examples
    --------
    Create a simple feature module that computes returns:
    
    >>> class ReturnsFeature(FeatureModule):
    ...     def __init__(self):
    ...         super().__init__("returns", tier=1, config={})
    ...
    ...     def compute(self, df, fit_data=None):
    ...         features = pd.DataFrame(index=df.index)
    ...         features['simple_return'] = df['Close'].pct_change()
    ...         return features
    ...
    ...     def validate(self, features):
    ...         if features.isna().any().any():
    ...             return False, ["Contains unexpected NaN values"]
    ...         return True, []
    
    >>> feature = ReturnsFeature()
    >>> result, errors = feature.validate(computed_features)
    """
    
    def __init__(
        self,
        name: str,
        tier: int,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize FeatureModule.
        
        Parameters
        ----------
        name : str
            Unique identifier for the feature module (e.g., 'returns', 'rsi', 'regime')
        tier : int
            Feature tier classification: 1=Tier-1, 2=Tier-2, 3=Tier-3, 4=Signal Processing
        config : dict, optional
            Configuration dictionary with module-specific parameters
        logger : logging.Logger, optional
            Logger instance; if None, creates logger named after module class
        
        Examples
        --------
        >>> module = SomeFeatureModule(
        ...     name="my_feature",
        ...     tier=2,
        ...     config={"lookback": 20, "threshold": 0.05}
        ... )
        """
        self.name = name
        self.tier = tier
        self.config = config or {}
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Initialized {self.__class__.__name__} (name={name}, tier={tier})")
    
    @abstractmethod
    def compute(
        self,
        df: pd.DataFrame,
        fit_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Compute feature(s) from input DataFrame.
        
        This is the main method that computes the feature(s) based on OHLCV data.
        Implementations should:
        - Use only historical data (no look-ahead)
        - Handle first N rows that may be NaN due to rolling window
        - Return DataFrame with clean column names
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with DatetimeIndex. Must contain columns:
            [Open, High, Low, Close, Volume]
        fit_data : pd.DataFrame, optional
            Data to fit parameters on (e.g., training data for scaler fitting).
            For modules that need fit parameters (e.g., RSI smoothing), use fit_data
            if provided, otherwise fit on df. Ensures no data leakage.
        
        Returns
        -------
        pd.DataFrame
            Computed features with DatetimeIndex matching df.
            Columns should have descriptive names (e.g., 'simple_return', 'rsi_14').
            First N rows may be NaN if computation requires lookback window.
        
        Raises
        ------
        ValueError
            If df is missing required columns or is empty
        
        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'Close': [100, 101, 102, 103, 104],
        ... }, index=pd.date_range('2020-01-01', periods=5))
        >>> feature = ReturnsFeature()
        >>> result = feature.compute(df)
        >>> print(result['simple_return'])
        2020-01-01         NaN
        2020-01-02    0.010000
        2020-01-03    0.009901
        2020-01-04    0.009804
        2020-01-05    0.009709
        """
        pass
    
    @abstractmethod
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate computed features for quality and integrity.
        
        Checks:
        - No unexpected NaN values (except initial rows from lookback)
        - No infinite values
        - No out-of-range values (e.g., RSI outside [0, 100])
        - Proper data types
        
        Parameters
        ----------
        features : pd.DataFrame
            Computed features to validate, with DatetimeIndex
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_valid, error_messages) where:
            - is_valid: True if all checks pass, False otherwise
            - error_messages: List of error descriptions if validation fails
        
        Examples
        --------
        >>> features = pd.DataFrame({
        ...     'rsi': [np.nan] * 14 + [30.5, 35.2, 40.1, ...],
        ... }, index=pd.date_range('2020-01-01', periods=20))
        >>> rsi_feature = RSIFeature()
        >>> is_valid, errors = rsi_feature.validate(features)
        >>> print(is_valid)
        True
        >>> print(errors)
        []
        
        >>> features_bad = pd.DataFrame({
        ...     'rsi': [np.nan] * 14 + [30.5, 105.0, 40.1, ...],  # 105 > 100!
        ... }, index=pd.date_range('2020-01-01', periods=20))
        >>> is_valid, errors = rsi_feature.validate(features_bad)
        >>> print(is_valid)
        False
        >>> print(errors)
        ['RSI values outside [0, 100] range']
        """
        pass
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Verify that features do not use future data (look-ahead bias check).
        
        Base implementation returns (True, []) - no causality issues.
        Override in subclasses where look-ahead bias is possible (e.g., rolling windows).
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame that was used to compute features
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_causal, error_messages) where:
            - is_causal: True if no look-ahead bias detected, False otherwise
            - error_messages: List of causality violation descriptions
        
        Examples
        --------
        >>> df = pd.DataFrame({
        ...     'Close': [100, 101, 102, 103, 104],
        ... }, index=pd.date_range('2020-01-01', periods=5))
        >>> feature = ReturnsFeature()
        >>> is_causal, errors = feature.check_causality(df)
        >>> print(is_causal)
        True
        >>> print(errors)
        []
        """
        # Default: no causality concerns
        return True, []
    
    def _validate_input_dataframe(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that input DataFrame has required structure.
        
        Checks:
        - DataFrame is not empty
        - Index is DatetimeIndex
        - Required columns present (checked by subclass)
        
        Parameters
        ----------
        df : pd.DataFrame
            Input OHLCV DataFrame to validate
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_valid, error_messages)
        """
        errors = []
        
        if df is None or len(df) == 0:
            errors.append("Input DataFrame is empty or None")
            return False, errors
        
        if not isinstance(df.index, pd.DatetimeIndex):
            errors.append(f"DataFrame index must be DatetimeIndex, got {type(df.index)}")
        
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        return len(errors) == 0, errors
    
    def _check_for_nan_and_inf(
        self,
        features: pd.DataFrame,
        expected_nan_rows: int = 0
    ) -> Tuple[bool, List[str]]:
        """
        Check for unexpected NaN and infinite values in computed features.
        
        Parameters
        ----------
        features : pd.DataFrame
            Computed features to check
        expected_nan_rows : int
            Expected number of leading NaN rows (e.g., from lookback window).
            If a feature has more NaN values than this, it's flagged as error.
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_valid, error_messages)
        
        Examples
        --------
        >>> features = pd.DataFrame({
        ...     'feature1': [np.nan] * 20 + [1.0, 2.0, 3.0],
        ...     'feature2': [1.0, 2.0, 3.0, ...],  # No NaN
        ... })
        >>> is_valid, errors = module._check_for_nan_and_inf(features, expected_nan_rows=20)
        >>> print(is_valid)
        True  # feature1 has exactly 20 NaN rows at start (expected)
        """
        errors = []
        
        for col in features.columns:
            # Count NaN values
            nan_count = features[col].isna().sum()
            
            # Count inf values
            inf_count = np.isinf(features[col]).sum()
            
            if inf_count > 0:
                errors.append(
                    f"Column '{col}' contains {inf_count} infinite values"
                )
            
            # Check NaN only beyond expected rows
            if nan_count > expected_nan_rows:
                unexpected_nans = nan_count - expected_nan_rows
                errors.append(
                    f"Column '{col}' contains {unexpected_nans} unexpected NaN values "
                    f"(beyond expected {expected_nan_rows} rows)"
                )
        
        return len(errors) == 0, errors
    
    def _log_computation_start(self, symbol: str = None, num_rows: int = None) -> None:
        """
        Log the start of feature computation.
        
        Parameters
        ----------
        symbol : str, optional
            Stock symbol being processed
        num_rows : int, optional
            Number of rows in input data
        """
        msg = f"{self.name}: Computing features"
        if symbol:
            msg += f" for {symbol}"
        if num_rows:
            msg += f" ({num_rows} rows)"
        self.logger.info(msg)
    
    def _log_computation_complete(
        self,
        num_features: int = None,
        num_rows: int = None,
        nan_count: int = None
    ) -> None:
        """
        Log the completion of feature computation.
        
        Parameters
        ----------
        num_features : int, optional
            Number of features computed
        num_rows : int, optional
            Number of rows in output
        nan_count : int, optional
            Total NaN values in output
        """
        msg = f"{self.name}: Computation complete"
        if num_features:
            msg += f" ({num_features} features)"
        if num_rows:
            msg += f" ({num_rows} rows)"
        if nan_count is not None:
            msg += f", {nan_count} NaN values"
        self.logger.debug(msg)
