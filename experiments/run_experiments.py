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

from agents.registry import AGENT_CLASSES, create_agent
from experiments.simulation_runner import run_episode
from railways.environment import DEFAULT_CONFIG_PATH, DEFAULT_MAP_PATH

DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "raw" / "experiment_results.csv"
BASELINE_AGENT_NAMES = ["random", "greedy_delivery", "greedy_expansion"]
DEFAULT_MAPS = [
    DEFAULT_MAP_PATH,
    PROJECT_ROOT / "data" / "toy_medium_map.json",
    PROJECT_ROOT / "data" / "semi_realistic_map.json",
]
CSV_COLUMNS = [
    "map",
    "config",
    "agent",
    "seed",
    "final_score",
    "raw_score",
    "bonds",
    "money",
    "deliveries",
    "built_edges",
    "major_line_bonus",
    "rail_baron_bonus",
    "operation_card_bonus",
    "empty_markers",
    "turns",
    "actions_taken",
    "invalid_actions",
    "runtime_seconds",
    "terminal",
]


def run_batch(
    agent_name: str,
    episodes: int,
    seed: int,
    output: str | Path = DEFAULT_OUTPUT,
    max_steps: int = 1000,
    map_arg: str | Path = DEFAULT_MAP_PATH,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> list[dict[str, Any]]:
    agent_names = BASELINE_AGENT_NAMES if agent_name == "all" else [agent_name]
    map_paths = resolve_map_paths(map_arg)
    selected_config_path = resolve_project_path(config_path)
    results: list[dict[str, Any]] = []

    for map_path in map_paths:
        for name in agent_names:
            for episode_index in range(episodes):
                episode_seed = seed + episode_index
                agent = create_agent(name, seed=episode_seed)
                result = run_episode(
                    agent,
                    seed=episode_seed,
                    max_steps=max_steps,
                    map_path=map_path,
                    config_path=selected_config_path,
                )
                results.append(result)

    write_results_csv(results, output)
    return results


def resolve_map_paths(map_arg: str | Path) -> list[Path]:
    if str(map_arg) == "all":
        return DEFAULT_MAPS
    return [resolve_project_path(map_arg)]


def resolve_project_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def write_results_csv(results: list[dict[str, Any]], output: str | Path) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(results)


def print_summary(results: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault((str(result["map"]), str(result["agent"])), []).append(result)

    print("Experiment summary")
    for (map_name, agent_name), rows in grouped.items():
        final_scores = [float(row["final_score"]) for row in rows]
        deliveries = [float(row["deliveries"]) for row in rows]
        mean_score = statistics.fmean(final_scores)
        score_std = statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0
        mean_deliveries = statistics.fmean(deliveries)
        print(
            f"- {map_name}/{agent_name}: episodes={len(rows)}, "
            f"mean_final_score={mean_score:.2f}, std={score_std:.2f}, "
            f"mean_deliveries={mean_deliveries:.2f}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline agent experiments.")
    parser.add_argument(
        "--agent",
        default="all",
        choices=["all", *AGENT_CLASSES.keys()],
        help="Agent to run.",
    )
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-steps", type=int, default=1000)
    parser.add_argument("--map", default=str(DEFAULT_MAP_PATH))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_batch(
        agent_name=args.agent,
        episodes=args.episodes,
        seed=args.seed,
        output=args.output,
        max_steps=args.max_steps,
        map_arg=args.map,
        config_path=args.config,
    )
    print(f"Wrote {len(results)} rows to {args.output}")
    print_summary(results)


if __name__ == "__main__":
    main()
