"""Tests for train-only preprocessing artifacts and leakage safeguards."""

import json

import numpy as np
import pandas as pd
import pytest

from preprocessing.artifact_manager import ArtifactManager, TrainOnlyStandardScaler


@pytest.fixture
def partitions():
    train_index = pd.date_range('2024-01-01', periods=4, freq='D')
    validation_index = pd.date_range('2024-01-05', periods=2, freq='D')
    test_index = pd.date_range('2024-01-07', periods=2, freq='D')
    train = pd.DataFrame(
        {'return': [0.0, 1.0, 2.0, 3.0], 'volume': [10.0, 20.0, 30.0, 40.0]},
        index=train_index,
    )
    validation = pd.DataFrame(
        {'return': [4.0, 5.0], 'volume': [50.0, 60.0]}, index=validation_index
    )
    test = pd.DataFrame(
        {'return': [6.0, 7.0], 'volume': [70.0, 80.0]}, index=test_index
    )
    return train, validation, test


def test_fit_requires_explicit_training_split(partitions, caplog):
    train, validation, _ = partitions
    scaler = TrainOnlyStandardScaler()

    with pytest.raises(ValueError, match="split_name='train'"):
        scaler.fit(validation, split_name='validation')
    with pytest.raises(ValueError, match="split_name='train'"):
        scaler.fit(train)
    assert 'CRITICAL' in caplog.text


def test_validation_and_test_are_transformed_without_refitting(partitions):
    train, validation, test = partitions
    scaler = TrainOnlyStandardScaler().fit(train, split_name='train')
    train_mean = scaler.mean_.copy()
    train_scale = scaler.scale_.copy()
    expected_validation = (validation - train.mean()) / train.std(ddof=0)

    scaled_validation = scaler.transform(validation, split_name='validation')
    scaled_test = scaler.transform(test, split_name='test')

    pd.testing.assert_frame_equal(scaled_validation, expected_validation)
    assert scaled_test.index.equals(test.index)
    np.testing.assert_array_equal(scaler.mean_, train_mean)
    np.testing.assert_array_equal(scaler.scale_, train_scale)
    assert scaler.fit_metadata['fit_split'] == 'train'
    assert scaler.fit_metadata['fit_rows'] == len(train)
    assert scaler.fit_metadata['fit_start_date'] == train.index.min().isoformat()
    assert scaler.fit_metadata['fit_end_date'] == train.index.max().isoformat()


def test_artifact_manager_round_trips_versioned_scaler_and_kalman_params(
    tmp_path, partitions
):
    train, validation, test = partitions
    scaler = TrainOnlyStandardScaler().fit(train, split_name='train')
    manager = ArtifactManager(tmp_path, version='v3')

    scaler_path = manager.save_scaler(scaler)
    kalman_path = manager.save_kalman_params({
        'process_variance': 0.01,
        'measurement_variance': 0.1,
        'fit_split': 'train',
    })
    loaded = manager.load_scaler()
    loaded_kalman = manager.load_kalman_params()
    metadata = json.loads((tmp_path / 'v3_metadata.json').read_text(encoding='utf-8'))

    assert scaler_path.endswith('v3_scaler.pkl')
    assert kalman_path.endswith('v3_kalman_params.pkl')
    np.testing.assert_array_equal(loaded.mean_, scaler.mean_)
    pd.testing.assert_frame_equal(
        loaded.transform(validation), scaler.transform(validation)
    )
    pd.testing.assert_frame_equal(loaded.transform(test), scaler.transform(test))
    assert loaded_kalman['fit_split'] == 'train'
    assert metadata['version'] == 'v3'
    assert metadata['artifacts']['scaler']['fitted_on'] == 'train'
    assert metadata['artifacts']['scaler']['parameters']['fit_rows'] == len(train)
    assert metadata['artifacts']['kalman_params']['path'] == 'v3_kalman_params.pkl'


def test_leakage_verification_confirms_train_fingerprint(partitions, tmp_path):
    train, validation, test = partitions
    scaler = TrainOnlyStandardScaler().fit(train, split_name='train')
    manager = ArtifactManager(tmp_path)

    assert manager.verify_no_leakage(scaler, train, validation, test)
    altered_train = train.copy()
    altered_train.iloc[0, 0] += 10
    with pytest.raises(ValueError, match='does not match training data'):
        manager.verify_no_leakage(scaler, altered_train)


def test_identical_validation_refit_is_flagged_as_suspicious(tmp_path):
    dates = pd.date_range('2024-01-01', periods=4, freq='D')
    train = pd.DataFrame({'feature': [1.0, 2.0, 3.0, 4.0]}, index=dates)
    scaler = TrainOnlyStandardScaler().fit(train, split_name='train')
    manager = ArtifactManager(tmp_path)

    with pytest.warns(RuntimeWarning, match='possible preprocessing leakage'):
        assert manager.verify_no_leakage(scaler, train, validation_data=train.copy())


def test_artifact_manager_rejects_non_training_kalman_params(tmp_path):
    manager = ArtifactManager(tmp_path)

    with pytest.raises(ValueError, match='training data only'):
        manager.save_kalman_params({'fit_split': 'validation', 'noise': 0.1})
    with pytest.raises(ValueError, match='training data only'):
        manager.save_kalman_params({'noise': 0.1})


def test_leakage_verification_rejects_altered_scaler_statistics(partitions, tmp_path):
    train, _, _ = partitions
    scaler = TrainOnlyStandardScaler().fit(train, split_name='train')
    scaler.scaler.mean_[0] += 1

    with pytest.raises(ValueError, match='do not match a fit on training data'):
        ArtifactManager(tmp_path).verify_no_leakage(scaler, train)