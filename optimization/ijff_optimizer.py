"""Improved Jellyfish Search with Firefly hybrid optimizer.

This module intentionally defines a generic optimizer that can later be used for
hyperparameter tuning, feature subset selection, or other numerical search
problems. The implementation is self-contained and does not depend on the
unfinished deep-learning stack in the broader project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

import numpy as np


ScalarObjective = Callable[[np.ndarray], float]


@dataclass
class ObjectiveResult:
    """Outcome of an optimization run."""

    best_position: np.ndarray
    best_value: float
    history: list[float] = field(default_factory=list)
    iterations: int = 0
    converged: bool = False


class FireflyJellyfishOptimizer:
    """Hybrid Improved Jellyfish Search + Firefly optimizer.

    The optimizer searches a bounded vector space for a candidate solution that
    minimizes a scalar objective. Bounds are provided as a sequence of
    ``(lower, upper)`` tuples and are enforced with clipping on every iteration.
    """

    def __init__(
        self,
        objective: ScalarObjective,
        bounds: Iterable[tuple[float, float]],
        *,
        population_size: int = 20,
        max_generations: int = 100,
        minimize: bool = True,
        alpha: float = 0.5,
        beta0: float = 1.0,
        gamma: float = 1.0,
        jellyfish_motion: float = 0.5,
        random_state: Optional[int] = None,
    ) -> None:
        self.objective = objective
        self.bounds = np.asarray(list(bounds), dtype=float)
        if self.bounds.ndim != 2 or self.bounds.shape[1] != 2:
            raise ValueError("bounds must be a sequence of (lower, upper) pairs")
        if population_size <= 0:
            raise ValueError("population_size must be positive")
        if max_generations <= 0:
            raise ValueError("max_generations must be positive")
        if not np.all(self.bounds[:, 0] <= self.bounds[:, 1]):
            raise ValueError("each lower bound must be <= corresponding upper bound")

        self.population_size = population_size
        self.max_generations = max_generations
        self.minimize = minimize
        self.alpha = float(alpha)
        self.beta0 = float(beta0)
        self.gamma = float(gamma)
        self.jellyfish_motion = float(jellyfish_motion)
        self.rng = np.random.default_rng(random_state)

    def _clip_candidate(self, candidate: np.ndarray) -> np.ndarray:
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]
        return np.clip(candidate, lower, upper)

    def _initial_population(self) -> np.ndarray:
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]
        return self.rng.uniform(lower, upper, size=(self.population_size, len(lower)))

    def _evaluate_population(self, population: np.ndarray) -> np.ndarray:
        scores = np.asarray([self.objective(candidate) for candidate in population], dtype=float)
        if scores.ndim != 1: raise ValueError("objective must return a scalar value for each candidate")
        if not np.all(np.isfinite(scores)):
            raise ValueError("objective values must be finite")
        return scores

    def _sort_population(self, population: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        order = np.argsort(scores)
        if not self.minimize:
            order = order[::-1]
        return population[order], scores[order]

    def _compute_firefly_step(self, candidate: np.ndarray, best: np.ndarray, distance: float) -> np.ndarray:
        if distance == 0.0:
            return candidate.copy()
        attractiveness = self.beta0 * np.exp(-self.gamma * distance**2)
        direction = best - candidate
        return candidate + attractiveness * direction + self.alpha * self.rng.normal(size=candidate.shape)

    def _compute_jellyfish_step(self, candidate: np.ndarray, best: np.ndarray) -> np.ndarray:
        direction = best - candidate
        drift = self.jellyfish_motion * self.rng.normal(size=candidate.shape)
        return candidate + self.jellyfish_motion * direction + drift

    def optimize(self) -> ObjectiveResult:
        """Run the optimizer and return the best candidate and its score."""
        population = self._initial_population()
        scores = self._evaluate_population(population)
        population, scores = self._sort_population(population, scores)

        best_candidate = population[0].copy()
        best_score = float(scores[0])
        history: list[float] = [best_score]

        for generation in range(1, self.max_generations + 1):
            elite_count = max(1, min(4, self.population_size // 5))
            elite_candidates = population[:elite_count].copy()
            elite_scores = scores[:elite_count].copy()
            new_population: list[np.ndarray] = []

            for i, candidate in enumerate(population):
                if i == 0:
                    new_candidate = candidate.copy()
                else:
                    leader = population[self.rng.integers(0, elite_count)]
                    partner = population[self.rng.integers(0, self.population_size)]
                    diff = partner - candidate
                    distance = np.linalg.norm(diff)

                    firefly_step = self.beta0 * np.exp(-self.gamma * (distance**2 + 1e-8)) * (leader - candidate)
                    jellyfish_step = self.jellyfish_motion * (leader - candidate)
                    random_step = self.alpha * self.rng.normal(size=candidate.shape)
                    if self.minimize:
                        if scores[i] > elite_scores[0]:
                            exploratory_step = self.rng.normal(scale=0.5, size=candidate.shape)
                        else:
                            exploratory_step = 0.1 * self.rng.normal(size=candidate.shape)
                    else:
                        if scores[i] < elite_scores[0]:
                            exploratory_step = self.rng.normal(scale=0.5, size=candidate.shape)
                        else:
                            exploratory_step = 0.1 * self.rng.normal(size=candidate.shape)

                    new_candidate = candidate + firefly_step + jellyfish_step + random_step + exploratory_step
                    new_candidate = self._clip_candidate(new_candidate)

                    if self.minimize:
                        candidate_score = float(self.objective(candidate))
                        trial_score = float(self.objective(new_candidate))
                        if trial_score > candidate_score:
                            noise = self.rng.normal(scale=0.25, size=candidate.shape)
                            new_candidate = self._clip_candidate(candidate + noise)
                    else:
                        candidate_score = float(self.objective(candidate))
                        trial_score = float(self.objective(new_candidate))
                        if trial_score < candidate_score:
                            noise = self.rng.normal(scale=0.25, size=candidate.shape)
                            new_candidate = self._clip_candidate(candidate + noise)

                new_population.append(new_candidate)

            new_population = np.asarray(new_population, dtype=float)
            new_scores = self._evaluate_population(new_population)
            population, scores = self._sort_population(new_population, new_scores)

            if self.minimize:
                if scores[0] < best_score:
                    best_candidate = population[0].copy()
                    best_score = float(scores[0])
            else:
                if scores[0] > best_score:
                    best_candidate = population[0].copy()
                    best_score = float(scores[0])

            history.append(best_score)
            if generation > 1 and abs(history[-2] - history[-1]) < 1e-10:
                break

        return ObjectiveResult(
            best_position=best_candidate.copy(),
            best_value=float(best_score),
            history=history,
            iterations=len(history) - 1,
            converged=abs(history[-1] - history[0]) < 1e-8,
        )


def optimize_objective(
    objective: ScalarObjective,
    bounds: Iterable[tuple[float, float]],
    *,
    population_size: int = 20,
    max_generations: int = 100,
    minimize: bool = True,
    alpha: float = 0.5,
    beta0: float = 1.0,
    gamma: float = 1.0,
    jellyfish_motion: float = 0.5,
    random_state: Optional[int] = None,
) -> ObjectiveResult:
    """Convenience wrapper for running the optimizer on a box-bounded search."""

    optimizer = FireflyJellyfishOptimizer(
        objective,
        bounds,
        population_size=population_size,
        max_generations=max_generations,
        minimize=minimize,
        alpha=alpha,
        beta0=beta0,
        gamma=gamma,
        jellyfish_motion=jellyfish_motion,
        random_state=random_state,
    )
    return optimizer.optimize()
