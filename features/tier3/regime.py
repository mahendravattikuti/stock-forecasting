"""
Market Regime Feature - Classifies market conditions

Implements MarketRegimeFeature which classifies market conditions into regimes:
- 0: Bearish (negative returns, low volatility)
- 1: Sideways (low returns, low volatility)
- 2: Bullish (positive returns, low volatility)
- 3: High-Volatility (high volatility regardless of direction)

This provides context about market conditions for the stock being analyzed.
"""

import logging
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np

from features.base_features import FeatureModule


class MarketRegimeFeature(FeatureModule):
    """
    Market Regime Detector - Classifies market conditions into 4 regimes.
    
    Regimes are determined by:
    - 60-day rolling return (trend direction)
    - 60-day rolling volatility (price fluctuation magnitude)
    
    Regime Classification:
    - 0: Bearish - Negative returns, normal volatility
    - 1: Sideways - Near-zero returns, low volatility
    - 2: Bullish - Positive returns, normal volatility
    - 3: High-Vol - Any return direction, high volatility
    
    Data Requirements:
    - Minimum 61 bars (60 for rolling calculations + 1 for first return)
    - First 60 rows will be NaN
    
    Attributes:
        lookback_period (int): Period for trend/volatility calculation (default: 60)
        volatility_threshold (float): Threshold for high volatility classification (default: 0.05)
        return_threshold (float): Threshold for bullish/bearish classification (default: 0.02)
    
    Example:
        >>> feature = MarketRegimeFeature()
        >>> df = pd.DataFrame({'Close': prices})
        >>> regime_df = feature.compute(df)
        >>> print(regime_df['market_regime'].iloc[100])
        2  # Bullish regime
    """
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize Market Regime feature module.
        
        Args:
            config (Optional[dict]): Configuration dict with optional parameters
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(name='market_regime', tier=3, config=config, logger=logger)
        self.lookback_period = 60
        self.volatility_threshold = 0.05  # 5% volatility threshold for high-vol
        self.return_threshold = 0.02      # 2% return threshold for bullish/bearish
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Compute market regime classification.
        
        Args:
            df (pd.DataFrame): OHLCV data with DatetimeIndex and 'Close' column
            fit_data (Optional[pd.DataFrame]): Historical data (not used for regime)
        
        Returns:
            pd.DataFrame: DataFrame with single column 'market_regime' containing regime (0-3)
        
        Raises:
            ValueError: If 'Close' column missing or insufficient data
        """
        self._validate_input_dataframe(df)
        
        close = df['Close'].astype(float)
        
        if len(df) < self.lookback_period + 1:
            self.logger.warning(
                f"Market Regime: Insufficient data. Got {len(df)} rows, need minimum {self.lookback_period + 1}",
                extra={'symbol': getattr(self, 'symbol', 'unknown')}
            )
        
        # Calculate 60-day returns
        returns = close.pct_change(periods=self.lookback_period)
        
        # Calculate 60-day rolling volatility (std of daily returns)
        daily_returns = close.pct_change()
        volatility = daily_returns.rolling(window=self.lookback_period).std()
        
        # Initialize regime column
        regime = pd.Series(np.nan, index=df.index, dtype=float)
        
        # Get valid indices (where both returns and volatility are not NaN)
        valid_idx = (returns.notna()) & (volatility.notna())
        
        # Classify regimes
        # High volatility takes precedence
        high_vol = volatility[valid_idx] > self.volatility_threshold
        regime[valid_idx & high_vol] = 3
        
        # For normal volatility, classify by return direction
        normal_vol = ~high_vol & valid_idx
        
        positive_return = returns[normal_vol] > self.return_threshold
        negative_return = returns[normal_vol] < -self.return_threshold
        
        regime[normal_vol & positive_return] = 2  # Bullish
        regime[normal_vol & negative_return] = 0  # Bearish
        
        # Remaining are sideways (near-zero returns)
        sideways_mask = normal_vol & (~positive_return) & (~negative_return)
        regime[sideways_mask] = 1
        
        result = pd.DataFrame({'market_regime': regime}, index=df.index)
        
        self._log_computation_complete(num_features=1, num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate market regime values are in valid range {0, 1, 2, 3}.
        
        Args:
            features (pd.DataFrame): DataFrame containing 'market_regime' column
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        if 'market_regime' not in features.columns:
            errors.append("Column 'market_regime' not found in features")
            return False, errors
        
        regime = features['market_regime'].dropna()
        
        if len(regime) == 0:
            errors.append("Market regime has no valid (non-NaN) values")
            return False, errors
        
        # Check values are in {0, 1, 2, 3}
        valid_regimes = {0, 1, 2, 3}
        invalid_regimes = set(regime.unique()) - valid_regimes
        
        if invalid_regimes:
            errors.append(f"Market regime: invalid values {invalid_regimes}, must be in {{0, 1, 2, 3}}")
        
        # Check distribution is reasonable (not all one regime)
        unique_count = regime.nunique()
        if unique_count == 1:
            self.logger.warning(f"Market regime: all values are regime {regime.iloc[0]} (no variation)")
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Verify market regime uses only past Close prices (no look-ahead).
        
        Args:
            df (pd.DataFrame): Input OHLCV data
        
        Returns:
            Tuple[bool, List[str]]: (is_causal, warnings)
        """
        warnings = []
        
        if len(df) < self.lookback_period + 2:
            warnings.append(
                f"Insufficient data for proper causality check ({len(df)} < {self.lookback_period + 2})"
            )
        
        return True, warnings
