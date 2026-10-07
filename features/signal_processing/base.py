"""Shared validation helpers for signal-processing feature modules."""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from features.base_features import FeatureModule


class SignalFeatureModule(FeatureModule):
    """FeatureModule helpers for methods operating on the Close series."""

    def __init__(self, name: str, config: Optional[dict] = None):
        super().__init__(name=name, tier=4, config=config)

    @staticmethod
    def _log_close(df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty:
            raise ValueError("Input DataFrame is empty or None")
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("Input DataFrame must have a DatetimeIndex")
        if 'Close' not in df.columns:
            raise ValueError("Input DataFrame must contain a 'Close' column")

        close = pd.to_numeric(df['Close'], errors='coerce').astype(float)
        values = close.to_numpy()
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("Close values must be finite and greater than zero")
        return np.log(close).rename('log_close')

    def validate(self, features: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        if features is None or features.empty:
            return False, ["Features DataFrame is empty or None"]
        if not isinstance(features.index, pd.DatetimeIndex):
            errors.append("Features DataFrame must have a DatetimeIndex")
        if features.columns.empty:
            errors.append("Features DataFrame has no columns")
        if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in features.dtypes):
            errors.append("Signal-processing features must be numeric")
        if np.isinf(features.select_dtypes(include=[np.number]).to_numpy()).any():
            errors.append("Signal-processing features contain infinite values")
        return not errors, errors

    def check_causality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        from features.signal_processing.causality import SignalProcessingCausalityChecker

        return SignalProcessingCausalityChecker().check(self, df)