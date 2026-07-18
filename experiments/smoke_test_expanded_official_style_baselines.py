from __future__ import annotations

from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_official_like_baselines import run_baseline_experiment


EXPANDED_MAP = (
    PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)


def test_tiny_baseline_run_supports_expanded_map() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        temp_csv = temp_path / "expanded.csv"
        temp_summary = temp_path / "expanded_summary.json"

        rows, summary = run_baseline_experiment(
            episodes_per_agent=1,
            max_steps_per_episode=20,
            base_seed=42,
            map_path=EXPANDED_MAP,
            config_path=OFFICIAL_CONFIG,
            output_csv=temp_csv,
            output_summary=temp_summary,
        )

        assert rows
        assert summary
        assert any(
            row["agent_name"] == "objective_aware_greedy" for row in rows
        )
        assert any(row["agent_name"] == "lookahead_greedy" for row in rows)
        assert temp_csv.exists()
        assert temp_summary.exists()
        assert all(row["success"] in {True, False} for row in rows)


def run_all() -> None:
    tests = [test_tiny_baseline_run_supports_expanded_map]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} expanded baseline smoke tests passed.")


if __name__ == "__main__":
    run_all()
