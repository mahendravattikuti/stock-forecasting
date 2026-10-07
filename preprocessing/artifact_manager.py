"""Train-only preprocessing and versioned artifact persistence."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


class TrainOnlyStandardScaler:
    """StandardScaler wrapper that requires an explicit training fit role.

    ``transform`` never changes fitted parameters and is used for validation
    and test partitions. The fit role, fit sample count, date range, features,
    and input fingerprint are retained for provenance checks.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, **scaler_kwargs: Any):
        self.scaler = StandardScaler(**scaler_kwargs)
        self.logger = logger or logging.getLogger(__name__)
        self.fit_split: Optional[str] = None
        self.fit_metadata: dict[str, Any] = {}
        self.feature_names: Optional[list[str]] = None

    @staticmethod
    def _as_matrix(data: Any) -> tuple[np.ndarray, Optional[pd.Index]]:
        if isinstance(data, pd.DataFrame):
            if data.empty or data.shape[1] == 0:
                raise ValueError("Scaler input DataFrame must contain rows and features")
            if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in data.dtypes):
                raise TypeError("Scaler input features must all be numeric")
            matrix = data.to_numpy(dtype=float)
            columns = data.columns
        else:
            matrix = np.asarray(data, dtype=float)
            columns = None
            if matrix.ndim == 1:
                matrix = matrix.reshape(-1, 1)
        if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
            raise ValueError("Scaler input must be a non-empty 2D array")
        if not np.isfinite(matrix).all():
            raise ValueError("Scaler input must contain only finite values")
        return matrix, columns

    @staticmethod
    def _fingerprint(matrix: np.ndarray, columns: Optional[pd.Index]) -> str:
        digest = hashlib.sha256()
        digest.update(np.ascontiguousarray(matrix, dtype=np.float64).tobytes())
        if columns is not None:
            digest.update(json.dumps([str(column) for column in columns]).encode('utf-8'))
        return digest.hexdigest()

    def fit(self, data: Any, split_name: Optional[str] = None) -> 'TrainOnlyStandardScaler':
        """Fit only when the caller explicitly identifies training data."""
        if split_name != 'train':
            self.logger.critical(
                "Preprocessing leakage prevented: scaler fit requested for split %r",
                split_name,
            )
            raise ValueError(
                "Preprocessing scalers may only be fitted on split_name='train'"
            )
        matrix, columns = self._as_matrix(data)
        self.scaler.fit(matrix)
        self.fit_split = split_name
        self.feature_names = [str(column) for column in columns] if columns is not None else None
        dates = data.index if isinstance(data, pd.DataFrame) and isinstance(
            data.index, pd.DatetimeIndex
        ) else None
        self.fit_metadata = {
            'fit_split': split_name,
            'fit_rows': int(matrix.shape[0]),
            'feature_count': int(matrix.shape[1]),
            'feature_names': self.feature_names,
            'fit_start_date': dates.min().isoformat() if dates is not None and len(dates) else None,
            'fit_end_date': dates.max().isoformat() if dates is not None and len(dates) else None,
            'data_fingerprint': self._fingerprint(matrix, columns),
        }
        return self

    def transform(self, data: Any, split_name: Optional[str] = None):
        """Transform data using the frozen training statistics."""
        if self.fit_split != 'train':
            raise RuntimeError("Scaler must be fitted on training data before transform")
        matrix, columns = self._as_matrix(data)
        if matrix.shape[1] != self.scaler.n_features_in_:
            raise ValueError(
                f"Expected {self.scaler.n_features_in_} features, got {matrix.shape[1]}"
            )
        if self.feature_names is not None:
            actual_names = [str(column) for column in columns] if columns is not None else None
            if actual_names != self.feature_names:
                raise ValueError("Input feature names/order differ from training data")
        transformed = self.scaler.transform(matrix)
        if isinstance(data, pd.DataFrame):
            return pd.DataFrame(transformed, index=data.index, columns=data.columns)
        return transformed

    def fit_transform(self, data: Any, split_name: Optional[str] = None):
        """Fit on explicitly identified training data and transform it."""
        return self.fit(data, split_name=split_name).transform(data, split_name=split_name)

    @property
    def mean_(self) -> np.ndarray:
        return self.scaler.mean_

    @property
    def scale_(self) -> np.ndarray:
        return self.scaler.scale_

    @property
    def var_(self) -> np.ndarray:
        return self.scaler.var_

    @property
    def n_samples_seen_(self):
        return self.scaler.n_samples_seen_

    def get_params(self) -> dict[str, Any]:
        """Return fitted statistics and provenance as JSON-compatible data."""
        if self.fit_split != 'train':
            raise RuntimeError("Scaler has not been fitted on training data")
        return {
            **self.fit_metadata,
            'mean': self.mean_.tolist(),
            'variance': self.var_.tolist(),
            'scale': self.scale_.tolist(),
        }


class ArtifactManager:
    """Save, load, version, and audit preprocessing artifacts."""

    def __init__(
        self,
        artifacts_dir: str | Path = 'reproducibility_artifacts',
        version: str = 'v1',
        logger: Optional[logging.Logger] = None,
    ):
        if not re.fullmatch(r'v[1-9]\d*', version):
            raise ValueError("version must use the form v1, v2, ...")
        self.artifacts_dir = Path(artifacts_dir)
        self.version = version
        self.logger = logger or logging.getLogger(__name__)
        self.metadata_path = self.artifacts_dir / f'{version}_metadata.json'

    def _read_metadata(self) -> dict:
        if self.metadata_path.exists():
            with self.metadata_path.open(encoding='utf-8') as file:
                return json.load(file)
        return {
            'version': self.version,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'artifacts': {},
        }

    def _write_metadata(self, metadata: dict) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = self.metadata_path.with_suffix('.json.tmp')
        with temporary_path.open('w', encoding='utf-8') as file:
            json.dump(metadata, file, indent=2)
        temporary_path.replace(self.metadata_path)

    def save_scaler(self, scaler: TrainOnlyStandardScaler) -> str:
        """Persist a scaler that has been fitted on training data only."""
        if not isinstance(scaler, TrainOnlyStandardScaler):
            raise TypeError("save_scaler expects a TrainOnlyStandardScaler")
        scaler_metadata = scaler.get_params()
        if scaler_metadata['fit_split'] != 'train':
            raise ValueError("Refusing to save a scaler not fitted on training data")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = self.artifacts_dir / f'{self.version}_scaler.pkl'
        joblib.dump(scaler, artifact_path)
        metadata = self._read_metadata()
        metadata['artifacts']['scaler'] = {
            'path': artifact_path.name,
            'type': 'TrainOnlyStandardScaler',
            'fitted_on': 'train',
            'fitted_at': datetime.now(timezone.utc).isoformat(),
            'parameters': scaler_metadata,
        }
        self._write_metadata(metadata)
        return str(artifact_path)

    def load_scaler(self) -> TrainOnlyStandardScaler:
        """Load the current version's fitted scaler."""
        artifact_path = self.artifacts_dir / f'{self.version}_scaler.pkl'
        if not artifact_path.exists():
            raise FileNotFoundError(f"Scaler artifact not found: {artifact_path}")
        scaler = joblib.load(artifact_path)
        if not isinstance(scaler, TrainOnlyStandardScaler):
            raise TypeError(f"Unexpected scaler artifact type: {type(scaler).__name__}")
        if scaler.fit_split != 'train':
            raise ValueError("Loaded scaler provenance does not indicate training-only fit")
        return scaler

    def save_kalman_params(self, params: dict[str, Any]) -> str:
        """Persist fitted Kalman parameters as a versioned artifact."""
        if not isinstance(params, dict) or not params:
            raise ValueError("params must be a non-empty dictionary")
        fit_split = params.get('fit_split')
        if fit_split != 'train':
            self.logger.critical(
                "Preprocessing leakage prevented: Kalman params have fit_split=%r",
                fit_split,
            )
            raise ValueError("Kalman parameters must be fitted on training data only")
        artifact_path = self.artifacts_dir / f'{self.version}_kalman_params.pkl'
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(params, artifact_path)
        metadata = self._read_metadata()
        metadata['artifacts']['kalman_params'] = {
            'path': artifact_path.name,
            'fitted_on': fit_split or 'train',
            'fitted_at': datetime.now(timezone.utc).isoformat(),
        }
        self._write_metadata(metadata)
        return str(artifact_path)

    def load_kalman_params(self) -> dict[str, Any]:
        """Load versioned Kalman parameters."""
        artifact_path = self.artifacts_dir / f'{self.version}_kalman_params.pkl'
        if not artifact_path.exists():
            raise FileNotFoundError(f"Kalman parameter artifact not found: {artifact_path}")
        params = joblib.load(artifact_path)
        if not isinstance(params, dict):
            raise TypeError("Kalman parameter artifact must contain a dictionary")
        return params

    def verify_no_leakage(
        self,
        scaler: TrainOnlyStandardScaler,
        train_data: Any,
        validation_data: Any = None,
        test_data: Any = None,
    ) -> bool:
        """Check scaler provenance against train data and flag suspicious refits.

        A scaler must have an explicit training fit role and statistics matching
        a fresh fit on the provided training sample. Identical independently
        fitted validation/test statistics are warned about as possible leakage,
        as requested by the project specification.
        """
        if not isinstance(scaler, TrainOnlyStandardScaler) or scaler.fit_split != 'train':
            message = "Scaler leakage detected: scaler was not fitted on training data"
            self.logger.critical(message)
            raise ValueError(message)
        train_matrix, train_columns = scaler._as_matrix(train_data)
        if scaler.fit_metadata.get('data_fingerprint') != scaler._fingerprint(
            train_matrix, train_columns
        ):
            message = "Scaler leakage detected: fitted data does not match training data"
            self.logger.critical(message)
            raise ValueError(message)
        if scaler.fit_metadata.get('fit_rows') != train_matrix.shape[0]:
            message = "Scaler leakage detected: fitted row count differs from training data"
            self.logger.critical(message)
            raise ValueError(message)
        training_scaler = StandardScaler().fit(train_matrix)
        if not (
            np.allclose(scaler.mean_, training_scaler.mean_, rtol=1e-9, atol=1e-12)
            and np.allclose(scaler.scale_, training_scaler.scale_, rtol=1e-9, atol=1e-12)
        ):
            message = "Scaler statistics do not match a fit on training data"
            self.logger.critical(message)
            raise ValueError(message)

        for split_name, split_data in (
            ('validation', validation_data), ('test', test_data)
        ):
            if split_data is None:
                continue
            split_matrix, split_columns = scaler._as_matrix(split_data)
            if split_columns is not None and scaler.feature_names is not None:
                if [str(name) for name in split_columns] != scaler.feature_names:
                    raise ValueError(f"{split_name} feature names/order differ from training data")
            comparison_scaler = StandardScaler().fit(split_matrix)
            same_mean = np.allclose(scaler.mean_, comparison_scaler.mean_, rtol=1e-9, atol=1e-12)
            same_scale = np.allclose(scaler.scale_, comparison_scaler.scale_, rtol=1e-9, atol=1e-12)
            if same_mean and same_scale:
                warnings.warn(
                    f"Scaler parameters exactly match a refit on {split_name} data; "
                    "possible preprocessing leakage or identical distributions.",
                    RuntimeWarning,
                    stacklevel=2,
                )
        return True