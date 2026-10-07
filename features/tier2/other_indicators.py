"""
Tier-2 Other Indicators - Momentum and Volatility

Implements: Momentum (5, 20, 60), Volatility (20-period std dev of returns)
"""

import logging
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np

from features.base_features import FeatureModule


class MomentumFeature(FeatureModule):
    """Momentum over multiple periods (5, 20, 60) - Price acceleration indicator."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='momentum', tier=2, config=config, logger=logger)
        self.periods = [5, 20, 60]
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        close = df['Close'].astype(float)
        
        result_dict = {}
        for period in self.periods:
            momentum = (close / close.shift(period)) - 1
            result_dict[f'momentum_{period}'] = momentum
        
        result = pd.DataFrame(result_dict, index=df.index)
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        for period in self.periods:
            col_name = f'momentum_{period}'
            if col_name not in features.columns:
                errors.append(f"Column '{col_name}' not found")
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []


class VolatilityFeature(FeatureModule):
    """20-period rolling volatility (standard deviation of returns)."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='volatility', tier=2, config=config, logger=logger)
        self.period = 20
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        close = df['Close'].astype(float)
        
        returns = close.pct_change()
        volatility = returns.rolling(window=self.period).std()
        
        result = pd.DataFrame({'volatility_20': volatility}, index=df.index)
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        if 'volatility_20' not in features.columns:
            errors.append("Column 'volatility_20' not found")
            return False, errors
        
        volatility = features['volatility_20'].dropna()
        if (volatility < -1e-6).any():
            errors.append("Volatility has negative values")
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []

