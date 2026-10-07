"""Linear regression baseline for Tier-1 features."""

import numpy as np
from sklearn.linear_model import LinearRegression

from baselines.base_model import BaselineModel


class LinearRegressionBaseline(BaselineModel):
    """Fit linear regression to training returns and Tier-1 features."""

    def __init__(self, logger=None):
        super().__init__('linear_regression', logger=logger)
        self.estimator = LinearRegression()
        self.feature_names = None
        self.coefficients = None
        self.intercept = None

    def fit(self, y_train, X_train=None, **kwargs):
        target = self._as_vector(y_train, 'y_train')
        matrix = self._features(X_train)
        if len(target) != len(matrix):
            raise ValueError("X_train and y_train must have the same number of rows")
        self.feature_names = list(X_train.columns) if hasattr(X_train, 'columns') else None
        self.estimator.fit(matrix, target)
        self.coefficients = self.estimator.coef_.reshape(-1).astype(float)
        self.intercept = float(self.estimator.intercept_)
        self.train_start_date, self.train_end_date = self._metadata_dates(y_train)
        self.is_fitted = True
        return self

    def predict(self, X=None, steps=None, **kwargs) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("LinearRegressionBaseline must be fitted before predict")
        return self.estimator.predict(self._features(X, self.feature_names)).astype(float)

    def coefficient_interpretation(self) -> dict:
        """Map feature names to fitted coefficients and return intercept."""
        names = self.feature_names or [f'feature_{i}' for i in range(len(self.coefficients))]
        return {
            'intercept': self.intercept,
            'coefficients': dict(zip(names, self.coefficients.tolist())),
        }