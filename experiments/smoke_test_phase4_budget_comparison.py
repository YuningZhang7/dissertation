from __future__ import annotations

import csv
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.compare_phase4_mcts_budget import (
    COMPARISON_COLUMNS,
    compare_phase4_mcts_budget,
)
from experiments.summarise_phase4_results import SUMMARY_COLUMNS


def test_budget_comparison_writes_expected_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        standard = output_dir / "standard.csv"
        mcts100 = output_dir / "mcts100.csv"
        output_csv = output_dir / "comparison.csv"
        output_md = output_dir / "comparison.md"

        _write_summary(standard, score_offset=0.0, runtime_offset=0.0)
        _write_summary(mcts100, score_offset=2.0, runtime_offset=3.0)
        rows = compare_phase4_mcts_budget(
            standard,
            mcts100,
            output_csv,
            output_md,
        )

        assert output_csv.exists()
        assert output_md.exists()
        assert {row["agent"] for row in rows} == {"mcts", "mcts_majorline"}
        assert {row["cards_enabled"] for row in rows} == {False, True}
        assert all(row["budget_delta"] == 2.0 for row in rows)
        assert all(row["runtime_delta"] == 3.0 for row in rows)

        with output_csv.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            assert set(COMPARISON_COLUMNS).issubset(reader.fieldnames or [])


def _write_summary(path: Path, score_offset: float, runtime_offset: float) -> None:
    rows = []
    for agent in ["mcts", "mcts_majorline", "random"]:
        for cards_enabled in [False, True]:
            rows.append(
                {
                    "map": "toy_map",
                    "cards_enabled": cards_enabled,
                    "agent": agent,
                    "episodes": 2,
                    "mean_final_score": 10.0 + score_offset + cards_enabled,
                    "std_final_score": 1.0,
                    "min_final_score": 9.0,
                    "max_final_score": 11.0,
                    "mean_raw_score": 8.0,
                    "mean_major_line_bonus": 3.0,
                    "mean_operation_card_bonus": 2.0 if cards_enabled else 0.0,
                    "mean_end_game_card_bonus": 4.0 if cards_enabled else 0.0,
                    "mean_financing_penalty": 1.0,
                    "mean_cards_selected": 3.0 if cards_enabled else 0.0,
                    "mean_cards_completed": 2.0 if cards_enabled else 0.0,
                    "mean_invalid_actions": 0.0,
                    "mean_runtime_seconds": 1.0 + runtime_offset,
                }
            )
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def run_all() -> None:
    tests = [test_budget_comparison_writes_expected_outputs]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} Phase 4 budget comparison smoke tests passed.")


if __name__ == "__main__":
    run_all()
