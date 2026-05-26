from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = "data/semi_realistic_map.json"
DEFAULT_SENSITIVITY_RESULTS = PROJECT_ROOT / "results" / "raw" / "major_line_sensitivity_results.csv"
DEFAULT_SENSITIVITY_SUMMARY = PROJECT_ROOT / "results" / "processed" / "major_line_sensitivity_summary.csv"
DEFAULT_SENSITIVITY_PLOTS = PROJECT_ROOT / "results" / "plots" / "major_line_sensitivity"
DEFAULT_MCTS_RESULTS = PROJECT_ROOT / "results" / "raw" / "mcts_major_line_results.csv"
DEFAULT_MCTS_SUMMARY = PROJECT_ROOT / "results" / "processed" / "mcts_major_line_summary.csv"
DEFAULT_MCTS_PLOTS = PROJECT_ROOT / "results" / "plots" / "mcts_major_line"


def run_pipeline(
    episodes: int,
    mcts_episodes: int,
    mcts_iterations_list: str,
    multipliers: str,
    seed: int,
    map_path: str = DEFAULT_MAP,
    rollout_depth: int = 60,
    sensitivity_output: str | Path = DEFAULT_SENSITIVITY_RESULTS,
    sensitivity_summary: str | Path = DEFAULT_SENSITIVITY_SUMMARY,
    sensitivity_plots: str | Path = DEFAULT_SENSITIVITY_PLOTS,
    mcts_output: str | Path = DEFAULT_MCTS_RESULTS,
    mcts_summary: str | Path = DEFAULT_MCTS_SUMMARY,
    mcts_plots: str | Path = DEFAULT_MCTS_PLOTS,
) -> None:
    commands = [
        [sys.executable, "experiments/smoke_test_rules.py"],
        [sys.executable, "experiments/smoke_test_agents.py"],
        [sys.executable, "experiments/smoke_test_maps.py"],
        [sys.executable, "experiments/smoke_test_mcts.py"],
        [
            sys.executable,
            "experiments/run_major_line_sensitivity.py",
            "--map",
            map_path,
            "--episodes",
            str(episodes),
            "--mcts-episodes",
            str(mcts_episodes),
            "--mcts-iterations-list",
            mcts_iterations_list,
            "--multipliers",
            multipliers,
            "--rollout-depth",
            str(rollout_depth),
            "--seed",
            str(seed),
            "--output",
            str(sensitivity_output),
        ],
        [
            sys.executable,
            "experiments/analyse_major_line_sensitivity.py",
            "--input",
            str(sensitivity_output),
            "--output",
            str(sensitivity_summary),
        ],
        [
            sys.executable,
            "experiments/plot_major_line_sensitivity.py",
            "--input",
            str(sensitivity_output),
            "--output-dir",
            str(sensitivity_plots),
        ],
        [
            sys.executable,
            "experiments/run_mcts_major_line_experiments.py",
            "--map",
            map_path,
            "--episodes",
            str(mcts_episodes),
            "--iterations-list",
            mcts_iterations_list,
            "--rollout-depth",
            str(rollout_depth),
            "--seed",
            str(seed),
            "--output",
            str(mcts_output),
        ],
        [
            sys.executable,
            "experiments/analyse_results.py",
            "--input",
            str(mcts_output),
            "--output",
            str(mcts_summary),
        ],
        [
            sys.executable,
            "experiments/plot_results.py",
            "--input",
            str(mcts_output),
            "--output-dir",
            str(mcts_plots),
        ],
        [
            sys.executable,
            "experiments/validate_major_line_experiments.py",
            "--input",
            str(mcts_output),
            "--episodes",
            str(mcts_episodes),
            "--agents",
            ",".join(_expected_agents(mcts_iterations_list)),
        ],
    ]

    for command in commands:
        print(f"\nRunning: {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

    print(
        "\nDiagnosis pipeline complete. Update notes/SEMI_REALISTIC_DIAGNOSIS.md "
        "with the generated summaries if this was a new full run.",
        flush=True,
    )


def _expected_agents(iterations_list: str) -> list[str]:
    agents = ["random", "greedy_delivery", "greedy_expansion"]
    budgets = [item.strip() for item in iterations_list.split(",") if item.strip()]
    for budget in budgets:
        agents.append(f"mcts_{budget}_random")
        agents.append(f"mcts_{budget}_majorline")
    return agents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the semi-realistic diagnosis and major-line-aware MCTS pipeline."
    )
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--mcts-episodes", type=int, default=5)
    parser.add_argument("--mcts-iterations-list", default="50,100")
    parser.add_argument("--multipliers", default="0,0.5,0.75,1.0")
    parser.add_argument("--rollout-depth", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--map", default=DEFAULT_MAP)
    parser.add_argument("--sensitivity-output", default=str(DEFAULT_SENSITIVITY_RESULTS))
    parser.add_argument("--sensitivity-summary", default=str(DEFAULT_SENSITIVITY_SUMMARY))
    parser.add_argument("--sensitivity-plots", default=str(DEFAULT_SENSITIVITY_PLOTS))
    parser.add_argument("--mcts-output", default=str(DEFAULT_MCTS_RESULTS))
    parser.add_argument("--mcts-summary", default=str(DEFAULT_MCTS_SUMMARY))
    parser.add_argument("--mcts-plots", default=str(DEFAULT_MCTS_PLOTS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(
        episodes=args.episodes,
        mcts_episodes=args.mcts_episodes,
        mcts_iterations_list=args.mcts_iterations_list,
        multipliers=args.multipliers,
        seed=args.seed,
        map_path=args.map,
        rollout_depth=args.rollout_depth,
        sensitivity_output=args.sensitivity_output,
        sensitivity_summary=args.sensitivity_summary,
        sensitivity_plots=args.sensitivity_plots,
        mcts_output=args.mcts_output,
        mcts_summary=args.mcts_summary,
        mcts_plots=args.mcts_plots,
    )


if __name__ == "__main__":
    main()
