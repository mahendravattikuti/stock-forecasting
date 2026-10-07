"""Cross-validated Ridge regression baseline."""

import numpy as np
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from baselines.base_model import BaselineModel


class RidgeRegressionBaseline(BaselineModel):
    """Tune L2 regularization with five-fold CV on training observations."""

    def __init__(self, alphas=None, cv: int = 5, logger=None):
        super().__init__('ridge_regression', logger=logger)
        self.alphas = np.asarray(
            alphas if alphas is not None else np.logspace(-3, 3, 50), dtype=float
        )
        if self.alphas.ndim != 1 or len(self.alphas) == 0 or (self.alphas <= 0).any():
            raise ValueError("alphas must be a non-empty sequence of positive values")
        if cv < 2:
            raise ValueError("cv must be at least 2")
        self.cv = int(cv)
        self.estimator = None
        self.best_alpha = None
        self.cv_best_alpha = None
        self.tuning_split = 'train_cv'
        self.feature_names = None

    def fit(self, y_train, X_train=None, **kwargs):
        target = self._as_vector(y_train, 'y_train')
        matrix = self._features(X_train)
        if len(target) != len(matrix):
            raise ValueError("X_train and y_train must have the same number of rows")
        if len(target) < 2:
            raise ValueError("At least two training samples are required for RidgeCV")
        self.feature_names = list(X_train.columns) if hasattr(X_train, 'columns') else None
        folds = min(self.cv, len(target))
        self.estimator = make_pipeline(
            StandardScaler(), RidgeCV(alphas=self.alphas, cv=folds)
        )
        self.estimator.fit(matrix, target)
        self.cv_best_alpha = float(self.estimator.named_steps['ridgecv'].alpha_)
        self.best_alpha = self.cv_best_alpha
        X_validation = kwargs.get('X_validation')
        y_validation = kwargs.get('y_validation')
        if X_validation is not None or y_validation is not None:
            if X_validation is None or y_validation is None:
                raise ValueError("X_validation and y_validation must be provided together")
            validation_target = self._as_vector(y_validation, 'y_validation')
            validation_matrix = self._features(X_validation, self.feature_names)
            if len(validation_target) != len(validation_matrix):
                raise ValueError("X_validation and y_validation must have the same number of rows")
            if hasattr(X_validation, 'columns') and hasattr(y_validation, 'index'):
                if not X_validation.index.equals(y_validation.index):
                    raise ValueError("Validation feature and target indices do not match")

            training_scaler = StandardScaler().fit(matrix)
            scaled_train = training_scaler.transform(matrix)
            scaled_validation = training_scaler.transform(validation_matrix)
            validation_scores = {}
            for alpha in self.alphas:
                candidate = Ridge(alpha=float(alpha)).fit(scaled_train, target)
                validation_scores[float(alpha)] = float(
                    np.mean(np.square(candidate.predict(scaled_validation) - validation_target))
                )
            self.best_alpha = min(validation_scores, key=validation_scores.get)
            self.estimator = make_pipeline(
                StandardScaler(), Ridge(alpha=self.best_alpha)
            )
            self.estimator.fit(matrix, target)
            self.validation_scores = validation_scores
            self.tuning_split = 'validation'
        self.train_start_date, self.train_end_date = self._metadata_dates(y_train)
        self.is_fitted = True
        return self

    def predict(self, X=None, steps=None, **kwargs) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("RidgeRegressionBaseline must be fitted before predict")
        return self.estimator.predict(self._features(X, self.feature_names)).astype(float)