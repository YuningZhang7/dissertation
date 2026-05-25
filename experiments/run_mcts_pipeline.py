from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = PROJECT_ROOT / "results" / "raw" / "mcts_experiment_results.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "results" / "processed" / "mcts_summary_by_map_agent.csv"
DEFAULT_PLOTS = PROJECT_ROOT / "results" / "plots" / "mcts"


def run_pipeline(
    map_path: str,
    episodes: int,
    iterations_list: str,
    seed: int,
    output: str | Path = DEFAULT_RESULTS,
    rollout_depth: int = 80,
    rollout_policy: str = "random",
    rollout_policy_list: str | None = None,
) -> None:
    output_path = Path(output)
    agents = _expected_agents(iterations_list, rollout_policy_list)
    commands = [
        [sys.executable, "experiments/smoke_test_rules.py"],
        [sys.executable, "experiments/smoke_test_agents.py"],
        [sys.executable, "experiments/smoke_test_maps.py"],
        [sys.executable, "experiments/smoke_test_mcts.py"],
        [
            sys.executable,
            "experiments/run_mcts_experiments.py",
            "--map",
            map_path,
            "--episodes",
            str(episodes),
            "--iterations-list",
            iterations_list,
            "--rollout-depth",
            str(rollout_depth),
            "--rollout-policy",
            rollout_policy,
            "--seed",
            str(seed),
            "--output",
            str(output_path),
        ],
        [
            sys.executable,
            "experiments/analyse_results.py",
            "--input",
            str(output_path),
            "--output",
            str(DEFAULT_SUMMARY),
        ],
        [
            sys.executable,
            "experiments/plot_results.py",
            "--input",
            str(output_path),
            "--output-dir",
            str(DEFAULT_PLOTS),
        ],
        [
            sys.executable,
            "experiments/validate_mcts_results.py",
            "--input",
            str(output_path),
            "--episodes",
            str(episodes),
            "--agents",
            ",".join(agents),
        ],
    ]

    if rollout_policy_list:
        commands[4].extend(["--rollout-policy-list", rollout_policy_list])

    for command in commands:
        print(f"\nRunning: {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def _expected_agents(
    iterations_list: str,
    rollout_policy_list: str | None,
) -> list[str]:
    agents = ["random", "greedy_delivery", "greedy_expansion"]
    budgets = [item.strip() for item in iterations_list.split(",") if item.strip()]

    if not rollout_policy_list:
        agents.extend(f"mcts_{budget}" for budget in budgets)
        return agents

    policies = [item.strip() for item in rollout_policy_list.split(",") if item.strip()]
    for policy in policies:
        label = "greedy" if policy == "greedy_delivery" else policy
        agents.extend(f"mcts_{budget}_{label}" for budget in budgets)
    return agents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full MCTS validation pipeline.")
    parser.add_argument("--map", default="data/toy_medium_map.json")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--iterations-list", default="50,100,250")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rollout-depth", type=int, default=80)
    parser.add_argument("--rollout-policy", default="random")
    parser.add_argument("--rollout-policy-list", default=None)
    parser.add_argument("--output", default=str(DEFAULT_RESULTS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(
        map_path=args.map,
        episodes=args.episodes,
        iterations_list=args.iterations_list,
        seed=args.seed,
        output=args.output,
        rollout_depth=args.rollout_depth,
        rollout_policy=args.rollout_policy,
        rollout_policy_list=args.rollout_policy_list,
    )


if __name__ == "__main__":
    main()
