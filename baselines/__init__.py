"""Baseline forecasting models and training/evaluation manager."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from baselines.arima_model import ARIMABaseline
from baselines.base_model import BaselineModel
from baselines.historical_mean import HistoricalMeanBaseline
from baselines.linear_regression import LinearRegressionBaseline
from baselines.random_walk import RandomWalkBaseline
from baselines.ridge_regression import RidgeRegressionBaseline


class BaselineManager:
	"""Fit all baseline models on training data and evaluate held-out periods."""

	def __init__(
		self,
		model_dir: str | Path = 'results/baseline_models',
		config: Optional[dict] = None,
		logger: Optional[logging.Logger] = None,
	):
		self.model_dir = Path(model_dir)
		self.config = config if config is not None else {}
		self.logger = logger or logging.getLogger(__name__)
		self.models: dict[str, BaselineModel] = {}

	@staticmethod
	def _series(values, name: str) -> np.ndarray:
		return BaselineModel._as_vector(values, name)

	@staticmethod
	def _validate_features(X, y, name: str) -> None:
		if X is None:
			raise ValueError(f"{name} features are required for regression baselines")
		if len(X) != len(y):
			raise ValueError(f"{name} features and target lengths do not match")
		if isinstance(X, pd.DataFrame) and isinstance(y, pd.Series):
			if not X.index.equals(y.index):
				raise ValueError(f"{name} feature and target indices do not match")

	@staticmethod
	def _forecast_returns_from_closes(last_close: float, forecast_closes: np.ndarray) -> np.ndarray:
		prior = np.concatenate(([last_close], forecast_closes[:-1]))
		return forecast_closes / prior - 1.0

	def _save_model(self, name: str, model: BaselineModel, metadata: dict) -> None:
		self.model_dir.mkdir(parents=True, exist_ok=True)
		model_path = self.model_dir / f'{name}.joblib'
		joblib.dump(model, model_path)
		metadata['model_path'] = str(model_path)
		with (self.model_dir / f'{name}_metadata.json').open('w', encoding='utf-8') as file:
			json.dump(metadata, file, indent=2, default=str)

	def train_and_evaluate_all(
		self,
		y_train,
		y_validation,
		y_test,
		X_train=None,
		X_validation=None,
		X_test=None,
		X_tier1_train=None,
		X_tier1_validation=None,
		X_tier1_test=None,
		close_train=None,
		close_validation=None,
		close_test=None,
		results_path: str | Path = 'results/reports/baseline_results.json',
	) -> dict:
		"""Train five baselines and evaluate validation/test return forecasts.

		Regression models use the supplied feature matrices; callers should
		provide Tier-1 features to Linear Regression and their selected full
		feature set to Ridge Regression. ARIMA is fit only on ``close_train``
		and its close forecasts are converted to returns before evaluation.
		"""
		self._validate_features(X_train, y_train, 'train')
		self._validate_features(X_validation, y_validation, 'validation')
		self._validate_features(X_test, y_test, 'test')
		X_tier1_train = X_train if X_tier1_train is None else X_tier1_train
		X_tier1_validation = X_validation if X_tier1_validation is None else X_tier1_validation
		X_tier1_test = X_test if X_tier1_test is None else X_tier1_test
		self._validate_features(X_tier1_train, y_train, 'tier1 train')
		self._validate_features(X_tier1_validation, y_validation, 'tier1 validation')
		self._validate_features(X_tier1_test, y_test, 'tier1 test')
		train = self._series(y_train, 'y_train')
		validation = self._series(y_validation, 'y_validation')
		test = self._series(y_test, 'y_test')
		if close_train is None or close_validation is None or close_test is None:
			raise ValueError("close_train, close_validation, and close_test are required for ARIMA")
		train_closes = self._series(close_train, 'close_train')
		validation_closes = self._series(close_validation, 'close_validation')
		test_closes = self._series(close_test, 'close_test')
		if len(train_closes) < 10:
			raise ValueError("At least 10 training closes are required for ARIMA")
		if len(validation_closes) != len(validation) or len(test_closes) != len(test):
			raise ValueError("Close and return target lengths must match within each split")

		ridge_alphas = self.config.get(
			'ridge_alphas', np.logspace(-3, 3, 50).tolist()
		)
		ridge_cv = self.config.get('ridge_cv', 5)
		models: dict[str, BaselineModel] = {
			'random_walk': RandomWalkBaseline(logger=self.logger),
			'arima_111': ARIMABaseline(logger=self.logger),
			'linear_regression': LinearRegressionBaseline(logger=self.logger),
			'ridge_regression': RidgeRegressionBaseline(
				alphas=ridge_alphas, cv=ridge_cv, logger=self.logger
			),
			'historical_mean': HistoricalMeanBaseline(logger=self.logger),
		}

		models['random_walk'].fit(train)
		models['historical_mean'].fit(train)
		models['arima_111'].fit(train, close_train=close_train)
		models['linear_regression'].fit(train, X_train=X_tier1_train)
		models['ridge_regression'].fit(
			train,
			X_train=X_train,
			X_validation=X_validation,
			y_validation=validation,
		)

		# For each one-step baseline forecast, use only returns observed before
		# the prediction timestamp. Test forecasts may use realized validation
		# returns, as they are historical by the time each test point is forecast.
		validation_current = np.concatenate(([train[-1]], validation[:-1]))
		test_history = np.concatenate((validation[-1:], test[:-1]))
		predictions = {
			'random_walk': {
				'validation': models['random_walk'].predict(current_values=validation_current),
				'test': models['random_walk'].predict(current_values=test_history),
			},
			'historical_mean': {
				'validation': models['historical_mean'].predict(steps=len(validation)),
				'test': models['historical_mean'].predict(steps=len(test)),
			},
		}
		predictions['linear_regression'] = {
			'validation': models['linear_regression'].predict(X_tier1_validation),
			'test': models['linear_regression'].predict(X_tier1_test),
		}
		predictions['ridge_regression'] = {
			'validation': models['ridge_regression'].predict(X_validation),
			'test': models['ridge_regression'].predict(X_test),
		}

		arima_close_forecasts = models['arima_111'].predict(
			steps=len(validation) + len(test)
		)
		arima_returns = self._forecast_returns_from_closes(
			float(train_closes[-1]), arima_close_forecasts
		)
		predictions['arima_111'] = {
			'validation': arima_returns[:len(validation)],
			'test': arima_returns[len(validation):],
		}

		targets = {'validation': validation, 'test': test}
		results = {
			'created_at': datetime.now(timezone.utc).isoformat(),
			'target': 'one-step-ahead returns',
			'models': {},
		}
		train_start, train_end = BaselineModel._metadata_dates(y_train)
		validation_start, validation_end = BaselineModel._metadata_dates(y_validation)
		feature_names = list(X_train.columns) if hasattr(X_train, 'columns') else None

		for name, model in models.items():
			model_result = {}
			for split_name in ('validation', 'test'):
				estimate = predictions[name][split_name]
				if len(estimate) != len(targets[split_name]):
					raise RuntimeError(f"{name} produced misaligned {split_name} predictions")
				model_result[split_name] = model.evaluate(targets[split_name], estimate)
				model_result[f'{split_name}_predictions'] = [float(value) for value in estimate]
			model_result['metadata'] = {
				'train_start_date': train_start,
				'train_end_date': train_end,
				'feature_set_used': feature_names if name in {
					'ridge_regression'
				} else (
					list(X_tier1_train.columns)
					if name == 'linear_regression' and hasattr(X_tier1_train, 'columns')
					else []
				),
				'hyperparameters': {
					'order': list(model.order) if isinstance(model, ARIMABaseline) else None,
					'best_alpha': model.best_alpha if isinstance(model, RidgeRegressionBaseline) else None,
					'alphas': model.alphas.tolist() if isinstance(model, RidgeRegressionBaseline) else None,
					'cv': model.cv if isinstance(model, RidgeRegressionBaseline) else None,
					'cv_best_alpha': model.cv_best_alpha if isinstance(model, RidgeRegressionBaseline) else None,
					'tuning_split': model.tuning_split if isinstance(model, RidgeRegressionBaseline) else None,
				},
				'validation_performance': model_result['validation'],
				'fitted_on': 'train',
			}
			self._save_model(name, model, model_result['metadata'])
			results['models'][name] = model_result

		if isinstance(models['ridge_regression'], RidgeRegressionBaseline):
			self.config['ridge_best_alpha'] = models['ridge_regression'].best_alpha
		results['training_period'] = {
			'start_date': train_start,
			'end_date': train_end,
			'rows': len(train),
		}
		results['validation_period'] = {
			'start_date': validation_start,
			'end_date': validation_end,
			'rows': len(validation),
		}
		results['test_rows'] = len(test)

		result_path = Path(results_path)
		result_path.parent.mkdir(parents=True, exist_ok=True)
		with result_path.open('w', encoding='utf-8') as file:
			json.dump(results, file, indent=2, default=str)
		self.models = models
		self.logger.info("Baseline training and evaluation complete")
		return results


__all__ = [
	'BaselineModel',
	'BaselineManager',
	'RandomWalkBaseline',
	'ARIMABaseline',
	'LinearRegressionBaseline',
	'RidgeRegressionBaseline',
	'HistoricalMeanBaseline',
]
