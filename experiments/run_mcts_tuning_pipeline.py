from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = PROJECT_ROOT / "results" / "raw" / "mcts_tuning_results.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "results" / "processed" / "mcts_tuning_summary.csv"
DEFAULT_PLOTS = PROJECT_ROOT / "results" / "plots" / "mcts_tuning"


def run_pipeline(
    map_arg: str,
    episodes: int,
    iterations_list: str,
    rollout_depth_list: str,
    rollout_policy_list: str,
    action_generation_list: str,
    max_candidate_actions_list: str,
    seed: int,
    output: str | Path = DEFAULT_RESULTS,
) -> None:
    output_path = Path(output)
    map_names = _map_names_for_validation(map_arg)
    commands = [
        [sys.executable, "experiments/smoke_test_rules.py"],
        [sys.executable, "experiments/smoke_test_agents.py"],
        [sys.executable, "experiments/smoke_test_maps.py"],
        [sys.executable, "experiments/smoke_test_mcts.py"],
        [
            sys.executable,
            "experiments/run_mcts_tuning.py",
            "--map",
            map_arg,
            "--episodes",
            str(episodes),
            "--iterations-list",
            iterations_list,
            "--rollout-depth-list",
            rollout_depth_list,
            "--rollout-policy-list",
            rollout_policy_list,
            "--action-generation-list",
            action_generation_list,
            "--max-candidate-actions-list",
            max_candidate_actions_list,
            "--seed",
            str(seed),
            "--output",
            str(output_path),
        ],
        [
            sys.executable,
            "experiments/analyse_mcts_tuning.py",
            "--input",
            str(output_path),
            "--output",
            str(DEFAULT_SUMMARY),
        ],
        [
            sys.executable,
            "experiments/plot_mcts_tuning.py",
            "--input",
            str(output_path),
            "--output-dir",
            str(DEFAULT_PLOTS),
        ],
        [
            sys.executable,
            "experiments/validate_mcts_tuning.py",
            "--input",
            str(output_path),
            "--episodes",
            str(episodes),
            "--maps",
            map_names,
            "--iterations-list",
            iterations_list,
            "--rollout-depth-list",
            rollout_depth_list,
            "--rollout-policy-list",
            rollout_policy_list,
            "--action-generation-list",
            action_generation_list,
            "--max-candidate-actions-list",
            max_candidate_actions_list,
        ],
    ]

    for command in commands:
        print(f"\nRunning: {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def _map_names_for_validation(map_arg: str) -> str:
    if map_arg == "all":
        return "toy_map,toy_medium_map"
    return Path(map_arg).stem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full MCTS tuning pipeline.")
    parser.add_argument("--map", default="data/toy_medium_map.json")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--iterations-list", default="50,100")
    parser.add_argument("--rollout-depth-list", default="40,80")
    parser.add_argument("--rollout-policy-list", default="random")
    parser.add_argument("--action-generation-list", default="fast")
    parser.add_argument("--max-candidate-actions-list", default="24")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default=str(DEFAULT_RESULTS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(
        map_arg=args.map,
        episodes=args.episodes,
        iterations_list=args.iterations_list,
        rollout_depth_list=args.rollout_depth_list,
        rollout_policy_list=args.rollout_policy_list,
        action_generation_list=args.action_generation_list,
        max_candidate_actions_list=args.max_candidate_actions_list,
        seed=args.seed,
        output=args.output,
    )


if __name__ == "__main__":
    main()
