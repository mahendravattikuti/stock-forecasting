"""Causal local-level Kalman filtering features."""

from typing import Optional

import numpy as np
import pandas as pd

from features.signal_processing.base import SignalFeatureModule


class KalmanFilterFeature(SignalFeatureModule):
    """Filter log prices and expose the standardized one-step innovation."""

    def __init__(self, config: Optional[dict] = None):
        config = config or {}
        super().__init__(name='kalman_filter', config=config)
        self.process_variance = float(config.get('process_variance', 1e-5))
        self.measurement_variance = float(config.get('measurement_variance', 1e-3))
        if self.process_variance < 0 or self.measurement_variance <= 0:
            raise ValueError(
                "process_variance must be nonnegative and measurement_variance positive"
            )

    def compute(
        self,
        df: pd.DataFrame,
        fit_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        observations = self._log_close(df).to_numpy()
        level = np.empty(len(observations))
        innovation_score = np.empty(len(observations))
        filtered_variance = np.empty(len(observations))
        estimate = observations[0]
        variance = self.measurement_variance

        for index, observation in enumerate(observations):
            predicted_variance = variance + self.process_variance
            innovation = observation - estimate
            innovation_variance = predicted_variance + self.measurement_variance
            gain = predicted_variance / innovation_variance
            estimate += gain * innovation
            variance = (1.0 - gain) * predicted_variance
            level[index] = estimate
            innovation_score[index] = innovation / np.sqrt(innovation_variance)
            filtered_variance[index] = variance

        return pd.DataFrame({
            'kalman_level': level,
            'kalman_innovation_zscore': innovation_score,
            'kalman_variance': filtered_variance,
        }, index=df.index)