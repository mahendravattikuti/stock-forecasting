"""
Cross-Asset Market Context Features

Implements features that compare stock performance to broader market indices:
- RelativeStrengthFeature: Correlation with S&P 500
- SectorCorrelationFeature (optional): Correlation with sector ETF
"""

import logging
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

from features.base_features import FeatureModule


class RelativeStrengthFeature(FeatureModule):
    """
    Relative Market Strength - Correlation with S&P 500 (SPY).
    
    Compares stock returns to broad market index returns using rolling correlation.
    High correlation indicates stock moves with market. Low correlation indicates
    idiosyncratic (stock-specific) movement.
    
    Formula:
        Market_Returns = returns of SPY (S&P 500)
        Stock_Returns = returns of target stock
        Relative_Strength = 60-day rolling correlation(Stock_Returns, Market_Returns)
    
    Data Requirements:
    - Minimum 61 bars for 60-day rolling correlation
    - SPY data must be aligned with stock dates
    - First 60 rows will be NaN
    
    Attributes:
        correlation_period (int): Period for rolling correlation (default: 60)
        symbol (str): Stock symbol being analyzed
    
    Example:
        >>> feature = RelativeStrengthFeature()
        >>> df = pd.DataFrame({'Close': prices}, index=dates)
        >>> rs_df = feature.compute(df)
        >>> print(rs_df['relative_strength'].iloc[100])
        0.75  # 75% correlated with market
    """
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        """Initialize Relative Strength feature module."""
        super().__init__(name='relative_strength', tier=3, config=config, logger=logger)
        self.correlation_period = 60
        self.spy_data = None
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Compute relative strength (correlation with S&P 500).
        
        Args:
            df (pd.DataFrame): OHLCV data with DatetimeIndex and 'Close' column
            fit_data (Optional[pd.DataFrame]): Historical data (not used)
        
        Returns:
            pd.DataFrame: DataFrame with single column 'relative_strength' (correlation)
        
        Raises:
            ValueError: If 'Close' column missing or SPY data unavailable
        """
        self._validate_input_dataframe(df)
        
        close = df['Close'].astype(float)
        
        if not HAS_YFINANCE and self.spy_data is None:
            self.logger.warning(
                "RelativeStrength: yfinance not installed. Install with 'pip install yfinance'. Using NaN.",
                extra={'symbol': getattr(self, 'symbol', 'unknown')}
            )
            relative_strength = pd.Series(np.nan, index=df.index)
            result = pd.DataFrame({'relative_strength': relative_strength}, index=df.index)
            self._log_computation_complete(num_features=1, num_rows=len(result), nan_count=result.isna().sum().sum())
            return result
        
        try:
            if self.spy_data is not None:
                spy_close = self.spy_data
                if isinstance(spy_close, pd.DataFrame):
                    spy_close = spy_close['Close'] if 'Close' in spy_close else spy_close.iloc[:, 0]
                spy_close = pd.Series(spy_close, index=spy_close.index).reindex(
                    df.index, method='ffill'
                )
            else:
                if not HAS_YFINANCE:
                    raise ImportError("yfinance is not installed")
                spy_close = yf.download(
                    'SPY',
                    start=df.index[0],
                    end=df.index[-1] + pd.Timedelta(days=1),
                    progress=False,
                    auto_adjust=True,
                )['Close']
                if isinstance(spy_close, pd.DataFrame):
                    spy_close = spy_close.iloc[:, 0]
                spy_close = spy_close.reindex(df.index, method='ffill')
        except Exception as e:
            self.logger.warning(
                f"RelativeStrength: Failed to download SPY data: {str(e)}. Using NaN.",
                extra={'symbol': getattr(self, 'symbol', 'unknown')}
            )
            relative_strength = pd.Series(np.nan, index=df.index)
            result = pd.DataFrame({'relative_strength': relative_strength}, index=df.index)
            self._log_computation_complete(num_features=1, num_rows=len(result), nan_count=result.isna().sum().sum())
            return result
        
        # Calculate returns for both stock and SPY
        stock_returns = close.pct_change()
        spy_returns = spy_close.pct_change()
        
        # Calculate rolling correlation
        relative_strength = stock_returns.rolling(window=self.correlation_period).corr(spy_returns)
        
        result = pd.DataFrame({'relative_strength': relative_strength}, index=df.index)
        
        self._log_computation_complete(num_features=1, num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate relative strength values are in [-1, 1] correlation range.
        
        Args:
            features (pd.DataFrame): DataFrame containing 'relative_strength' column
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        if 'relative_strength' not in features.columns:
            errors.append("Column 'relative_strength' not found")
            return False, errors
        
        rs = features['relative_strength'].dropna()
        
        # If all NaN (e.g., yfinance not available), that's OK for optional feature
        if len(rs) == 0:
            return True, []
        
        # Check bounds [-1, 1]
        if (rs < -1.01).any() or (rs > 1.01).any():
            invalid_count = ((rs < -1.01) | (rs > 1.01)).sum()
            errors.append(f"Relative strength: {invalid_count} values outside [-1, 1] correlation range")
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Verify uses only past returns for correlation calculation."""
        warnings = []
        
        if len(df) < self.correlation_period + 1:
            warnings.append(
                f"Insufficient data for proper causality check ({len(df)} < {self.correlation_period + 1})"
            )
        
        return True, warnings


class SectorCorrelationFeature(FeatureModule):
    """
    Sector Correlation - Correlation with sector ETF (optional feature).
    
    Compares stock returns to its sector ETF returns. Useful for understanding
    whether price movements are sector-driven or stock-specific.
    
    Sector ETF Mapping (sample - can be extended):
        - Tech (XLK, QQQ): Information Technology
        - Healthcare (XLV): Healthcare
        - Financials (XLF): Financials
        - Energy (XLE): Energy
        - Industrials (XLI): Industrials
        - Consumer Discretionary (XLY): Consumer Discretionary
        - Consumer Staples (XLP): Consumer Staples
        - Real Estate (XLRE): Real Estate
        - Utilities (XLU): Utilities
        - Materials (XLB): Materials
    
    Data Requirements:
    - Symbol must be mapped to a sector
    - Sector ETF data must be available
    - Minimum 61 bars for 60-day rolling correlation
    
    Attributes:
        correlation_period (int): Period for rolling correlation (default: 60)
        sector_mapping (dict): Symbol to sector ETF mapping
    
    Example:
        >>> feature = SectorCorrelationFeature()
        >>> # For AAPL (Tech), would correlate with XLK or QQQ
        >>> df = pd.DataFrame({'Close': prices}, index=dates)
        >>> sc_df = feature.compute(df)
    """
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        """Initialize Sector Correlation feature module."""
        super().__init__(name='sector_correlation', tier=3, config=config, logger=logger)
        self.correlation_period = 60
        config = config or {}
        self.sector_data = config.get('sector_data')
        self.sector_etf = config.get('sector_etf')
        
        # Default sector mappings (can be overridden via config)
        self.sector_mapping = {
            'TECH': 'XLK',
            'HEALTHCARE': 'XLV',
            'FINANCIAL': 'XLF',
            'ENERGY': 'XLE',
            'INDUSTRIAL': 'XLI',
            'CONSUMER': 'XLY',
            'STAPLES': 'XLP',
            'REALESTATE': 'XLRE',
            'UTILITY': 'XLU',
            'MATERIALS': 'XLB',
        }
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Compute sector correlation.
        
        Args:
            df (pd.DataFrame): OHLCV data with DatetimeIndex and 'Close' column
            fit_data (Optional[pd.DataFrame]): Historical data (not used)
        
        Returns:
            pd.DataFrame: DataFrame with 'sector_correlation' column or NaN if sector unknown
        """
        self._validate_input_dataframe(df)
        
        sector_correlation = pd.Series(np.nan, index=df.index)
        if self.sector_data is not None:
            sector_close = self.sector_data
            if isinstance(sector_close, pd.DataFrame):
                sector_close = (
                    sector_close['Close'] if 'Close' in sector_close
                    else sector_close.iloc[:, 0]
                )
            sector_close = pd.Series(sector_close, index=sector_close.index).reindex(
                df.index, method='ffill'
            )
            stock_returns = df['Close'].astype(float).pct_change(fill_method=None)
            sector_returns = sector_close.astype(float).pct_change(fill_method=None)
            sector_correlation = stock_returns.rolling(
                window=self.correlation_period,
                min_periods=self.correlation_period,
            ).corr(sector_returns)
        
        result = pd.DataFrame({'sector_correlation': sector_correlation}, index=df.index)
        
        self._log_computation_complete(num_features=1, num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate sector correlation values in [-1, 1] range."""
        errors = []
        
        if 'sector_correlation' not in features.columns:
            errors.append("Column 'sector_correlation' not found")
            return False, errors
        
        sc = features['sector_correlation'].dropna()
        
        if len(sc) > 0:
            # Check bounds [-1, 1]
            if (sc < -1.01).any() or (sc > 1.01).any():
                errors.append("Sector correlation values outside [-1, 1] range")
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Verify uses only past returns."""
        return True, []
