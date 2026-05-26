from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics
import sys
import tempfile
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

DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "raw" / "major_line_sensitivity_results.csv"
BASELINE_AGENT_NAMES = ["random", "greedy_delivery", "greedy_expansion"]
EXTRA_COLUMNS = [
    "major_line_multiplier",
    "mcts_evaluation_mode",
    "mcts_major_line_weight",
    "mcts_delivery_weight",
    "mcts_network_weight",
]


def run_sensitivity(
    map_path: str | Path,
    episodes: int,
    mcts_episodes: int,
    mcts_iterations_list: list[int],
    multipliers: list[float],
    seed: int,
    output: str | Path = DEFAULT_OUTPUT,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    rollout_depth: int = 60,
    rollout_policy: str = "random",
    max_steps: int = 1000,
) -> list[dict[str, Any]]:
    selected_map_path = resolve_project_path(map_path)
    selected_config_path = resolve_project_path(config_path)
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="railways_major_line_") as temp_dir:
        temp_root = Path(temp_dir)
        for multiplier in multipliers:
            scaled_map_path = _write_scaled_map(
                selected_map_path,
                temp_root,
                multiplier,
            )
            results.extend(
                _run_baseline_rows(
                    selected_map_path,
                    scaled_map_path,
                    selected_config_path,
                    multiplier,
                    episodes,
                    seed,
                    max_steps,
                )
            )
            results.extend(
                _run_mcts_rows(
                    selected_map_path,
                    scaled_map_path,
                    selected_config_path,
                    multiplier,
                    mcts_episodes,
                    mcts_iterations_list,
                    seed,
                    rollout_depth,
                    rollout_policy,
                    max_steps,
                )
            )

    write_results_csv(results, output)
    return results


def _run_baseline_rows(
    original_map_path: Path,
    scaled_map_path: Path,
    config_path: Path,
    multiplier: float,
    episodes: int,
    seed: int,
    max_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for agent_name in BASELINE_AGENT_NAMES:
        for episode_index in range(episodes):
            episode_seed = seed + episode_index
            result = run_episode(
                create_agent(agent_name, seed=episode_seed),
                seed=episode_seed,
                max_steps=max_steps,
                map_path=scaled_map_path,
                config_path=config_path,
            )
            result["map"] = original_map_path.stem
            result["major_line_multiplier"] = multiplier
            result.update(_empty_mcts_metadata())
            rows.append(result)
    return rows


def _run_mcts_rows(
    original_map_path: Path,
    scaled_map_path: Path,
    config_path: Path,
    multiplier: float,
    episodes: int,
    iterations_list: list[int],
    seed: int,
    rollout_depth: int,
    rollout_policy: str,
    max_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for iterations in iterations_list:
        for episode_index in range(episodes):
            episode_seed = seed + episode_index
            agent = MCTSAgent(
                seed=episode_seed,
                iterations=iterations,
                rollout_depth_limit=rollout_depth,
                rollout_policy=rollout_policy,
                evaluation_mode="final_score",
            )
            result = run_episode(
                agent,
                seed=episode_seed,
                max_steps=max_steps,
                map_path=scaled_map_path,
                config_path=config_path,
            )
            result["map"] = original_map_path.stem
            result["agent"] = f"mcts_{iterations}"
            result["major_line_multiplier"] = multiplier
            result.update(
                {
                    "mcts_iterations": iterations,
                    "mcts_rollout_depth": rollout_depth,
                    "mcts_exploration_constant": agent.exploration_constant,
                    "mcts_rollout_policy": rollout_policy,
                    "mcts_action_generation": agent.action_generation,
                    "mcts_max_candidate_actions": agent.max_candidate_actions,
                    "mcts_evaluation_mode": agent.evaluation_mode,
                    "mcts_major_line_weight": agent.major_line_weight,
                    "mcts_delivery_weight": agent.delivery_weight,
                    "mcts_network_weight": agent.network_weight,
                }
            )
            rows.append(result)
    return rows


def _write_scaled_map(
    source_map_path: Path,
    output_dir: Path,
    multiplier: float,
) -> Path:
    with source_map_path.open("r", encoding="utf-8") as file:
        map_data = json.load(file)

    for major_line in map_data.get("major_lines", []):
        major_line["bonus_points"] = int(
            round(int(major_line["bonus_points"]) * multiplier)
        )

    metadata = map_data.setdefault("metadata", {})
    metadata["major_line_multiplier"] = multiplier

    multiplier_label = str(multiplier).replace(".", "_")
    output_path = output_dir / f"{source_map_path.stem}_major_line_{multiplier_label}.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(map_data, file, indent=2)
    return output_path


def write_results_csv(results: list[dict[str, Any]], output: str | Path) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*CSV_COLUMNS, "major_line_multiplier", *MCTS_COLUMNS, *EXTRA_COLUMNS[1:]]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_summary(results: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[float, str], list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(
            (float(result["major_line_multiplier"]), str(result["agent"])),
            [],
        ).append(result)

    print("Major-line sensitivity summary")
    for (multiplier, agent), rows in sorted(grouped.items()):
        scores = [float(row["final_score"]) for row in rows]
        mean_score = statistics.fmean(scores)
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        print(
            f"- multiplier={multiplier:g}/{agent}: episodes={len(rows)}, "
            f"mean_final_score={mean_score:.2f}, std={score_std:.2f}"
        )


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


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run major-line bonus sensitivity experiments."
    )
    parser.add_argument("--map", default="data/semi_realistic_map.json")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--mcts-episodes", type=int, default=5)
    parser.add_argument("--mcts-iterations-list", default="50,100")
    parser.add_argument("--multipliers", default="0,0.5,0.75,1.0")
    parser.add_argument("--rollout-depth", type=int, default=60)
    parser.add_argument("--rollout-policy", default="random")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=1000)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_sensitivity(
        map_path=args.map,
        episodes=args.episodes,
        mcts_episodes=args.mcts_episodes,
        mcts_iterations_list=_parse_int_list(args.mcts_iterations_list),
        multipliers=_parse_float_list(args.multipliers),
        seed=args.seed,
        output=args.output,
        config_path=args.config,
        rollout_depth=args.rollout_depth,
        rollout_policy=args.rollout_policy,
        max_steps=args.max_steps,
    )
    print(f"Wrote {len(results)} rows to {args.output}")
    print_summary(results)


if __name__ == "__main__":
    main()
