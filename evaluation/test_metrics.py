"""Tests for evaluation metrics and bootstrap confidence intervals."""

import numpy as np
import pytest

from evaluation import (
    BootstrapConfidenceIntervals,
    EvaluationMetrics,
    MetricsComputer,
)


def test_error_and_direction_metrics_match_hand_calculation():
    actual = np.array([1.0, -1.0, 0.0])
    predicted = np.array([0.5, -0.5, 1.0])

    assert EvaluationMetrics.mae(actual, predicted) == pytest.approx(2 / 3)
    assert EvaluationMetrics.rmse(actual, predicted) == pytest.approx(np.sqrt(0.5))
    assert EvaluationMetrics.directional_accuracy(actual, predicted) == pytest.approx(2 / 3)


def test_mape_ignores_zero_actuals_and_handles_all_zero_case():
    assert EvaluationMetrics.mape([0.0, 2.0, -4.0], [10.0, 3.0, -2.0]) == pytest.approx(50.0)
    assert EvaluationMetrics.mape([0.0, 0.0], [0.0, 0.0]) == 0.0
    with pytest.raises(ValueError, match='every actual value is zero'):
        EvaluationMetrics.mape([0.0, 0.0], [0.0, 1.0])


def test_sharpe_and_information_coefficient_edge_cases():
    assert EvaluationMetrics.sharpe_ratio([0.0, 0.0]) == 0.0
    assert EvaluationMetrics.sharpe_ratio([0.1, 0.1]) is None
    assert EvaluationMetrics.sharpe_ratio([0.01, 0.02, 0.03]) == pytest.approx(
        np.mean([0.01, 0.02, 0.03]) / np.std([0.01, 0.02, 0.03])
    )
    assert EvaluationMetrics.information_coefficient([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert EvaluationMetrics.information_coefficient([1, 1, 1], [2, 3, 4]) is None


def test_metric_inputs_reject_mismatched_lengths_and_nonfinite_values():
    with pytest.raises(ValueError, match='same length'):
        EvaluationMetrics.mae([1, 2], [1])
    with pytest.raises(ValueError, match='finite'):
        EvaluationMetrics.rmse([1, np.nan], [1, 2])


def test_bootstrap_confidence_interval_is_paired_and_reproducible():
    actual = np.array([1.0, 2.0, 3.0, 4.0])
    predicted = np.array([1.1, 1.8, 3.2, 3.9])
    first = BootstrapConfidenceIntervals(n_bootstrap=300, random_state=17)
    second = BootstrapConfidenceIntervals(n_bootstrap=300, random_state=17)

    first_ci = first.compute_ci(EvaluationMetrics.mae, actual, predicted)
    second_ci = second.compute_ci(EvaluationMetrics.mae, actual, predicted)

    assert first_ci == second_ci
    assert first_ci['value'] == pytest.approx(0.15)
    assert first_ci['ci_lower'] <= first_ci['value'] <= first_ci['ci_upper']
    assert first_ci['valid_bootstrap_samples'] == 300


def test_bootstrap_omits_undefined_samples_and_validates_options():
    ci = BootstrapConfidenceIntervals(n_bootstrap=100, random_state=2).compute_ci(
        EvaluationMetrics.information_coefficient,
        [1.0, 1.0, 2.0], [2.0, 2.0, 3.0],
    )
    assert ci['value'] == 1.0
    assert ci['valid_bootstrap_samples'] <= 100

    with pytest.raises(ValueError, match='n_bootstrap'):
        BootstrapConfidenceIntervals(n_bootstrap=0)
    with pytest.raises(ValueError, match='confidence_level'):
        BootstrapConfidenceIntervals(confidence_level=1.0)


def test_metrics_computer_returns_all_metrics_with_95_percent_intervals():
    actual = np.array([0.01, -0.02, 0.005, 0.03, -0.01, 0.015])
    predicted = np.array([0.012, -0.01, 0.004, 0.02, -0.015, 0.01])
    computer = MetricsComputer(n_bootstrap=250, confidence_level=0.95, random_state=42)

    result = computer.compute_all_metrics(actual, predicted, split_name='test')

    assert result['split'] == 'test'
    assert result['sample_count'] == len(actual)
    assert result['confidence_level'] == 0.95
    assert result['bootstrap_samples'] == 250
    assert set(result['metrics']) == {
        'mae', 'rmse', 'mape', 'directional_accuracy',
        'sharpe_ratio', 'information_coefficient',
    }
    for metric in result['metrics'].values():
        assert {'value', 'ci_lower', 'ci_upper', 'valid_bootstrap_samples'} <= set(metric)
        if metric['value'] is not None:
            assert metric['ci_lower'] is not None
            assert metric['ci_upper'] is not None
    assert result['metrics']['mape']['zero_actuals_excluded'] == 0
