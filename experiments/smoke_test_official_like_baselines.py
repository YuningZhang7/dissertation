from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_official_like_baselines import (
    BASELINE_AGENT_NAMES,
    CSV_COLUMNS,
    run_baseline_experiment,
)


def test_baseline_outputs_have_required_structure_and_are_deterministic() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        first_csv = temp_path / "first.csv"
        first_summary_path = temp_path / "first_summary.json"
        second_csv = temp_path / "second.csv"
        second_summary_path = temp_path / "second_summary.json"

        first_rows, first_summary = run_baseline_experiment(
            episodes_per_agent=2,
            max_steps_per_episode=80,
            base_seed=42,
            output_csv=first_csv,
            output_summary=first_summary_path,
        )
        second_rows, second_summary = run_baseline_experiment(
            episodes_per_agent=2,
            max_steps_per_episode=80,
            base_seed=42,
            output_csv=second_csv,
            output_summary=second_summary_path,
        )

        assert first_csv.exists()
        assert first_summary_path.exists()
        assert second_csv.exists()
        assert second_summary_path.exists()
        assert first_rows == second_rows
        assert first_summary == second_summary

        with first_csv.open("r", newline="", encoding="utf-8") as file:
            csv_rows = list(csv.DictReader(file))
        with first_summary_path.open("r", encoding="utf-8") as file:
            summary_data = json.load(file)

        assert len(csv_rows) == len(BASELINE_AGENT_NAMES) * 2
        assert set(CSV_COLUMNS).issubset(csv_rows[0])
        assert {row["agent_name"] for row in csv_rows} == set(BASELINE_AGENT_NAMES)
        assert set(summary_data) == set(BASELINE_AGENT_NAMES)
        assert "objective_aware_greedy" in summary_data
        assert "urbanization_aware_lookahead_greedy" in summary_data
        assert all("success" in row for row in first_rows)
        assert all(
            row["final_score"] != ""
            and row["bonds"] != ""
            and row["delivered_goods_count"] != ""
            for row in csv_rows
        )
        assert all(summary_data[name]["episodes"] == 2 for name in BASELINE_AGENT_NAMES)


def run_all() -> None:
    tests = [test_baseline_outputs_have_required_structure_and_are_deterministic]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} official-like baseline smoke tests passed.")


if __name__ == "__main__":
    run_all()
