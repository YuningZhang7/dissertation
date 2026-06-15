from __future__ import annotations

import csv
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_phase4_card_experiments import (
    Phase4OutputPaths,
    get_profile_output_paths,
    resolve_profile_settings,
    run_phase4_card_experiments,
)
from experiments.validate_phase4_card_results import validate_phase4_card_results


def test_phase4_profiles_and_overrides() -> None:
    quick = resolve_profile_settings("quick")
    assert quick.episodes == 2
    assert quick.mcts_iterations == 5
    assert quick.mcts_rollout_depth == 20
    assert quick.max_steps == 100

    overridden = resolve_profile_settings(
        "standard",
        episodes=3,
        mcts_iterations=7,
        mcts_rollout_depth=11,
        max_steps=99,
    )
    assert overridden.episodes == 3
    assert overridden.mcts_iterations == 7
    assert overridden.mcts_rollout_depth == 11
    assert overridden.max_steps == 99

    paths = get_profile_output_paths("mcts100")
    assert "phase4_mcts100" in paths.disabled_raw.name
    assert "phase4_mcts100" in paths.effect_csv.name


def test_phase4_experiment_pipeline_writes_expected_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        disabled_output = output_dir / "disabled.csv"
        enabled_output = output_dir / "enabled.csv"
        summary_csv = output_dir / "summary.csv"
        summary_md = output_dir / "summary.md"
        effect_csv = output_dir / "effect.csv"
        effect_md = output_dir / "effect.md"
        usage_csv = output_dir / "usage.csv"
        usage_md = output_dir / "usage.md"

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
            effect_csv=effect_csv,
            effect_md=effect_md,
            usage_csv=usage_csv,
            usage_md=usage_md,
        )

        assert disabled_output.exists()
        assert enabled_output.exists()
        assert summary_csv.exists()
        assert summary_md.exists()
        assert effect_csv.exists()
        assert effect_md.exists()
        assert usage_csv.exists()
        assert usage_md.exists()
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

        messages = validate_phase4_card_results(
            profile="quick",
            paths=Phase4OutputPaths(
                disabled_raw=disabled_output,
                enabled_raw=enabled_output,
                summary_csv=summary_csv,
                summary_md=summary_md,
                effect_csv=effect_csv,
                effect_md=effect_md,
                usage_csv=usage_csv,
                usage_md=usage_md,
            ),
            required_maps={"toy_map"},
            required_agents={"random", "greedy_delivery"},
        )
        assert "Invalid actions: 0" in messages


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def run_all() -> None:
    tests = [
        test_phase4_profiles_and_overrides,
        test_phase4_experiment_pipeline_writes_expected_outputs,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} Phase 4 experiment smoke tests passed.")


if __name__ == "__main__":
    run_all()
