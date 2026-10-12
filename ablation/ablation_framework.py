from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from evaluation.metrics import EvaluationMetrics


@dataclass
class AblationPlan:
    """Container for a family of ablation experiments.

    Each group can be represented as a list of feature names or a dictionary with
    metadata. The default implementation uses the feature name patterns used by
    the project specification for Tier-2, Tier-3, and signal-processing groups.
    """

    name: str = "phase_15_default"
    feature_groups: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.feature_groups:
            self.feature_groups = {}

    @staticmethod
    def _normalize_group(group: Any) -> dict[str, Any]:
        if isinstance(group, dict):
            payload = dict(group)
            columns = payload.get("columns")
            if columns is not None:
                payload["columns"] = list(columns)
            return payload
        return {"columns": list(group)}

    @classmethod
    def build_default_plan(
        cls,
        feature_columns: Sequence[str] | None = None,
        feature_catalog: Mapping[str, Sequence[str]] | None = None,
    ) -> "AblationPlan":
        columns = list(feature_columns or [])
        catalog = {
            "rsi": ["rsi_14", "rsi_9", "rsi_21"],
            "macd": ["macd_line", "macd_signal", "macd_histogram"],
            "bollinger": ["bollinger_upper", "bollinger_lower", "bollinger_bandwidth"],
            "tier2": [
                "rsi_14",
                "rsi_9",
                "rsi_21",
                "macd_line",
                "macd_signal",
                "macd_histogram",
                "bollinger_upper",
                "bollinger_lower",
                "bollinger_bandwidth",
                "stochastic_k",
                "stochastic_d",
                "atr_14",
                "adx_14",
                "obv",
                "momentum",
                "volatility",
            ],
            "tier3": [
                "market_regime",
                "sector_momentum",
                "market_beta",
                "cross_asset_correlation",
            ],
            "wavelet": ["wavelet_approximation", "wavelet_detail", "wavelet_energy"],
            "ssa": ["ssa_component_1", "ssa_component_2", "ssa_reconstruction"],
            "kalman": ["kalman_state", "kalman_smoothed", "kalman_gain"],
            "signal_processing": [
                "wavelet_approximation",
                "wavelet_detail",
                "wavelet_energy",
                "ssa_component_1",
                "ssa_component_2",
                "ssa_reconstruction",
                "kalman_state",
                "kalman_smoothed",
                "kalman_gain",
            ],
        }
        if feature_catalog is not None:
            catalog.update(feature_catalog)

        groups: dict[str, dict[str, Any]] = {"full_feature_set": {"columns": list(columns), "description": "Full feature set baseline"}}

        def match_columns(names: Iterable[str]) -> list[str]:
            matched: list[str] = []
            for column in columns:
                lower = column.lower()
                if any(name.lower() in lower for name in names):
                    matched.append(column)
            return matched

        for group_name, aliases in catalog.items():
            matches = match_columns(aliases)
            if not matches:
                continue
            groups[f"remove_{group_name}"] = {
                "columns": matches,
                "description": f"Remove {group_name} feature group",
            }

        if not groups.get("full_feature_set", {}).get("columns"):
            groups["full_feature_set"] = {"columns": [], "description": "Full feature set baseline"}

        return cls(name="phase_15_default", feature_groups=groups)

    def add_group(self, name: str, columns: Sequence[str], description: str | None = None) -> None:
        self.feature_groups[name] = {
            "columns": list(columns),
            "description": description or f"Ablation group: {name}",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "feature_groups": {
                key: {**value, "columns": list(value.get("columns", []))}
                for key, value in self.feature_groups.items()
            },
        }

    def save(self, path: str | Path) -> str:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=2)
        return str(output_path)

    @classmethod
    def from_json(cls, path: str | Path) -> "AblationPlan":
        with Path(path).open("r", encoding="utf-8") as file:
            payload = json.load(file)
        feature_groups = {
            key: cls._normalize_group(value)
            for key, value in payload.get("feature_groups", {}).items()
        }
        return cls(name=payload.get("name", "loaded_plan"), feature_groups=feature_groups)

    def __iter__(self):
        return iter(self.feature_groups.items())

    def __len__(self) -> int:
        return len(self.feature_groups)

    def __getitem__(self, key: str) -> dict[str, Any]:
        return self.feature_groups[key]


class AblationRunner:
    """Train and evaluate a model under a set of feature ablations."""

    def __init__(
        self,
        model_factory: Callable[[], Any] | Any | None = None,
        logger: logging.Logger | None = None,
    ):
        self.model_factory = model_factory
        self.logger = logger or logging.getLogger(__name__)

    @staticmethod
    def _get_default_model():
        try:
            from sklearn.linear_model import LinearRegression

            return LinearRegression()
        except Exception:  # pragma: no cover - fallback for minimal environments
            class _FallbackRegressor:
                def fit(self, X, y):
                    self._coef = np.zeros(np.asarray(X).shape[1])
                    return self

                def predict(self, X):
                    X = np.asarray(X)
                    return np.full(X.shape[0], float(np.mean(y) if hasattr(self, "_y_mean") else 0.0))

            return _FallbackRegressor()

    @staticmethod
    def _as_frame(frame: Any, name: str) -> pd.DataFrame:
        if isinstance(frame, pd.DataFrame):
            return frame
        array = np.asarray(frame)
        if array.ndim == 1:
            raise ValueError(f"{name} must be a 2D object or DataFrame")
        return pd.DataFrame(array)

    def _resolve_model(self) -> Any:
        if self.model_factory is None:
            return self._get_default_model()
        if callable(self.model_factory):
            return self.model_factory()
        return self.model_factory

    @staticmethod
    def _metric_summary(y_true: Sequence[float], y_pred: Sequence[float]) -> dict[str, float]:
        return {
            "mae": float(EvaluationMetrics.mae(y_true, y_pred)),
            "rmse": float(EvaluationMetrics.rmse(y_true, y_pred)),
            "mape": float(EvaluationMetrics.mape(y_true, y_pred)),
            "directional_accuracy": float(EvaluationMetrics.directional_accuracy(y_true, y_pred)),
            "sharpe_ratio": EvaluationMetrics.sharpe_ratio(y_pred),
            "information_coefficient": EvaluationMetrics.information_coefficient(y_true, y_pred),
        }

    @staticmethod
    def _paired_t_test(baseline: Sequence[float], ablation: Sequence[float]) -> float | None:
        if len(baseline) != len(ablation) or len(baseline) < 2:
            return None
        try:
            _, p_value = stats.ttest_rel(np.asarray(baseline), np.asarray(ablation))
            return float(p_value)
        except Exception:
            return None

    @staticmethod
    def _resolve_deltas(values: Mapping[str, float], reference: Mapping[str, float]) -> dict[str, float]:
        return {key: float(values.get(key, 0.0) - reference.get(key, 0.0)) for key in sorted({*values, *reference})}

    def _score_split(
        self,
        model: Any,
        X_train: Any,
        X_eval: Any,
        y_train: Sequence[float],
        y_eval: Sequence[float],
    ) -> tuple[Any, np.ndarray]:
        model.fit(X_train, y_train)
        predictions = model.predict(X_eval)
        return model, np.asarray(predictions, dtype=float)

    def run_ablations(
        self,
        X_train: Any,
        X_validation: Any,
        X_test: Any,
        y_train: Sequence[float],
        y_validation: Sequence[float],
        y_test: Sequence[float],
        feature_plan: AblationPlan | Mapping[str, Any] | None = None,
        feature_columns: Sequence[str] | None = None,
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        if feature_plan is None:
            if hasattr(X_train, "columns"):
                feature_columns = list(X_train.columns)
            plan = AblationPlan.build_default_plan(feature_columns=feature_columns)
        elif isinstance(feature_plan, AblationPlan):
            plan = feature_plan
        else:
            plan = AblationPlan(name="custom_plan", feature_groups={
                key: self._normalize_group(value) for key, value in dict(feature_plan).items()
            })

        X_train_df = self._as_frame(X_train, "X_train")
        X_validation_df = self._as_frame(X_validation, "X_validation")
        X_test_df = self._as_frame(X_test, "X_test")

        base_model = self._resolve_model()
        base_model.fit(X_train_df, np.asarray(y_train, dtype=float))
        validation_predictions = np.asarray(base_model.predict(X_validation_df), dtype=float)
        test_predictions = np.asarray(base_model.predict(X_test_df), dtype=float)
        baseline = {
            "validation": self._metric_summary(y_validation, validation_predictions),
            "test": self._metric_summary(y_test, test_predictions),
        }

        ablations: list[dict[str, Any]] = []
        for name, group in plan:
            if name == "full_feature_set":
                continue
            columns = list(group.get("columns", []))
            if not columns:
                continue
            mask = [column for column in X_train_df.columns if column not in columns]
            if len(mask) == 0:
                self.logger.warning("Skipping %s because all features would be removed", name)
                continue

            X_train_ablated = X_train_df.loc[:, mask]
            X_validation_ablated = X_validation_df.loc[:, mask]
            X_test_ablated = X_test_df.loc[:, mask]

            model = self._resolve_model()
            model.fit(X_train_ablated, np.asarray(y_train, dtype=float))
            val_pred = np.asarray(model.predict(X_validation_ablated), dtype=float)
            test_pred = np.asarray(model.predict(X_test_ablated), dtype=float)

            validation_metrics = self._metric_summary(y_validation, val_pred)
            test_metrics = self._metric_summary(y_test, test_pred)
            ablation_result = {
                "name": name,
                "description": group.get("description", ""),
                "removed_columns": columns,
                "validation_metrics": validation_metrics,
                "test_metrics": test_metrics,
                "delta_validation": self._resolve_deltas(validation_metrics, baseline["validation"]),
                "delta_test": self._resolve_deltas(test_metrics, baseline["test"]),
                "significance": {
                    "validation_p_value": self._paired_t_test(
                        np.abs(np.asarray(y_validation, dtype=float) - np.asarray(validation_predictions, dtype=float)),
                        np.abs(np.asarray(y_validation, dtype=float) - val_pred),
                    ),
                    "test_p_value": self._paired_t_test(
                        np.abs(np.asarray(y_test, dtype=float) - np.asarray(test_predictions, dtype=float)),
                        np.abs(np.asarray(y_test, dtype=float) - test_pred),
                    ),
                },
            }
            ablations.append(ablation_result)

        results = {
            "generated_at": pd.Timestamp.utcnow().isoformat(),
            "baseline": {
                "model": type(base_model).__name__,
                "validation": baseline["validation"],
                "test": baseline["test"],
            },
            "plan": plan.to_dict(),
            "ablations": ablations,
        }

        if output_path is not None:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w", encoding="utf-8") as file:
                json.dump(results, file, indent=2, default=str)

        return results

    @staticmethod
    def _normalize_group(group: Any) -> dict[str, Any]:
        if isinstance(group, dict):
            payload = dict(group)
            payload["columns"] = list(payload.get("columns", []))
            return payload
        return {"columns": list(group)}


def _load_default_plan() -> AblationPlan:
    default_path = Path("ablation_plan.json")
    if default_path.exists():
        return AblationPlan.from_json(default_path)
    return AblationPlan.build_default_plan()


__all__ = ["AblationPlan", "AblationRunner", "_load_default_plan"]
