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
from experiments.run_experiments import CSV_COLUMNS, resolve_project_path
from experiments.run_mcts_experiments import MCTS_COLUMNS
from experiments.simulation_runner import run_episode
from railways.environment import DEFAULT_CONFIG_PATH

DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "raw" / "mcts_major_line_results.csv"
BASELINE_AGENT_NAMES = ["random", "greedy_delivery", "greedy_expansion"]
EVALUATION_COLUMNS = [
    "mcts_evaluation_mode",
    "mcts_major_line_weight",
    "mcts_delivery_weight",
    "mcts_network_weight",
]


def run_major_line_mcts_batch(
    map_path: str | Path,
    episodes: int,
    iterations_list: list[int],
    seed: int,
    output: str | Path = DEFAULT_OUTPUT,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    rollout_depth: int = 60,
    rollout_policy: str = "random",
    max_steps: int = 1000,
    major_line_weight: float = 1.0,
    delivery_weight: float = 0.2,
    network_weight: float = 0.1,
) -> list[dict[str, Any]]:
    selected_map_path = resolve_project_path(map_path)
    selected_config_path = resolve_project_path(config_path)
    results: list[dict[str, Any]] = []

    for agent_name in BASELINE_AGENT_NAMES:
        for episode_index in range(episodes):
            episode_seed = seed + episode_index
            result = run_episode(
                create_agent(agent_name, seed=episode_seed),
                seed=episode_seed,
                max_steps=max_steps,
                map_path=selected_map_path,
                config_path=selected_config_path,
            )
            result.update(_empty_mcts_metadata())
            results.append(result)

    for iterations in iterations_list:
        for evaluation_mode in ("final_score", "major_line_aware"):
            for episode_index in range(episodes):
                episode_seed = seed + episode_index
                agent = MCTSAgent(
                    seed=episode_seed,
                    iterations=iterations,
                    rollout_depth_limit=rollout_depth,
                    rollout_policy=rollout_policy,
                    evaluation_mode=evaluation_mode,
                    major_line_weight=major_line_weight,
                    delivery_weight=delivery_weight,
                    network_weight=network_weight,
                )
                result = run_episode(
                    agent,
                    seed=episode_seed,
                    max_steps=max_steps,
                    map_path=selected_map_path,
                    config_path=selected_config_path,
                )
                result["agent"] = _mcts_label(iterations, evaluation_mode)
                result.update(
                    {
                        "mcts_iterations": iterations,
                        "mcts_rollout_depth": rollout_depth,
                        "mcts_exploration_constant": agent.exploration_constant,
                        "mcts_rollout_policy": rollout_policy,
                        "mcts_action_generation": agent.action_generation,
                        "mcts_max_candidate_actions": agent.max_candidate_actions,
                        "mcts_evaluation_mode": evaluation_mode,
                        "mcts_major_line_weight": major_line_weight,
                        "mcts_delivery_weight": delivery_weight,
                        "mcts_network_weight": network_weight,
                    }
                )
                results.append(result)

    write_results_csv(results, output)
    return results


def write_results_csv(results: list[dict[str, Any]], output: str | Path) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[*CSV_COLUMNS, *MCTS_COLUMNS, *EVALUATION_COLUMNS],
        )
        writer.writeheader()
        writer.writerows(results)


def print_summary(results: list[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(str(result["agent"]), []).append(result)

    print("Major-line-aware MCTS summary")
    for agent, rows in sorted(grouped.items()):
        scores = [float(row["final_score"]) for row in rows]
        runtimes = [float(row["runtime_seconds"]) for row in rows]
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        print(
            f"- {agent}: episodes={len(rows)}, "
            f"mean_final_score={statistics.fmean(scores):.2f}, "
            f"std={score_std:.2f}, "
            f"mean_runtime={statistics.fmean(runtimes):.2f}s"
        )


def _mcts_label(iterations: int, evaluation_mode: str) -> str:
    if evaluation_mode == "major_line_aware":
        return f"mcts_{iterations}_majorline"
    return f"mcts_{iterations}_random"


def _empty_mcts_metadata() -> dict[str, Any]:
    return {
        "mcts_iterations": "",
        "mcts_rollout_depth": "",
        "mcts_exploration_constant": "",
        "mcts_rollout_policy": "",
        "mcts_action_generation": "",
        "mcts_max_candidate_actions": "",
        "mcts_evaluation_mode": "",
        "mcts_major_line_weight": "",
        "mcts_delivery_weight": "",
        "mcts_network_weight": "",
    }


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare final-score and major-line-aware MCTS variants."
    )
    parser.add_argument("--map", default="data/semi_realistic_map.json")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--iterations-list", default="50,100")
    parser.add_argument("--rollout-depth", type=int, default=60)
    parser.add_argument("--rollout-policy", default="random")
    parser.add_argument("--major-line-weight", type=float, default=1.0)
    parser.add_argument("--delivery-weight", type=float, default=0.2)
    parser.add_argument("--network-weight", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=1000)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_major_line_mcts_batch(
        map_path=args.map,
        episodes=args.episodes,
        iterations_list=_parse_int_list(args.iterations_list),
        seed=args.seed,
        output=args.output,
        config_path=args.config,
        rollout_depth=args.rollout_depth,
        rollout_policy=args.rollout_policy,
        max_steps=args.max_steps,
        major_line_weight=args.major_line_weight,
        delivery_weight=args.delivery_weight,
        network_weight=args.network_weight,
    )
    print(f"Wrote {len(results)} rows to {args.output}")
    print_summary(results)


if __name__ == "__main__":
    main()
