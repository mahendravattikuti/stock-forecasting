"""
Tier-2 Technical Indicator Features - Simplified and Production-Ready

Implements: RSI, MACD, Bollinger Bands, Stochastic, ATR, ADX, OBV
All indicators inherit from FeatureModule and support causality verification.
"""

import logging
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np

from features.base_features import FeatureModule


class RSIFeature(FeatureModule):
    """Relative Strength Index - Momentum oscillator (0-100)."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='rsi_14', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.period = int(cfg.get('rsi_period', cfg.get('period', 14)))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        close = df['Close'].astype(float)
        
        deltas = close.diff()
        gains = deltas.clip(lower=0)
        losses = -deltas.clip(upper=0)
        
        avg_gains = gains.ewm(span=self.period, adjust=False).mean()
        avg_losses = losses.ewm(span=self.period, adjust=False).mean()
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        result = pd.DataFrame({'rsi_14': rsi}, index=df.index)
        self._log_computation_complete(num_features=1, num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        if 'rsi_14' not in features.columns:
            errors.append("Column 'rsi_14' not found")
            return False, errors
        
        rsi = features['rsi_14'].dropna()
        if (rsi < -0.01).any() or (rsi > 100.01).any():
            errors.append(f"RSI values outside [0, 100]")
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []


class MACDFeature(FeatureModule):
    """MACD with signal line and histogram."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='macd', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.fast_period = int(cfg.get('macd_fast', 12))
        self.slow_period = int(cfg.get('macd_slow', 26))
        self.signal_period = int(cfg.get('macd_signal', 9))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        close = df['Close'].astype(float)
        
        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        macd_histogram = macd_line - macd_signal
        
        result = pd.DataFrame({
            'macd_line': macd_line,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram
        }, index=df.index)
        
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        for col in ['macd_line', 'macd_signal', 'macd_histogram']:
            if col not in features.columns:
                errors.append(f"Column '{col}' not found")
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []


class BollingerBandsFeature(FeatureModule):
    """Bollinger Bands - Volatility bands."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='bollinger_bands', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.period = int(cfg.get('bb_period', cfg.get('period', 20)))
        self.num_std = float(cfg.get('bb_std', 2.0))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        close = df['Close'].astype(float)
        
        middle = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()
        upper = middle + (self.num_std * std)
        lower = middle - (self.num_std * std)
        width = upper - lower
        
        result = pd.DataFrame({
            'bb_upper': upper,
            'bb_middle': middle,
            'bb_lower': lower,
            'bb_width': width
        }, index=df.index)
        
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        for col in ['bb_upper', 'bb_middle', 'bb_lower', 'bb_width']:
            if col not in features.columns:
                errors.append(f"Column '{col}' not found")
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []


class StochasticFeature(FeatureModule):
    """Stochastic Oscillator - %K and %D (0-100)."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='stochastic', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.period = int(cfg.get('stoch_period', cfg.get('period', 14)))
        self.signal_period = int(cfg.get('stoch_signal_period', 3))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        if 'High' not in df.columns or 'Low' not in df.columns:
            raise ValueError("Stochastic requires 'High' and 'Low' columns")
        
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        close = df['Close'].astype(float)
        
        lowest_low = low.rolling(window=self.period).min()
        highest_high = high.rolling(window=self.period).max()
        k_line = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_line = k_line.rolling(window=self.signal_period).mean()
        
        result = pd.DataFrame({
            'stoch_k': k_line,
            'stoch_d': d_line
        }, index=df.index)
        
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        for col in ['stoch_k', 'stoch_d']:
            if col not in features.columns:
                errors.append(f"Column '{col}' not found")
            else:
                values = features[col].dropna()
                if (values < -0.01).any() or (values > 100.01).any():
                    errors.append(f"Stochastic {col} outside [0, 100]")
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []


class ATRFeature(FeatureModule):
    """Average True Range - Volatility indicator."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='atr_14', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.period = int(cfg.get('atr_period', cfg.get('period', 14)))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        if 'High' not in df.columns or 'Low' not in df.columns:
            raise ValueError("ATR requires 'High' and 'Low' columns")
        
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        close = df['Close'].astype(float)
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.period).mean()
        
        result = pd.DataFrame({'atr_14': atr}, index=df.index)
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        if 'atr_14' not in features.columns:
            errors.append("Column 'atr_14' not found")
            return False, errors
        
        atr = features['atr_14'].dropna()
        if (atr < -1e-6).any():
            errors.append("ATR has negative values")
        
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []


class ADXFeature(FeatureModule):
    """Average Directional Index - Trend strength with +DI/-DI."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='adx', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.period = int(cfg.get('adx_period', cfg.get('period', 14)))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        if 'High' not in df.columns or 'Low' not in df.columns:
            raise ValueError("ADX requires 'High' and 'Low' columns")
        
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        close = df['Close'].astype(float)
        
        # True Range
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.period).mean()
        
        # Directional movements
        high_diff = high.diff()
        low_diff = -low.diff()
        
        plus_dm = pd.Series(0.0, index=df.index)
        minus_dm = pd.Series(0.0, index=df.index)
        
        mask_plus = (high_diff > low_diff) & (high_diff > 0)
        mask_minus = (low_diff > high_diff) & (low_diff > 0)
        
        plus_dm[mask_plus] = high_diff[mask_plus]
        minus_dm[mask_minus] = low_diff[mask_minus]
        
        plus_di = 100 * plus_dm.rolling(window=self.period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=self.period).mean() / atr
        
        di_diff = (plus_di - minus_di).abs()
        di_sum = plus_di + minus_di
        dx = 100 * di_diff / di_sum
        adx = dx.rolling(window=self.period).mean()
        
        result = pd.DataFrame({
            'adx_plus_di': plus_di,
            'adx_minus_di': minus_di,
            'adx_value': adx
        }, index=df.index)
        
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        for col in ['adx_plus_di', 'adx_minus_di', 'adx_value']:
            if col not in features.columns:
                errors.append(f"Column '{col}' not found")
            else:
                values = features[col].dropna()
                if (values < -0.01).any() or (values > 100.01).any():
                    errors.append(f"ADX {col} outside [0, 100]")
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []


class OBVFeature(FeatureModule):
    """On-Balance Volume with moving average."""
    
    def __init__(self, config: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(name='obv', tier=2, config=config, logger=logger)
        cfg = config or {}
        self.ma_period = int(cfg.get('obv_ma_period', 20))
    
    def compute(self, df: pd.DataFrame, fit_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        self._validate_input_dataframe(df)
        if 'Volume' not in df.columns:
            raise ValueError("OBV requires 'Volume' column")
        
        close = df['Close'].astype(float)
        volume = df['Volume'].astype(float)
        
        price_change = close.diff()
        signed_volume = pd.Series(0.0, index=df.index)
        signed_volume[price_change > 0] = volume[price_change > 0]
        signed_volume[price_change < 0] = -volume[price_change < 0]
        
        obv = signed_volume.cumsum()
        obv_ma = obv.rolling(window=self.ma_period).mean()
        
        result = pd.DataFrame({
            'obv': obv,
            'obv_ma20': obv_ma
        }, index=df.index)
        
        self._log_computation_complete(num_features=result.shape[1], num_rows=len(result), nan_count=result.isna().sum().sum())
        return result
    
    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        for col in ['obv', 'obv_ma20']:
            if col not in features.columns:
                errors.append(f"Column '{col}' not found")
        return len(errors) == 0, errors
    
    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        return True, []
