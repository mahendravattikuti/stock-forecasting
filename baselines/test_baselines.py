"""Tests for baseline estimators and orchestration."""

import json

import numpy as np
import pandas as pd
import pytest

from baselines import (
    ARIMABaseline,
    BaselineManager,
    HistoricalMeanBaseline,
    LinearRegressionBaseline,
    RandomWalkBaseline,
    RidgeRegressionBaseline,
)


@pytest.fixture
def sample_splits():
    rng = np.random.default_rng(91)
    train_index = pd.date_range('2020-01-01', periods=100, freq='D')
    validation_index = pd.date_range('2020-04-10', periods=20, freq='D')
    test_index = pd.date_range('2020-04-30', periods=20, freq='D')

    def make_features(index):
        return pd.DataFrame({
            'simple_return': rng.normal(0, 0.01, len(index)),
            'momentum_5': rng.normal(0, 0.02, len(index)),
        }, index=index)

    X_train = make_features(train_index)
    X_validation = make_features(validation_index)
    X_test = make_features(test_index)
    weights = np.array([0.4, -0.2])
    y_train = pd.Series(X_train.to_numpy() @ weights + rng.normal(0, 0.001, 100), index=train_index)
    y_validation = pd.Series(X_validation.to_numpy() @ weights, index=validation_index)
    y_test = pd.Series(X_test.to_numpy() @ weights, index=test_index)
    close_train = pd.Series(100 * np.exp(y_train.cumsum()), index=train_index)
    close_validation = pd.Series(
        close_train.iloc[-1] * np.exp(y_validation.cumsum()), index=validation_index
    )
    close_test = pd.Series(
        close_validation.iloc[-1] * np.exp(y_test.cumsum()), index=test_index
    )
    return {
        'y_train': y_train,
        'y_validation': y_validation,
        'y_test': y_test,
        'X_train': X_train,
        'X_validation': X_validation,
        'X_test': X_test,
        'close_train': close_train,
        'close_validation': close_validation,
        'close_test': close_test,
    }


def test_base_metrics_compute_mae_rmse_and_direction():
    model = HistoricalMeanBaseline()

    metrics = model.evaluate([1.0, -1.0, 0.0], [0.5, -0.5, 1.0])

    assert metrics['mae'] == pytest.approx(2 / 3)
    assert metrics['rmse'] == pytest.approx(np.sqrt(0.5))
    assert metrics['directional_accuracy'] == pytest.approx(2 / 3)


def test_random_walk_and_historical_mean_predictions():
    history = np.array([0.01, -0.02, 0.03])
    random_walk = RandomWalkBaseline().fit(history)
    mean_model = HistoricalMeanBaseline().fit(history)

    np.testing.assert_allclose(random_walk.predict(steps=2), [0.03, 0.03])
    np.testing.assert_allclose(
        random_walk.predict(current_values=[-0.01, 0.02]), [-0.01, 0.02]
    )
    np.testing.assert_allclose(mean_model.predict(steps=3), np.mean(history))


def test_regression_models_fit_and_report_parameters(sample_splits):
    data = sample_splits
    linear = LinearRegressionBaseline().fit(data['y_train'], data['X_train'])
    ridge = RidgeRegressionBaseline(
        alphas=[0.001, 0.01, 0.1, 1.0, 10.0], cv=5
    ).fit(data['y_train'], data['X_train'])

    linear_predictions = linear.predict(data['X_validation'])
    ridge_predictions = ridge.predict(data['X_validation'])
    assert len(linear_predictions) == len(data['y_validation'])
    assert len(ridge_predictions) == len(data['y_validation'])
    assert set(linear.coefficient_interpretation()['coefficients']) == {
        'simple_return', 'momentum_5'
    }
    assert ridge.best_alpha in [0.001, 0.01, 0.1, 1.0, 10.0]


def test_ridge_alpha_can_be_selected_on_validation(sample_splits):
    data = sample_splits
    ridge = RidgeRegressionBaseline(
        alphas=[0.001, 0.01, 0.1, 1.0, 10.0], cv=5
    ).fit(
        data['y_train'], data['X_train'],
        X_validation=data['X_validation'], y_validation=data['y_validation'],
    )

    assert ridge.tuning_split == 'validation'
    assert ridge.best_alpha in ridge.validation_scores
    assert ridge.cv_best_alpha in [0.001, 0.01, 0.1, 1.0, 10.0]


def test_arima_fits_training_closes_and_forecasts(sample_splits):
    data = sample_splits
    model = ARIMABaseline().fit(
        data['y_train'], close_train=data['close_train']
    )

    forecast = model.predict(steps=5)

    assert model.order == (1, 1, 1)
    assert len(forecast) == 5
    assert np.isfinite(forecast).all()


def test_baseline_manager_trains_evaluates_and_saves_every_model(sample_splits, tmp_path):
    data = sample_splits
    config = {'ridge_alphas': [0.001, 0.1, 1.0, 10.0], 'ridge_cv': 5}
    data['X_tier1_train'] = data['X_train'][['simple_return']]
    data['X_tier1_validation'] = data['X_validation'][['simple_return']]
    data['X_tier1_test'] = data['X_test'][['simple_return']]
    results_path = tmp_path / 'reports' / 'baseline_results.json'
    manager = BaselineManager(model_dir=tmp_path / 'models', config=config)

    results = manager.train_and_evaluate_all(
        **data,
        results_path=results_path,
    )

    expected_names = {
        'random_walk', 'arima_111', 'linear_regression',
        'ridge_regression', 'historical_mean',
    }
    assert set(results['models']) == expected_names
    assert set(manager.models) == expected_names
    assert config['ridge_best_alpha'] in config['ridge_alphas']
    assert results['models']['arima_111']['metadata']['fitted_on'] == 'train'
    assert results['models']['ridge_regression']['metadata']['feature_set_used'] == [
        'simple_return', 'momentum_5'
    ]
    assert results['models']['linear_regression']['metadata']['feature_set_used'] == [
        'simple_return'
    ]
    assert results['models']['ridge_regression']['metadata']['hyperparameters'][
        'tuning_split'
    ] == 'validation'
    for name in expected_names:
        assert (tmp_path / 'models' / f'{name}.joblib').exists()
        assert (tmp_path / 'models' / f'{name}_metadata.json').exists()
        assert len(results['models'][name]['validation_predictions']) == 20
        assert len(results['models'][name]['test_predictions']) == 20
        assert set(results['models'][name]['test']) == {
            'mae', 'rmse', 'directional_accuracy'
        }
    persisted = json.loads(results_path.read_text(encoding='utf-8'))
    assert persisted['target'] == 'one-step-ahead returns'
    assert set(persisted['models']) == expected_names


def test_manager_rejects_feature_target_date_mismatch(sample_splits, tmp_path):
    data = sample_splits
    data['X_validation'] = data['X_validation'].set_axis(
        data['X_validation'].index + pd.Timedelta(days=1)
    )
    manager = BaselineManager(model_dir=tmp_path / 'models')

    with pytest.raises(ValueError, match='indices do not match'):
        manager.train_and_evaluate_all(**data, results_path=tmp_path / 'results.json')