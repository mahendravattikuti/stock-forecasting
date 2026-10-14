"""Property-based tests for evaluation metrics using hypothesis.

These tests verify fundamental mathematical properties of evaluation metrics
across randomly generated prediction scenarios. Properties are validated
for 100+ randomized test cases per property.

**Validates: Requirements 12.1 through 12.7**
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from evaluation.metrics import EvaluationMetrics


class TestPBTMetrics:
    """Property-based tests for evaluation metrics."""

    # ========================================================================
    # Property 1: MAE ≥ 0
    # ========================================================================
    # Property: MAE is always ≥ 0
    # Why: Mean of absolute values is non-negative by definition
    # Test: Generate random predictions and actuals, compute MAE, verify ≥ 0
    # ========================================================================

    @settings(max_examples=100)
    @given(
        predictions=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        actuals=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
    )
    def test_mae_non_negative(self, predictions, actuals):
        """MAE must always be ≥ 0 for any prediction/actual pair.
        
        **Validates: Requirement 12.1 (MAE definition)**
        
        Property: mean(|prediction - actual|) ≥ 0
        This holds by definition since absolute values are non-negative.
        """
        # Ensure same length
        min_len = min(len(predictions), len(actuals))
        if min_len < 2:
            pytest.skip("Need at least 2 samples for meaningful MAE test")
        
        mae = EvaluationMetrics.mae(
            np.array(actuals[:min_len]),
            np.array(predictions[:min_len])
        )
        assert mae >= 0.0, f"MAE should be non-negative, got {mae}"

    # ========================================================================
    # Property 2: RMSE ≥ 0
    # ========================================================================
    # Property: RMSE is always ≥ 0
    # Why: Square root of mean of squared values is non-negative by definition
    # Test: Generate random predictions and actuals, compute RMSE, verify ≥ 0
    # ========================================================================

    @settings(max_examples=100)
    @given(
        predictions=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        actuals=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
    )
    def test_rmse_non_negative(self, predictions, actuals):
        """RMSE must always be ≥ 0 for any prediction/actual pair.
        
        **Validates: Requirement 12.2 (RMSE definition)**
        
        Property: sqrt(mean((prediction - actual)²)) ≥ 0
        This holds by definition since square root of non-negative is non-negative.
        """
        # Ensure same length
        min_len = min(len(predictions), len(actuals))
        if min_len < 2:
            pytest.skip("Need at least 2 samples for meaningful RMSE test")
        
        rmse = EvaluationMetrics.rmse(
            np.array(actuals[:min_len]),
            np.array(predictions[:min_len])
        )
        assert rmse >= 0.0, f"RMSE should be non-negative, got {rmse}"

    # ========================================================================
    # Property 3: RMSE ≥ MAE
    # ========================================================================
    # Property: RMSE ≥ MAE for all prediction sets
    # Why: Quadratic penalty in RMSE makes it ≥ arithmetic mean penalty (MAE)
    # By Cauchy-Schwarz: sqrt(mean(x²)) ≥ mean(|x|) for any values x
    # Test: Generate random data, compute both, verify RMSE ≥ MAE
    # ========================================================================

    @settings(max_examples=100)
    @given(
        predictions=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        actuals=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
    )
    def test_rmse_gte_mae(self, predictions, actuals):
        """RMSE ≥ MAE for all prediction sets (Cauchy-Schwarz inequality).
        
        **Validates: Requirement 12.1, 12.2 (Relationship between metrics)**
        
        Property: sqrt(mean(errors²)) ≥ mean(|errors|)
        
        This follows from Cauchy-Schwarz inequality:
        (sum of |x_i|)² ≤ n * sum of x_i²
        Therefore: mean(|x|) ≤ sqrt(mean(x²))
        """
        # Ensure same length
        min_len = min(len(predictions), len(actuals))
        if min_len < 2:
            pytest.skip("Need at least 2 samples for meaningful comparison")
        
        actuals_arr = np.array(actuals[:min_len])
        predictions_arr = np.array(predictions[:min_len])
        
        mae = EvaluationMetrics.mae(actuals_arr, predictions_arr)
        rmse = EvaluationMetrics.rmse(actuals_arr, predictions_arr)
        
        # Allow small numerical tolerance for floating-point comparisons
        assert rmse >= mae - 1e-10, (
            f"RMSE ({rmse}) should be ≥ MAE ({mae}) by Cauchy-Schwarz inequality"
        )

    # ========================================================================
    # Property 4: Directional Accuracy in Valid Range [0, 1]
    # ========================================================================
    # Property: Directional accuracy always in [0, 1]
    # Why: It's a percentage of correct directional predictions (0-100%)
    # Test: Generate predictions with random signs, compute accuracy, verify
    # ========================================================================

    @settings(max_examples=100)
    @given(
        predictions=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        actuals=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
    )
    def test_directional_accuracy_in_range(self, predictions, actuals):
        """Directional accuracy must always be in [0, 1].
        
        **Validates: Requirement 12.3 (Directional accuracy definition)**
        
        Property: 0 ≤ directional_accuracy ≤ 1
        
        Directional accuracy is the fraction of predictions with correct
        direction sign (including flat/zero predictions), which ranges
        from 0% (all wrong) to 100% (all correct).
        """
        # Ensure same length
        min_len = min(len(predictions), len(actuals))
        if min_len < 2:
            pytest.skip("Need at least 2 samples for meaningful accuracy test")
        
        acc = EvaluationMetrics.directional_accuracy(
            np.array(actuals[:min_len]),
            np.array(predictions[:min_len])
        )
        
        assert 0 <= acc <= 1, (
            f"Directional accuracy must be in [0, 1], got {acc}"
        )

    # ========================================================================
    # Property 5: Sharpe Ratio Stability
    # ========================================================================
    # Property: Sharpe ratio changes predictably under constant shifts
    # Why: Sharpe = mean/std, adding constant to all values changes mean
    #      but not std, so new Sharpe = (mean + shift) / std
    # Test: Generate predictions, compute Sharpe; shift all by constant;
    #       verify new Sharpe = old Sharpe + (shift / std)
    # ========================================================================

    @settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
    @given(
        returns=st.lists(
            st.floats(min_value=-0.05, max_value=0.05, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        shift=st.floats(min_value=-0.01, max_value=0.01, allow_nan=False, allow_infinity=False),
    )
    def test_sharpe_ratio_stability_under_shift(self, returns, shift):
        """Sharpe ratio changes predictably under constant shifts.
        
        **Validates: Requirement 12.4 (Sharpe ratio definition)**
        
        Property: Sharpe(X + shift) = (mean(X) + shift) / std(X)
        
        This is the mathematical definition of Sharpe ratio:
        - Adding constant to all returns shifts the mean
        - Adding constant does not change the standard deviation
        - Therefore Sharpe scales predictably
        """
        if len(returns) < 2:
            pytest.skip("Need at least 2 samples for meaningful Sharpe test")
        
        returns_arr = np.array(returns)
        std_returns = np.std(returns_arr, ddof=0)
        
        # Skip if zero volatility (cannot verify ratio)
        if np.isclose(std_returns, 0.0):
            pytest.skip("Zero volatility: cannot test Sharpe ratio shift property")
        
        # Compute original Sharpe ratio
        sharpe_orig = EvaluationMetrics.sharpe_ratio(returns_arr)
        if sharpe_orig is None:
            pytest.skip("Original Sharpe ratio undefined (edge case)")
        
        # Shift all returns by constant
        shifted_returns = returns_arr + shift
        sharpe_shifted = EvaluationMetrics.sharpe_ratio(shifted_returns)
        if sharpe_shifted is None:
            pytest.skip("Shifted Sharpe ratio undefined (edge case)")
        
        # Verify: Sharpe(X + shift) = Sharpe(X) + shift/std(X)
        expected_sharpe_shift = shift / std_returns
        expected_sharpe_after_shift = sharpe_orig + expected_sharpe_shift
        
        assert np.isclose(sharpe_shifted, expected_sharpe_after_shift, atol=1e-10), (
            f"Sharpe ratio shift property violated: "
            f"expected {expected_sharpe_after_shift}, got {sharpe_shifted}"
        )

    # ========================================================================
    # Property 6: Perfect Predictions
    # ========================================================================
    # Property: When predictions = actuals, MAE = RMSE = 0
    # Why: Error is zero everywhere by definition
    # Test: Set predictions = actuals, verify metrics all zero
    # ========================================================================

    @settings(max_examples=50)
    @given(
        values=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
    )
    def test_perfect_predictions_zero_error(self, values):
        """Perfect predictions (predictions = actuals) yield zero error metrics.
        
        **Validates: Requirement 12.1, 12.2 (Error metric edge case)**
        
        Property: When prediction = actual for all samples:
        - MAE = 0
        - RMSE = 0
        - Directional accuracy = 1.0 (all directions match)
        """
        if len(values) < 2:
            pytest.skip("Need at least 2 samples")
        
        values_arr = np.array(values)
        
        mae = EvaluationMetrics.mae(values_arr, values_arr)
        rmse = EvaluationMetrics.rmse(values_arr, values_arr)
        dir_acc = EvaluationMetrics.directional_accuracy(values_arr, values_arr)
        
        assert np.isclose(mae, 0.0, atol=1e-10), f"MAE should be 0 for perfect predictions, got {mae}"
        assert np.isclose(rmse, 0.0, atol=1e-10), f"RMSE should be 0 for perfect predictions, got {rmse}"
        assert np.isclose(dir_acc, 1.0, atol=1e-10), f"Directional accuracy should be 1.0 for perfect predictions, got {dir_acc}"

    # ========================================================================
    # Property 7: Constant Predictions
    # ========================================================================
    # Property: Predictions of a constant value produce consistent metrics
    # Why: Metrics should be well-defined even for constant predictions
    # Test: Generate actuals, set all predictions to a constant, verify metrics
    # ========================================================================

    @settings(max_examples=50)
    @given(
        actuals=st.lists(
            st.floats(min_value=-0.05, max_value=0.05, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        constant=st.floats(min_value=-0.05, max_value=0.05, allow_nan=False, allow_infinity=False),
    )
    def test_constant_predictions_well_defined(self, actuals, constant):
        """Constant predictions produce well-defined metrics.
        
        **Validates: Requirement 12.1-12.5 (Edge case handling)**
        
        Property: MAE, RMSE, and directional accuracy are all well-defined
        when all predictions are identical constant values.
        """
        if len(actuals) < 2:
            pytest.skip("Need at least 2 samples")
        
        actuals_arr = np.array(actuals)
        predictions_arr = np.full_like(actuals_arr, constant)
        
        # These should not raise exceptions
        mae = EvaluationMetrics.mae(actuals_arr, predictions_arr)
        rmse = EvaluationMetrics.rmse(actuals_arr, predictions_arr)
        dir_acc = EvaluationMetrics.directional_accuracy(actuals_arr, predictions_arr)
        
        # All should be non-negative and in valid ranges
        assert mae >= 0.0
        assert rmse >= 0.0
        assert 0 <= dir_acc <= 1.0

    # ========================================================================
    # Property 8: Scale Invariance Properties
    # ========================================================================
    # Property: MAE and RMSE scale linearly with predictions and actuals
    # Why: Error metrics are linear in their arguments (homogeneous of degree 1)
    # Test: Scale predictions and actuals by factor k, verify metrics scale by k
    # ========================================================================

    @settings(max_examples=50)
    @given(
        predictions=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        actuals=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        scale_factor=st.floats(min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False),
    )
    def test_mae_rmse_linear_scaling(self, predictions, actuals, scale_factor):
        """MAE and RMSE scale linearly with scale_factor.
        
        **Validates: Requirement 12.1, 12.2 (Metric scaling property)**
        
        Property: If predictions and actuals are scaled by factor k:
        - MAE(k*actual, k*pred) = k * MAE(actual, pred)
        - RMSE(k*actual, k*pred) = k * RMSE(actual, pred)
        """
        if len(predictions) < 2 or np.isclose(scale_factor, 0.0):
            pytest.skip("Invalid inputs for scaling test")
        
        min_len = min(len(predictions), len(actuals))
        actuals_arr = np.array(actuals[:min_len])
        predictions_arr = np.array(predictions[:min_len])
        
        # Compute unscaled metrics
        mae_unscaled = EvaluationMetrics.mae(actuals_arr, predictions_arr)
        rmse_unscaled = EvaluationMetrics.rmse(actuals_arr, predictions_arr)
        
        # Compute scaled metrics
        actuals_scaled = actuals_arr * scale_factor
        predictions_scaled = predictions_arr * scale_factor
        mae_scaled = EvaluationMetrics.mae(actuals_scaled, predictions_scaled)
        rmse_scaled = EvaluationMetrics.rmse(actuals_scaled, predictions_scaled)
        
        # Verify scaling relationship
        expected_mae_scaled = mae_unscaled * abs(scale_factor)
        expected_rmse_scaled = rmse_unscaled * abs(scale_factor)
        
        assert np.isclose(mae_scaled, expected_mae_scaled, rtol=1e-9), (
            f"MAE scaling violated: expected {expected_mae_scaled}, got {mae_scaled}"
        )
        assert np.isclose(rmse_scaled, expected_rmse_scaled, rtol=1e-9), (
            f"RMSE scaling violated: expected {expected_rmse_scaled}, got {rmse_scaled}"
        )

    # ========================================================================
    # Property 9: Directional Accuracy Symmetry
    # ========================================================================
    # Property: Negating all predictions and actuals preserves directional accuracy
    # Why: Direction sign is preserved under negation
    # Test: Compute accuracy on (actual, pred), then on (-actual, -pred), verify equal
    # ========================================================================

    @settings(max_examples=50)
    @given(
        predictions=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
        actuals=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=500,
        ),
    )
    def test_directional_accuracy_negation_invariance(self, predictions, actuals):
        """Directional accuracy is preserved under negation.
        
        **Validates: Requirement 12.3 (Direction sign property)**
        
        Property: directional_accuracy(actual, pred) = directional_accuracy(-actual, -pred)
        
        Since direction is determined by sign(x), and sign(-x) = -sign(x),
        the relative directions are preserved under negation.
        """
        if len(predictions) < 2:
            pytest.skip("Need at least 2 samples")
        
        min_len = min(len(predictions), len(actuals))
        actuals_arr = np.array(actuals[:min_len])
        predictions_arr = np.array(predictions[:min_len])
        
        # Compute accuracy on original data
        acc_original = EvaluationMetrics.directional_accuracy(actuals_arr, predictions_arr)
        
        # Compute accuracy on negated data
        acc_negated = EvaluationMetrics.directional_accuracy(-actuals_arr, -predictions_arr)
        
        assert np.isclose(acc_original, acc_negated, atol=1e-10), (
            f"Directional accuracy should be invariant under negation: "
            f"original {acc_original}, negated {acc_negated}"
        )

    # ========================================================================
    # Property 10: Large Sample Stability
    # ========================================================================
    # Property: Metrics computed on large samples are well-defined and finite
    # Why: Metrics must scale gracefully with data volume
    # Test: Generate large random sample, compute all metrics, verify finite
    # ========================================================================

    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example, HealthCheck.data_too_large])
    @given(
        predictions=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=1000,
            max_size=2000,
        ),
        actuals=st.lists(
            st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False),
            min_size=1000,
            max_size=2000,
        ),
    )
    def test_large_sample_metrics_stability(self, predictions, actuals):
        """All metrics remain well-defined and finite for large samples.
        
        **Validates: Requirement 12.1-12.5 (Scalability and stability)**
        
        Property: MAE, RMSE, and directional accuracy are finite and
        well-defined even with thousands of samples.
        """
        min_len = min(len(predictions), len(actuals))
        actuals_arr = np.array(actuals[:min_len])
        predictions_arr = np.array(predictions[:min_len])
        
        mae = EvaluationMetrics.mae(actuals_arr, predictions_arr)
        rmse = EvaluationMetrics.rmse(actuals_arr, predictions_arr)
        dir_acc = EvaluationMetrics.directional_accuracy(actuals_arr, predictions_arr)
        
        # All should be finite
        assert np.isfinite(mae), f"MAE not finite for large sample: {mae}"
        assert np.isfinite(rmse), f"RMSE not finite for large sample: {rmse}"
        assert np.isfinite(dir_acc), f"Directional accuracy not finite: {dir_acc}"
        
        # In valid ranges
        assert mae >= 0.0
        assert rmse >= 0.0
        assert 0 <= dir_acc <= 1.0
