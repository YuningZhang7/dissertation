from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_agent_benchmark import CSV_COLUMNS, run_benchmark


def test_quick_agent_benchmark_outputs() -> None:
    agents = [
        "route_segment_greedy",
        "objective_aware_greedy",
        "adaptive_objective_greedy",
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        rows, summary, output = run_benchmark(
            maps=["official_like"],
            agents=agents,
            episodes=2,
            max_steps=10,
            base_seed=42,
            output_dir=temp_dir,
        )
        csv_path = output / "benchmark_rows.csv"
        json_path = output / "benchmark_summary.json"
        markdown_path = output / "benchmark_summary.md"
        assert csv_path.exists() and json_path.exists() and markdown_path.exists()
        with csv_path.open(newline="", encoding="utf-8") as file:
            csv_rows = list(csv.DictReader(file))
        saved_summary = json.loads(json_path.read_text(encoding="utf-8"))
        assert len(rows) == len(csv_rows) == 6
        assert set(CSV_COLUMNS).issubset(csv_rows[0])
        assert "official_like" in saved_summary
        assert set(saved_summary["official_like"]) == set(agents)
        for agent in agents:
            group = saved_summary["official_like"][agent]
            assert group["episodes"] == 2
            for field in (
                "success_rate",
                "mean_final_score",
                "mean_bonds",
                "mean_runtime_seconds",
            ):
                assert field in group
        assert summary == saved_summary
        assert "not final dissertation results" in markdown_path.read_text(
            encoding="utf-8"
        )


def run_all() -> None:
    test_quick_agent_benchmark_outputs()
    print("PASS test_quick_agent_benchmark_outputs")
    print("1 agent benchmark smoke test passed.")


if __name__ == "__main__":
    run_all()
