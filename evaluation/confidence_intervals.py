"""Paired bootstrap percentile confidence intervals for evaluation metrics."""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np


class BootstrapConfidenceIntervals:
    """Compute metric confidence intervals using paired bootstrap samples."""

    def __init__(
        self,
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95,
        random_state: Optional[int] = 42,
    ):
        if n_bootstrap < 1:
            raise ValueError("n_bootstrap must be at least 1")
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        self.n_bootstrap = int(n_bootstrap)
        self.confidence_level = float(confidence_level)
        self.random_state = random_state
        self.rng = np.random.default_rng(random_state)

    @staticmethod
    def _finite_vector(values, name: str) -> np.ndarray:
        array = np.asarray(values, dtype=float).reshape(-1)
        if array.size == 0 or not np.isfinite(array).all():
            raise ValueError(f"{name} must contain finite, non-empty values")
        return array

    def compute_ci(
        self,
        metric_fn: Callable,
        y_true,
        y_pred=None,
    ) -> dict[str, Optional[float]]:
        """Return a point estimate and percentile interval for a metric.

        When ``y_pred`` is supplied, each bootstrap draw resamples matching
        indices from both arrays, preserving the pairing between observations.
        If a metric is undefined for every bootstrap draw, interval bounds are
        returned as ``None``.
        """
        actual = self._finite_vector(y_true, 'y_true')
        predicted = None if y_pred is None else self._finite_vector(y_pred, 'y_pred')
        if predicted is not None and len(actual) != len(predicted):
            raise ValueError("y_true and y_pred must have the same length")

        estimate = metric_fn(actual) if predicted is None else metric_fn(actual, predicted)
        estimate = float(estimate) if estimate is not None and np.isfinite(estimate) else None
        draws = []
        for _ in range(self.n_bootstrap):
            indices = self.rng.integers(0, len(actual), size=len(actual))
            try:
                value = (
                    metric_fn(actual[indices]) if predicted is None
                    else metric_fn(actual[indices], predicted[indices])
                )
            except (ValueError, FloatingPointError, ZeroDivisionError):
                continue
            if value is not None and np.isfinite(value):
                draws.append(float(value))

        if not draws:
            lower = upper = None
        else:
            tail = (1.0 - self.confidence_level) / 2.0
            lower, upper = np.quantile(draws, [tail, 1.0 - tail]).tolist()
        return {
            'value': estimate,
            'ci_lower': lower,
            'ci_upper': upper,
            'valid_bootstrap_samples': len(draws),
        }