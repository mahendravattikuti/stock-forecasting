"""Historical mean return baseline."""

import numpy as np

from baselines.base_model import BaselineModel


class HistoricalMeanBaseline(BaselineModel):
    """Predict the training-period mean return for each future observation."""

    def __init__(self, logger=None):
        super().__init__('historical_mean', logger=logger)
        self.mean_return = None

    def fit(self, y_train, X_train=None, **kwargs):
        values = self._as_vector(y_train, 'y_train')
        self.mean_return = float(np.mean(values))
        self.is_fitted = True
        return self

    def predict(self, X=None, steps=None, **kwargs) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("HistoricalMeanBaseline must be fitted before predict")
        horizon = steps if steps is not None else (len(X) if X is not None else None)
        if horizon is None or int(horizon) < 1:
            raise ValueError("steps or a non-empty X is required to define forecast horizon")
        return np.full(int(horizon), self.mean_return, dtype=float)