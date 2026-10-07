"""Shared interface and metrics for return-forecasting baselines."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np
import pandas as pd


class BaselineModel(ABC):
    """Abstract forecasting baseline with common evaluation metrics."""

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.is_fitted = False

    @abstractmethod
    def fit(self, y_train, X_train=None, **kwargs) -> 'BaselineModel':
        """Fit model parameters using training data only."""

    @abstractmethod
    def predict(self, X=None, steps: Optional[int] = None, **kwargs) -> np.ndarray:
        """Generate predictions for an explicit feature frame or horizon."""

    @staticmethod
    def _as_vector(values, name: str) -> np.ndarray:
        vector = np.asarray(values, dtype=float).reshape(-1)
        if vector.size == 0 or not np.isfinite(vector).all():
            raise ValueError(f"{name} must contain finite, non-empty values")
        return vector

    @staticmethod
    def _directional_accuracy(y_true, y_pred) -> float:
        actual = np.sign(np.asarray(y_true, dtype=float))
        predicted = np.sign(np.asarray(y_pred, dtype=float))
        return float(np.mean(actual == predicted))

    def evaluate(self, y_true, y_pred) -> dict[str, float]:
        """Compute MAE, RMSE, and directional accuracy."""
        actual = self._as_vector(y_true, 'y_true')
        predicted = self._as_vector(y_pred, 'y_pred')
        if len(actual) != len(predicted):
            raise ValueError("y_true and y_pred must have the same number of values")
        errors = predicted - actual
        return {
            'mae': float(np.mean(np.abs(errors))),
            'rmse': float(np.sqrt(np.mean(np.square(errors)))),
            'directional_accuracy': self._directional_accuracy(actual, predicted),
        }

    @staticmethod
    def _features(X, expected_columns=None) -> np.ndarray:
        if X is None:
            raise ValueError("Feature matrix X is required for this model")
        if isinstance(X, pd.DataFrame):
            if expected_columns is not None and list(X.columns) != list(expected_columns):
                raise ValueError("Feature columns/order differ from training data")
            matrix = X.to_numpy(dtype=float)
        else:
            matrix = np.asarray(X, dtype=float)
        if matrix.ndim == 1:
            matrix = matrix.reshape(-1, 1)
        if matrix.ndim != 2 or matrix.shape[0] == 0 or not np.isfinite(matrix).all():
            raise ValueError("X must be a non-empty 2D matrix of finite values")
        return matrix

    @staticmethod
    def _metadata_dates(values: Any) -> tuple[Optional[str], Optional[str]]:
        if isinstance(values, (pd.Series, pd.DataFrame)) and isinstance(values.index, pd.DatetimeIndex):
            return values.index.min().isoformat(), values.index.max().isoformat()
        return None, None