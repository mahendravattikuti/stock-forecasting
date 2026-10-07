"""ARIMA(1,1,1) close-price forecasting baseline."""

import numpy as np
from statsmodels.tsa.arima.model import ARIMA

from baselines.base_model import BaselineModel


class ARIMABaseline(BaselineModel):
    """Fit ARIMA(1,1,1) to training closes and forecast future close levels."""

    def __init__(self, order=(1, 1, 1), logger=None):
        if tuple(order) != (1, 1, 1):
            raise ValueError("ARIMABaseline is defined as ARIMA(1,1,1)")
        super().__init__('arima_111', logger=logger)
        self.order = tuple(order)
        self.model_fit = None
        self.train_end_date = None

    def fit(self, y_train, X_train=None, close_train=None, **kwargs):
        close = y_train if close_train is None else close_train
        values = self._as_vector(close, 'close_train')
        if len(values) < 10:
            raise ValueError("ARIMA(1,1,1) requires at least 10 training close prices")
        self.model_fit = ARIMA(values, order=self.order).fit()
        self.train_end_date = self._metadata_dates(close)[1]
        self.is_fitted = True
        return self

    def predict(self, X=None, steps=None, **kwargs) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("ARIMABaseline must be fitted before predict")
        horizon = steps if steps is not None else (len(X) if X is not None else None)
        if horizon is None or int(horizon) < 1:
            raise ValueError("steps or a non-empty X is required to define forecast horizon")
        prediction = np.asarray(self.model_fit.forecast(steps=int(horizon)), dtype=float)
        if not np.isfinite(prediction).all():
            raise ValueError("ARIMA produced non-finite forecasts")
        return prediction