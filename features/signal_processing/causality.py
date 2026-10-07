"""Future-perturbation causality checks for signal-processing modules."""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from features.base_features import FeatureModule


class SignalProcessingCausalityChecker:
    """Detect future-data dependence by perturbing rows after sample cutoffs."""

    def check(
        self,
        module: FeatureModule,
        df: pd.DataFrame,
        check_points: int = 3,
        tolerance: float = 1e-10,
        fit_data: Optional[pd.DataFrame] = None
    ) -> Tuple[bool, List[str]]:
        """Compare feature prefixes before and after changing future observations.

        Parameters
        ----------
        module : FeatureModule
            Module to test. Its ``compute`` method must be deterministic.
        df : pd.DataFrame
            Time-indexed input data.
        check_points : int, default=3
            Number of cutoff positions selected across the input.
        tolerance : float, default=1e-10
            Absolute and relative numerical comparison tolerance.
        fit_data : pd.DataFrame, optional
            Fit data forwarded unchanged to each computation.

        Returns
        -------
        tuple[bool, list[str]]
            Whether the tested output prefixes are invariant and any issues.
        """
        if df is None or len(df) < 2:
            return False, ["At least two rows are required for a causality check"]
        if check_points < 1:
            return False, ["check_points must be positive"]

        baseline = module.compute(df, fit_data=fit_data)
        cutoff_count = min(check_points, len(df) - 1)
        cutoffs = np.unique(np.linspace(
            0, len(df) - 2, num=cutoff_count, dtype=int
        ))
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        issues = []

        for cutoff in cutoffs:
            perturbed = df.copy(deep=True)
            future = perturbed.index[int(cutoff) + 1:]
            if len(numeric_columns) == 0:
                return False, ["Input data has no numeric columns to perturb"]
            perturbed.loc[future, numeric_columns] *= 1.137
            changed = module.compute(perturbed, fit_data=fit_data)

            try:
                assert_frame_equal(
                    baseline.iloc[:int(cutoff) + 1],
                    changed.iloc[:int(cutoff) + 1],
                    check_dtype=False,
                    check_exact=False,
                    rtol=tolerance,
                    atol=tolerance,
                )
            except AssertionError:
                issues.append(
                    f"Output through row {int(cutoff)} changed after future data was perturbed"
                )

        return not issues, issues