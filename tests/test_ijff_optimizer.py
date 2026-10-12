import numpy as np

from optimization.ijff_optimizer import optimize_objective


def sphere_objective(x):
    return float(np.sum(np.square(x)))


def rosenbrock_objective(x):
    x = np.asarray(x, dtype=float)
    return float(np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2))


def test_optimizer_finds_sphere_minimum():
    bounds = [(-5.0, 5.0)] * 3
    result = optimize_objective(
        sphere_objective,
        bounds,
        population_size=16,
        max_generations=80,
        random_state=7,
    )

    assert np.isfinite(result.best_value)
    assert np.all(result.best_position >= np.asarray([-5.0, -5.0, -5.0]))
    assert np.all(result.best_position <= np.asarray([5.0, 5.0, 5.0]))
    assert result.best_value < 0.5


def test_optimizer_handles_bounds_and_robustness():
    bounds = [(-2.0, 2.0), (-2.0, 2.0)]
    result = optimize_objective(
        rosenbrock_objective,
        bounds,
        population_size=18,
        max_generations=120,
        random_state=5,
    )

    assert np.isfinite(result.best_value)
    assert np.all(result.best_position >= np.asarray([-2.0, -2.0]))
    assert np.all(result.best_position <= np.asarray([2.0, 2.0]))
    assert result.best_value < 5.0
