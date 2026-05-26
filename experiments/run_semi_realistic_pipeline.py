from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = "data/semi_realistic_map.json"
DEFAULT_BASELINE_RESULTS = PROJECT_ROOT / "results" / "raw" / "semi_realistic_baseline_results.csv"
DEFAULT_BASELINE_SUMMARY = PROJECT_ROOT / "results" / "processed" / "semi_realistic_baseline_summary.csv"
DEFAULT_BASELINE_PLOTS = PROJECT_ROOT / "results" / "plots" / "semi_realistic_baseline"
DEFAULT_MCTS_RESULTS = PROJECT_ROOT / "results" / "raw" / "semi_realistic_mcts_results.csv"
DEFAULT_MCTS_SUMMARY = PROJECT_ROOT / "results" / "processed" / "semi_realistic_mcts_summary.csv"
DEFAULT_MCTS_PLOTS = PROJECT_ROOT / "results" / "plots" / "semi_realistic_mcts"


def run_pipeline(
    baseline_episodes: int,
    mcts_episodes: int,
    mcts_iterations_list: str,
    seed: int,
    map_path: str = DEFAULT_MAP,
    mcts_rollout_depth: int = 60,
    mcts_rollout_policy: str = "random",
    baseline_output: str | Path = DEFAULT_BASELINE_RESULTS,
    baseline_summary: str | Path = DEFAULT_BASELINE_SUMMARY,
    baseline_plots: str | Path = DEFAULT_BASELINE_PLOTS,
    mcts_output: str | Path = DEFAULT_MCTS_RESULTS,
    mcts_summary: str | Path = DEFAULT_MCTS_SUMMARY,
    mcts_plots: str | Path = DEFAULT_MCTS_PLOTS,
) -> None:
    baseline_output_path = Path(baseline_output)
    baseline_summary_path = Path(baseline_summary)
    baseline_plots_path = Path(baseline_plots)
    mcts_output_path = Path(mcts_output)
    mcts_summary_path = Path(mcts_summary)
    mcts_plots_path = Path(mcts_plots)
    map_name = Path(map_path).stem

    commands = [
        [sys.executable, "experiments/smoke_test_rules.py"],
        [sys.executable, "experiments/smoke_test_agents.py"],
        [sys.executable, "experiments/smoke_test_maps.py"],
        [sys.executable, "experiments/smoke_test_mcts.py"],
        [sys.executable, "experiments/check_project_readiness.py"],
        [
            sys.executable,
            "experiments/run_experiments.py",
            "--agent",
            "all",
            "--episodes",
            str(baseline_episodes),
            "--seed",
            str(seed),
            "--map",
            map_path,
            "--output",
            str(baseline_output_path),
        ],
        [
            sys.executable,
            "experiments/analyse_results.py",
            "--input",
            str(baseline_output_path),
            "--output",
            str(baseline_summary_path),
        ],
        [
            sys.executable,
            "experiments/plot_results.py",
            "--input",
            str(baseline_output_path),
            "--output-dir",
            str(baseline_plots_path),
        ],
        [
            sys.executable,
            "experiments/validate_baselines.py",
            "--input",
            str(baseline_output_path),
            "--episodes",
            str(baseline_episodes),
            "--maps",
            map_name,
        ],
        [
            sys.executable,
            "experiments/run_mcts_experiments.py",
            "--map",
            map_path,
            "--episodes",
            str(mcts_episodes),
            "--iterations-list",
            mcts_iterations_list,
            "--rollout-depth",
            str(mcts_rollout_depth),
            "--rollout-policy",
            mcts_rollout_policy,
            "--seed",
            str(seed),
            "--output",
            str(mcts_output_path),
        ],
        [
            sys.executable,
            "experiments/analyse_results.py",
            "--input",
            str(mcts_output_path),
            "--output",
            str(mcts_summary_path),
        ],
        [
            sys.executable,
            "experiments/plot_results.py",
            "--input",
            str(mcts_output_path),
            "--output-dir",
            str(mcts_plots_path),
        ],
        [
            sys.executable,
            "experiments/validate_mcts_results.py",
            "--input",
            str(mcts_output_path),
            "--episodes",
            str(mcts_episodes),
            "--maps",
            map_name,
            "--agents",
            ",".join(_expected_mcts_agents(mcts_iterations_list)),
        ],
    ]

    for command in commands:
        print(f"\nRunning: {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def _expected_mcts_agents(iterations_list: str) -> list[str]:
    agents = ["random", "greedy_delivery", "greedy_expansion"]
    budgets = [item.strip() for item in iterations_list.split(",") if item.strip()]
    agents.extend(f"mcts_{budget}" for budget in budgets)
    return agents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the semi-realistic baseline and MCTS experiment pipeline."
    )
    parser.add_argument("--baseline-episodes", type=int, default=50)
    parser.add_argument("--mcts-episodes", type=int, default=10)
    parser.add_argument("--mcts-iterations-list", default="50,100")
    parser.add_argument("--mcts-rollout-depth", type=int, default=60)
    parser.add_argument("--mcts-rollout-policy", default="random")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--map", default=DEFAULT_MAP)
    parser.add_argument("--baseline-output", default=str(DEFAULT_BASELINE_RESULTS))
    parser.add_argument("--baseline-summary", default=str(DEFAULT_BASELINE_SUMMARY))
    parser.add_argument("--baseline-plots", default=str(DEFAULT_BASELINE_PLOTS))
    parser.add_argument("--mcts-output", default=str(DEFAULT_MCTS_RESULTS))
    parser.add_argument("--mcts-summary", default=str(DEFAULT_MCTS_SUMMARY))
    parser.add_argument("--mcts-plots", default=str(DEFAULT_MCTS_PLOTS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(
        baseline_episodes=args.baseline_episodes,
        mcts_episodes=args.mcts_episodes,
        mcts_iterations_list=args.mcts_iterations_list,
        seed=args.seed,
        map_path=args.map,
        mcts_rollout_depth=args.mcts_rollout_depth,
        mcts_rollout_policy=args.mcts_rollout_policy,
        baseline_output=args.baseline_output,
        baseline_summary=args.baseline_summary,
        baseline_plots=args.baseline_plots,
        mcts_output=args.mcts_output,
        mcts_summary=args.mcts_summary,
        mcts_plots=args.mcts_plots,
    )


if __name__ == "__main__":
    main()
