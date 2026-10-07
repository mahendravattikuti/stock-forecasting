"""Naive random-walk return baseline."""

import numpy as np

from baselines.base_model import BaselineModel


class RandomWalkBaseline(BaselineModel):
    """Predict the next return as the most recently observed return."""

    def __init__(self, logger=None):
        super().__init__('random_walk', logger=logger)
        self.last_value = None

    def fit(self, y_train, X_train=None, **kwargs):
        values = self._as_vector(y_train, 'y_train')
        self.last_value = float(values[-1])
        self.is_fitted = True
        return self

    def predict(self, X=None, steps=None, current_values=None, **kwargs) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("RandomWalkBaseline must be fitted before predict")
        if current_values is not None:
            current = self._as_vector(current_values, 'current_values')
            return current.copy()
        if X is not None:
            return self._as_vector(X, 'X').copy()
        if steps is None or steps < 1:
            raise ValueError("steps must be a positive integer when no current values are provided")
        return np.full(int(steps), self.last_value, dtype=float)