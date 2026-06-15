from __future__ import annotations

import csv
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_phase4_card_experiments import run_phase4_card_experiments


def test_phase4_experiment_pipeline_writes_expected_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        disabled_output = output_dir / "disabled.csv"
        enabled_output = output_dir / "enabled.csv"
        summary_csv = output_dir / "summary.csv"
        summary_md = output_dir / "summary.md"

        summaries = run_phase4_card_experiments(
            maps=[PROJECT_ROOT / "data" / "toy_map.json"],
            agents=["random", "greedy_delivery"],
            episodes=2,
            seed=0,
            max_steps=100,
            mcts_iterations=5,
            mcts_rollout_depth=20,
            disabled_output=disabled_output,
            enabled_output=enabled_output,
            summary_csv=summary_csv,
            summary_md=summary_md,
        )

        assert disabled_output.exists()
        assert enabled_output.exists()
        assert summary_csv.exists()
        assert summary_md.exists()
        assert summaries

        disabled_rows = _read_rows(disabled_output)
        enabled_rows = _read_rows(enabled_output)
        required_columns = {
            "cards_enabled",
            "operation_card_bonus",
            "end_game_card_bonus",
            "cards_selected",
            "cards_completed",
            "invalid_actions",
        }
        assert required_columns.issubset(disabled_rows[0])
        assert required_columns.issubset(enabled_rows[0])
        assert all(not _as_bool(row["cards_enabled"]) for row in disabled_rows)
        assert all(_as_bool(row["cards_enabled"]) for row in enabled_rows)
        assert all(int(row["invalid_actions"]) == 0 for row in disabled_rows)
        assert all(int(row["invalid_actions"]) == 0 for row in enabled_rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def run_all() -> None:
    tests = [test_phase4_experiment_pipeline_writes_expected_outputs]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} Phase 4 experiment smoke tests passed.")


if __name__ == "__main__":
    run_all()
