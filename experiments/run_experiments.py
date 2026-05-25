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

DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "raw" / "experiment_results.csv"
CSV_COLUMNS = [
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
) -> list[dict[str, Any]]:
    agent_names = list(AGENT_CLASSES) if agent_name == "all" else [agent_name]
    results: list[dict[str, Any]] = []

    for name in agent_names:
        for episode_index in range(episodes):
            episode_seed = seed + episode_index
            agent = create_agent(name, seed=episode_seed)
            result = run_episode(agent, seed=episode_seed, max_steps=max_steps)
            results.append(result)

    write_results_csv(results, output)
    return results


def write_results_csv(results: list[dict[str, Any]], output: str | Path) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(results)


def print_summary(results: list[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(str(result["agent"]), []).append(result)

    print("Experiment summary")
    for agent_name, rows in grouped.items():
        final_scores = [float(row["final_score"]) for row in rows]
        deliveries = [float(row["deliveries"]) for row in rows]
        mean_score = statistics.fmean(final_scores)
        score_std = statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0
        mean_deliveries = statistics.fmean(deliveries)
        print(
            f"- {agent_name}: episodes={len(rows)}, "
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_batch(
        agent_name=args.agent,
        episodes=args.episodes,
        seed=args.seed,
        output=args.output,
        max_steps=args.max_steps,
    )
    print(f"Wrote {len(results)} rows to {args.output}")
    print_summary(results)


if __name__ == "__main__":
    main()
