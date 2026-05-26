from __future__ import annotations

import argparse
import csv
from itertools import product
from pathlib import Path
import statistics
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.mcts_agent import MCTSAgent
from experiments.run_experiments import CSV_COLUMNS, resolve_map_paths, resolve_project_path
from experiments.run_mcts_experiments import MCTS_COLUMNS
from experiments.simulation_runner import run_episode
from railways.environment import DEFAULT_CONFIG_PATH, DEFAULT_MAP_PATH

DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "raw" / "mcts_tuning_results.csv"


def run_mcts_tuning(
    map_arg: str | Path = DEFAULT_MAP_PATH,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    episodes: int = 10,
    seed: int = 0,
    iterations_list: list[int] | None = None,
    rollout_depth_list: list[int] | None = None,
    rollout_policy_list: list[str] | None = None,
    action_generation_list: list[str] | None = None,
    max_candidate_actions_list: list[int] | None = None,
    exploration_constant: float = 1.414,
    max_steps: int = 1000,
    output: str | Path = DEFAULT_OUTPUT,
) -> list[dict[str, Any]]:
    map_paths = resolve_map_paths(map_arg)
    selected_config_path = resolve_project_path(config_path)
    iterations_values = iterations_list or [50, 100]
    rollout_depth_values = rollout_depth_list or [40, 80]
    rollout_policy_values = rollout_policy_list or ["random"]
    action_generation_values = action_generation_list or ["fast"]
    candidate_values = max_candidate_actions_list or [24]
    results: list[dict[str, Any]] = []

    parameter_grid = list(
        product(
            iterations_values,
            rollout_depth_values,
            rollout_policy_values,
            action_generation_values,
            candidate_values,
        )
    )

    for map_path in map_paths:
        for (
            iterations,
            rollout_depth,
            rollout_policy,
            action_generation,
            max_candidate_actions,
        ) in parameter_grid:
            for episode_index in range(episodes):
                episode_seed = seed + episode_index
                agent = MCTSAgent(
                    seed=episode_seed,
                    iterations=iterations,
                    exploration_constant=exploration_constant,
                    rollout_depth_limit=rollout_depth,
                    rollout_policy=rollout_policy,
                    action_generation=action_generation,
                    max_candidate_actions=max_candidate_actions,
                )
                result = run_episode(
                    agent,
                    seed=episode_seed,
                    max_steps=max_steps,
                    map_path=map_path,
                    config_path=selected_config_path,
                )
                result["agent"] = _agent_label(
                    iterations,
                    rollout_depth,
                    rollout_policy,
                    action_generation,
                    max_candidate_actions,
                )
                result.update(
                    {
                        "mcts_iterations": iterations,
                        "mcts_rollout_depth": rollout_depth,
                        "mcts_exploration_constant": exploration_constant,
                        "mcts_rollout_policy": rollout_policy,
                        "mcts_action_generation": action_generation,
                        "mcts_max_candidate_actions": max_candidate_actions,
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
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(str(result["agent"]), []).append(result)

    print("MCTS tuning summary")
    for agent_name, rows in grouped.items():
        scores = [float(row["final_score"]) for row in rows]
        runtimes = [float(row["runtime_seconds"]) for row in rows]
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        print(
            f"- {agent_name}: episodes={len(rows)}, "
            f"mean_final_score={statistics.fmean(scores):.2f}, "
            f"std={score_std:.2f}, "
            f"mean_runtime={statistics.fmean(runtimes):.4f}s"
        )


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_str_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _agent_label(
    iterations: int,
    rollout_depth: int,
    rollout_policy: str,
    action_generation: str,
    max_candidate_actions: int,
) -> str:
    policy_label = "greedy" if rollout_policy == "greedy_delivery" else rollout_policy
    return (
        f"mcts_i{iterations}_d{rollout_depth}_"
        f"{policy_label}_{action_generation}_c{max_candidate_actions}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MCTS tuning parameter sweeps.")
    parser.add_argument("--map", default=str(DEFAULT_MAP_PATH))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--iterations-list", default="50,100")
    parser.add_argument("--rollout-depth-list", default="40,80")
    parser.add_argument("--rollout-policy-list", default="random")
    parser.add_argument("--action-generation-list", default="fast")
    parser.add_argument("--max-candidate-actions-list", default="24")
    parser.add_argument("--exploration-constant", type=float, default=1.414)
    parser.add_argument("--max-steps", type=int, default=1000)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_mcts_tuning(
        map_arg=args.map,
        config_path=args.config,
        episodes=args.episodes,
        seed=args.seed,
        iterations_list=parse_int_list(args.iterations_list),
        rollout_depth_list=parse_int_list(args.rollout_depth_list),
        rollout_policy_list=parse_str_list(args.rollout_policy_list),
        action_generation_list=parse_str_list(args.action_generation_list),
        max_candidate_actions_list=parse_int_list(args.max_candidate_actions_list),
        exploration_constant=args.exploration_constant,
        max_steps=args.max_steps,
        output=args.output,
    )
    print(f"Wrote {len(results)} rows to {args.output}")
    print_summary(results)


if __name__ == "__main__":
    main()
