"""Causal Daubechies wavelet decomposition features."""

from typing import Optional

import numpy as np
import pandas as pd
import pywt

from features.signal_processing.base import SignalFeatureModule


class WaveletFeature(SignalFeatureModule):
    """Decompose trailing log-price windows into approximation and details.

    Each output row is calculated from a fixed window ending on that row, so
    no observations after the feature timestamp enter the decomposition.
    """

    def __init__(self, config: Optional[dict] = None):
        config = config or {}
        super().__init__(name='wavelet', config=config)
        self.wavelet = config.get('wavelet', 'db4')
        self.window = int(config.get('window', 64))
        self.level = int(config.get('level', 3))
        if self.window < 2 or self.level < 1:
            raise ValueError("window must be at least 2 and level must be positive")
        wavelet = pywt.Wavelet(self.wavelet)
        max_level = pywt.dwt_max_level(self.window, wavelet.dec_len)
        if self.level > max_level:
            raise ValueError(
                f"level {self.level} exceeds maximum {max_level} for window {self.window}"
            )

    def compute(
        self,
        df: pd.DataFrame,
        fit_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        signal = self._log_close(df).to_numpy()
        columns = ['wavelet_approximation'] + [
            f'wavelet_detail_{detail}' for detail in range(1, self.level + 1)
        ]
        values = np.full((len(signal), len(columns)), np.nan)
        wavelet = pywt.Wavelet(self.wavelet)

        for end in range(self.window - 1, len(signal)):
            segment = signal[end - self.window + 1:end + 1]
            coefficients = pywt.wavedec(
                segment, wavelet, mode='symmetric', level=self.level
            )
            for component in range(len(coefficients)):
                isolated = [np.zeros_like(coefficient) for coefficient in coefficients]
                isolated[component] = coefficients[component]
                reconstructed = pywt.waverec(isolated, wavelet, mode='symmetric')
                values[end, component] = reconstructed[:self.window][-1]

        return pd.DataFrame(values, index=df.index, columns=columns)