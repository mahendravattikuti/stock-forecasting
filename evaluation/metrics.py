"""Evaluation metrics and a combined metrics computation pipeline."""

from __future__ import annotations

import logging
from typing import Callable, Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from evaluation.confidence_intervals import BootstrapConfidenceIntervals


class EvaluationMetrics:
    """Static evaluation metrics for return forecasts."""

    @staticmethod
    def _vector(values, name: str) -> np.ndarray:
        vector = np.asarray(values, dtype=float).reshape(-1)
        if vector.size == 0:
            raise ValueError(f"{name} must not be empty")
        if not np.isfinite(vector).all():
            raise ValueError(f"{name} must contain only finite values")
        return vector

    @staticmethod
    def _paired(y_true, y_pred) -> tuple[np.ndarray, np.ndarray]:
        actual = EvaluationMetrics._vector(y_true, 'y_true')
        predicted = EvaluationMetrics._vector(y_pred, 'y_pred')
        if len(actual) != len(predicted):
            raise ValueError("y_true and y_pred must have the same length")
        return actual, predicted

    @staticmethod
    def mae(y_true, y_pred) -> float:
        """Mean absolute error."""
        actual, predicted = EvaluationMetrics._paired(y_true, y_pred)
        return float(np.mean(np.abs(predicted - actual)))

    @staticmethod
    def rmse(y_true, y_pred) -> float:
        """Root mean squared error."""
        actual, predicted = EvaluationMetrics._paired(y_true, y_pred)
        return float(np.sqrt(np.mean(np.square(predicted - actual))))

    @staticmethod
    def mape(y_true, y_pred) -> float:
        """Mean absolute percentage error in percent, ignoring zero actuals.

        Returns zero when all actual and predicted values are zero. Raises
        ``ValueError`` when all actuals are zero but at least one prediction is
        nonzero, since percentage error is undefined for that input.
        """
        actual, predicted = EvaluationMetrics._paired(y_true, y_pred)
        nonzero = ~np.isclose(actual, 0.0)
        if not nonzero.any():
            if np.all(np.isclose(predicted, 0.0)):
                return 0.0
            raise ValueError("MAPE is undefined when every actual value is zero")
        return float(np.mean(np.abs((predicted[nonzero] - actual[nonzero]) / actual[nonzero])) * 100.0)

    @staticmethod
    def directional_accuracy(y_true, y_pred) -> float:
        """Fraction of forecasts matching actual return direction, including flat."""
        actual, predicted = EvaluationMetrics._paired(y_true, y_pred)
        return float(np.mean(np.sign(actual) == np.sign(predicted)))

    @staticmethod
    def sharpe_ratio(returns) -> Optional[float]:
        """Mean return divided by population standard deviation (zero risk-free rate).

        Returns ``None`` for a constant nonzero series, where the ratio is
        undefined due to zero volatility; a constant zero series has Sharpe 0.
        """
        values = EvaluationMetrics._vector(returns, 'returns')
        volatility = float(np.std(values, ddof=0))
        if np.isclose(volatility, 0.0):
            return 0.0 if np.isclose(float(np.mean(values)), 0.0) else None
        return float(np.mean(values) / volatility)

    @staticmethod
    def information_coefficient(y_true, y_pred) -> Optional[float]:
        """Spearman rank correlation between actual and predicted returns."""
        actual, predicted = EvaluationMetrics._paired(y_true, y_pred)
        if len(actual) < 2 or np.ptp(actual) == 0 or np.ptp(predicted) == 0:
            return None
        coefficient = spearmanr(actual, predicted).statistic
        return float(coefficient) if np.isfinite(coefficient) else None

    @classmethod
    def compute_all(
        cls,
        y_true,
        y_pred,
        sharpe_returns=None,
    ) -> dict[str, Optional[float]]:
        """Compute all six metrics; Sharpe defaults to the predicted return series."""
        actual, predicted = cls._paired(y_true, y_pred)
        return {
            'mae': cls.mae(actual, predicted),
            'rmse': cls.rmse(actual, predicted),
            'mape': cls.mape(actual, predicted),
            'directional_accuracy': cls.directional_accuracy(actual, predicted),
            'sharpe_ratio': cls.sharpe_ratio(predicted if sharpe_returns is None else sharpe_returns),
            'information_coefficient': cls.information_coefficient(actual, predicted),
        }


class MetricsComputer:
    """Compute all evaluation metrics and bootstrap confidence intervals."""

    def __init__(
        self,
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95,
        random_state: Optional[int] = 42,
        logger: Optional[logging.Logger] = None,
    ):
        self.bootstrap = BootstrapConfidenceIntervals(
            n_bootstrap=n_bootstrap,
            confidence_level=confidence_level,
            random_state=random_state,
        )
        self.logger = logger or logging.getLogger(__name__)

    def compute_all_metrics(
        self,
        y_true,
        y_pred,
        split_name: str = 'test',
    ) -> dict:
        """Return point estimates and paired-bootstrap percentile intervals.

        Sharpe ratio is computed on predicted returns for model-specific
        comparability. All other metrics compare paired actual and predicted
        values directly.
        """
        actual, predicted = EvaluationMetrics._paired(y_true, y_pred)
        definitions: dict[str, tuple[Callable, bool]] = {
            'mae': (EvaluationMetrics.mae, True),
            'rmse': (EvaluationMetrics.rmse, True),
            'mape': (EvaluationMetrics.mape, True),
            'directional_accuracy': (EvaluationMetrics.directional_accuracy, True),
            'sharpe_ratio': (EvaluationMetrics.sharpe_ratio, False),
            'information_coefficient': (EvaluationMetrics.information_coefficient, True),
        }
        result = {}
        for name, (metric, paired) in definitions.items():
            metric_true = actual if paired else predicted
            metric_pred = predicted if paired else None
            result[name] = self.bootstrap.compute_ci(
                metric,
                metric_true,
                y_pred=metric_pred,
            )
            if name == 'mape':
                result[name]['zero_actuals_excluded'] = int(
                    np.isclose(actual, 0.0).sum()
                )
        return {
            'split': split_name,
            'sample_count': len(actual),
            'confidence_level': self.bootstrap.confidence_level,
            'bootstrap_samples': self.bootstrap.n_bootstrap,
            'metrics': result,
        }