"""
Tier-2 Other Indicators - Momentum and Volatility

Implements: Momentum (configurable periods), Volatility (configurable rolling std dev)
"""

import logging
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np

from features.base_features import FeatureModule


class MomentumFeature(FeatureModule):
    """Momentum over multiple periods - Price acceleration indicator."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='momentum', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.periods = cfg.get('momentum_periods', [5, 20, 60])
    
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
    """Rolling volatility (standard deviation of returns)."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='volatility', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.period = int(cfg.get('volatility_period', 20))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        close = df['Close'].astype(float)
        
        returns = close.pct_change()
        volatility = returns.rolling(window=self.period).std()
        
        col_name = f'volatility_{self.period}'
        result = pd.DataFrame({col_name: volatility}, index=df.index)
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        col_name = f'volatility_{self.period}'
        if col_name not in features.columns:
            errors.append(f"Column '{col_name}' not found")
            return False, errors
        
        volatility = features[col_name].dropna()
        if (volatility < -1e-6).any():
            errors.append("Volatility has negative values")
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []
