from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd


class AblationReporter:
    """Convert ablation run results into a human-readable summary."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_report(
        self,
        results: dict,
        report_path: str | Path = "results/ablation/ablation_results.json",
        summary_csv_path: str | Path = "results/ablation/ablation_summary_table.csv",
    ) -> dict:
        if not results:
            raise ValueError("results must not be empty")

        summary_rows = []
        for ablation in results.get("ablations", []):
            summary_rows.append(
                {
                    "ablation_name": ablation.get("name"),
                    "description": ablation.get("description", ""),
                    "removed_columns": "; ".join(ablation.get("removed_columns", [])),
                    "validation_mae": ablation.get("validation_metrics", {}).get("mae"),
                    "validation_rmse": ablation.get("validation_metrics", {}).get("rmse"),
                    "test_mae": ablation.get("test_metrics", {}).get("mae"),
                    "test_rmse": ablation.get("test_metrics", {}).get("rmse"),
                    "delta_test_mae": ablation.get("delta_test", {}).get("mae"),
                    "delta_test_rmse": ablation.get("delta_test", {}).get("rmse"),
                    "validation_p_value": ablation.get("significance", {}).get("validation_p_value"),
                    "test_p_value": ablation.get("significance", {}).get("test_p_value"),
                }
            )

        summary = {
            "generated_at": pd.Timestamp.utcnow().isoformat(),
            "baseline": results.get("baseline", {}),
            "ablations": summary_rows,
        }

        report_output = Path(report_path)
        report_output.parent.mkdir(parents=True, exist_ok=True)
        with report_output.open("w", encoding="utf-8") as file:
            json.dump(summary, file, indent=2, default=str)

        table_output = Path(summary_csv_path)
        table_output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(summary_rows).to_csv(table_output, index=False)

        self.logger.info("Saved ablation report to %s and summary CSV to %s", report_output, table_output)
        return summary


__all__ = ["AblationReporter"]
