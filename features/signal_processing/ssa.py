"""Causal Singular Spectrum Analysis features."""

from typing import Optional

import numpy as np
import pandas as pd

from features.signal_processing.base import SignalFeatureModule


class SSAFeature(SignalFeatureModule):
    """Extract a rank-one trend and residual from trailing log-price windows."""

    def __init__(self, config: Optional[dict] = None):
        config = config or {}
        super().__init__(name='ssa', config=config)
        self.window = int(config.get('window', 40))
        self.embedding_dimension = int(config.get('embedding_dimension', 10))
        if self.window < 3:
            raise ValueError("window must be at least 3")
        if not 2 <= self.embedding_dimension < self.window:
            raise ValueError("embedding_dimension must be between 2 and window - 1")

    def compute(
        self,
        df: pd.DataFrame,
        fit_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        signal = self._log_close(df).to_numpy()
        trend = np.full(len(signal), np.nan)
        residual = np.full(len(signal), np.nan)
        rows = self.embedding_dimension
        columns = self.window - rows + 1

        for end in range(self.window - 1, len(signal)):
            segment = signal[end - self.window + 1:end + 1]
            trajectory = np.column_stack([
                segment[offset:offset + columns] for offset in range(rows)
            ])
            left, singular_values, right = np.linalg.svd(
                trajectory, full_matrices=False
            )
            latest_trend = singular_values[0] * left[-1, 0] * right[0, -1]
            trend[end] = latest_trend
            residual[end] = segment[-1] - latest_trend

        return pd.DataFrame({
            'ssa_trend': trend,
            'ssa_residual': residual,
        }, index=df.index)