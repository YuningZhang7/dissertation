from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.mcts_agent import MCTSAgent
from agents.registry import create_agent
from experiments.run_experiments import CSV_COLUMNS, resolve_map_paths, resolve_project_path
from experiments.simulation_runner import run_episode
from railways.environment import DEFAULT_CONFIG_PATH, DEFAULT_MAP_PATH

DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "raw" / "mcts_experiment_results.csv"
BASELINE_AGENT_NAMES = ["random", "greedy_delivery", "greedy_expansion"]
MCTS_COLUMNS = [
    "mcts_iterations",
    "mcts_rollout_depth",
    "mcts_exploration_constant",
    "mcts_rollout_policy",
]


def run_mcts_batch(
    episodes: int,
    seed: int,
    output: str | Path = DEFAULT_OUTPUT,
    map_arg: str | Path = DEFAULT_MAP_PATH,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    iterations_list: list[int] | None = None,
    rollout_depth: int = 80,
    exploration_constant: float = 1.414,
    rollout_policy: str = "random",
    max_steps: int = 1000,
) -> list[dict[str, Any]]:
    selected_map_paths = resolve_map_paths(map_arg)
    selected_config_path = resolve_project_path(config_path)
    budgets = iterations_list or [100]
    results: list[dict[str, Any]] = []

    for map_path in selected_map_paths:
        for agent_name in BASELINE_AGENT_NAMES:
            for episode_index in range(episodes):
                episode_seed = seed + episode_index
                result = run_episode(
                    create_agent(agent_name, seed=episode_seed),
                    seed=episode_seed,
                    max_steps=max_steps,
                    map_path=map_path,
                    config_path=selected_config_path,
                )
                result.update(_empty_mcts_metadata())
                results.append(result)

        for iterations in budgets:
            for episode_index in range(episodes):
                episode_seed = seed + episode_index
                agent = MCTSAgent(
                    seed=episode_seed,
                    iterations=iterations,
                    exploration_constant=exploration_constant,
                    rollout_depth_limit=rollout_depth,
                    rollout_policy=rollout_policy,
                )
                result = run_episode(
                    agent,
                    seed=episode_seed,
                    max_steps=max_steps,
                    map_path=map_path,
                    config_path=selected_config_path,
                )
                result["agent"] = f"mcts_{iterations}"
                result.update(
                    {
                        "mcts_iterations": iterations,
                        "mcts_rollout_depth": rollout_depth,
                        "mcts_exploration_constant": exploration_constant,
                        "mcts_rollout_policy": rollout_policy,
                    }
                )
                results.append(result)

    write_results_csv(results, output)
    return results


def write_results_csv(results: list[dict[str, Any]], output: str | Path) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[*CSV_COLUMNS, *MCTS_COLUMNS])
        writer.writeheader()
        writer.writerows(results)


def print_summary(results: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault((str(result["map"]), str(result["agent"])), []).append(result)

    print("MCTS experiment summary")
    for (map_name, agent_name), rows in grouped.items():
        final_scores = [float(row["final_score"]) for row in rows]
        runtimes = [float(row["runtime_seconds"]) for row in rows]
        mean_score = statistics.fmean(final_scores)
        score_std = statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0
        mean_runtime = statistics.fmean(runtimes)
        print(
            f"- {map_name}/{agent_name}: episodes={len(rows)}, "
            f"mean_final_score={mean_score:.2f}, std={score_std:.2f}, "
            f"mean_runtime={mean_runtime:.4f}s"
        )


def parse_iterations_list(value: str | None, fallback: int) -> list[int]:
    if not value:
        return [fallback]

    budgets = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not budgets:
        raise ValueError("--iterations-list must contain at least one integer.")
    return budgets


def _empty_mcts_metadata() -> dict[str, str]:
    return {
        "mcts_iterations": "",
        "mcts_rollout_depth": "",
        "mcts_exploration_constant": "",
        "mcts_rollout_policy": "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare baseline agents with Monte Carlo Tree Search."
    )
    parser.add_argument("--map", default=str(DEFAULT_MAP_PATH))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--iterations-list", default=None)
    parser.add_argument("--rollout-depth", type=int, default=80)
    parser.add_argument("--exploration-constant", type=float, default=1.414)
    parser.add_argument(
        "--rollout-policy",
        choices=["random", "greedy_delivery"],
        default="random",
    )
    parser.add_argument("--max-steps", type=int, default=1000)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    budgets = parse_iterations_list(args.iterations_list, args.iterations)
    results = run_mcts_batch(
        episodes=args.episodes,
        seed=args.seed,
        output=args.output,
        map_arg=args.map,
        config_path=args.config,
        iterations_list=budgets,
        rollout_depth=args.rollout_depth,
        exploration_constant=args.exploration_constant,
        rollout_policy=args.rollout_policy,
        max_steps=args.max_steps,
    )
    print(f"Wrote {len(results)} rows to {args.output}")
    print_summary(results)


if __name__ == "__main__":
    main()
