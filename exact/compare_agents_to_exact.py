from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.greedy_expansion_agent import GreedyExpansionAgent
from agents.mcts_agent import MCTSAgent
from agents.random_agent import RandomAgent
from exact.run_exact_benchmark import DEFAULT_CONFIG, DEFAULT_MAP, DEFAULT_OUTPUT, run_exact_benchmark
from experiments.simulation_runner import run_episode

DEFAULT_COMPARISON_CSV = (
    PROJECT_ROOT / "results" / "exact_benchmark" / "micro_map_agent_comparison.csv"
)
DEFAULT_COMPARISON_MD = (
    PROJECT_ROOT / "results" / "exact_benchmark" / "micro_map_agent_comparison.md"
)
COMPARISON_COLUMNS = [
    "agent",
    "episodes",
    "mean_score",
    "std_score",
    "min_score",
    "max_score",
    "exact_optimum",
    "absolute_gap",
    "relative_gap_percent",
    "mean_runtime_seconds",
]


def compare_agents_to_exact(
    map_path: str | Path = DEFAULT_MAP,
    config_path: str | Path = DEFAULT_CONFIG,
    exact_result_path: str | Path = DEFAULT_OUTPUT,
    output_csv: str | Path = DEFAULT_COMPARISON_CSV,
    output_md: str | Path = DEFAULT_COMPARISON_MD,
    random_episodes: int = 30,
    mcts_episodes: int = 20,
    seed: int = 0,
    mcts_small_iterations: int = 25,
    mcts_large_iterations: int = 100,
    use_existing_exact: bool = False,
) -> list[dict[str, Any]]:
    exact_payload = _load_or_run_exact(
        map_path,
        config_path,
        exact_result_path,
        use_existing=use_existing_exact,
    )
    exact_optimum = float(exact_payload["optimal_final_score"])

    rows: list[dict[str, Any]] = [
        _exact_row(exact_payload),
        _evaluate_agent(
            "random",
            lambda episode_seed: RandomAgent(seed=episode_seed),
            random_episodes,
            seed,
            map_path,
            config_path,
            exact_optimum,
        ),
        _evaluate_agent(
            "greedy_delivery",
            lambda episode_seed: GreedyDeliveryAgent(seed=episode_seed),
            1,
            seed,
            map_path,
            config_path,
            exact_optimum,
        ),
        _evaluate_agent(
            "greedy_expansion",
            lambda episode_seed: GreedyExpansionAgent(seed=episode_seed),
            1,
            seed,
            map_path,
            config_path,
            exact_optimum,
        ),
        _evaluate_agent(
            f"mcts_{mcts_small_iterations}",
            lambda episode_seed: MCTSAgent(
                seed=episode_seed,
                iterations=mcts_small_iterations,
                rollout_depth_limit=40,
                action_generation="full",
            ),
            mcts_episodes,
            seed,
            map_path,
            config_path,
            exact_optimum,
        ),
        _evaluate_agent(
            f"mcts_{mcts_large_iterations}",
            lambda episode_seed: MCTSAgent(
                seed=episode_seed,
                iterations=mcts_large_iterations,
                rollout_depth_limit=40,
                action_generation="full",
            ),
            mcts_episodes,
            seed,
            map_path,
            config_path,
            exact_optimum,
        ),
        _evaluate_agent(
            f"mcts_{mcts_small_iterations}_majorline",
            lambda episode_seed: MCTSAgent(
                seed=episode_seed,
                iterations=mcts_small_iterations,
                rollout_depth_limit=40,
                action_generation="full",
                evaluation_mode="major_line_aware",
            ),
            mcts_episodes,
            seed,
            map_path,
            config_path,
            exact_optimum,
        ),
        _evaluate_agent(
            f"mcts_{mcts_large_iterations}_majorline",
            lambda episode_seed: MCTSAgent(
                seed=episode_seed,
                iterations=mcts_large_iterations,
                rollout_depth_limit=40,
                action_generation="full",
                evaluation_mode="major_line_aware",
            ),
            mcts_episodes,
            seed,
            map_path,
            config_path,
            exact_optimum,
        ),
    ]

    _write_csv(rows, output_csv)
    _write_markdown(rows, output_md)
    return rows


def _load_or_run_exact(
    map_path: str | Path,
    config_path: str | Path,
    exact_result_path: str | Path,
    use_existing: bool,
) -> dict[str, Any]:
    path = Path(exact_result_path)
    if use_existing and path.exists():
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    return run_exact_benchmark(map_path, config_path, path)


def _exact_row(payload: dict[str, Any]) -> dict[str, Any]:
    optimum = float(payload["optimal_final_score"])
    return {
        "agent": "exact_optimum",
        "episodes": 1,
        "mean_score": optimum,
        "std_score": 0.0,
        "min_score": optimum,
        "max_score": optimum,
        "exact_optimum": optimum,
        "absolute_gap": 0.0,
        "relative_gap_percent": 0.0,
        "mean_runtime_seconds": float(payload["runtime_seconds"]),
    }


def _evaluate_agent(
    name: str,
    agent_factory,
    episodes: int,
    seed: int,
    map_path: str | Path,
    config_path: str | Path,
    exact_optimum: float,
) -> dict[str, Any]:
    scores: list[float] = []
    runtimes: list[float] = []

    for episode_index in range(episodes):
        episode_seed = seed + episode_index
        result = run_episode(
            agent_factory(episode_seed),
            seed=episode_seed,
            map_path=map_path,
            config_path=config_path,
            max_steps=200,
        )
        scores.append(float(result["final_score"]))
        runtimes.append(float(result["runtime_seconds"]))

    mean_score = statistics.fmean(scores)
    absolute_gap = exact_optimum - mean_score
    relative_gap_percent = (
        None
        if exact_optimum == 0
        else 100.0 * absolute_gap / abs(exact_optimum)
    )
    return {
        "agent": name,
        "episodes": episodes,
        "mean_score": mean_score,
        "std_score": statistics.stdev(scores) if len(scores) > 1 else 0.0,
        "min_score": min(scores),
        "max_score": max(scores),
        "exact_optimum": exact_optimum,
        "absolute_gap": absolute_gap,
        "relative_gap_percent": relative_gap_percent,
        "mean_runtime_seconds": statistics.fmean(runtimes),
    }


def _write_csv(rows: list[dict[str, Any]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COMPARISON_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(rows: list[dict[str, Any]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Micro-map Agent Comparison",
        "",
        "| agent | episodes | mean_score | std_score | min | max | exact_optimum | absolute_gap | relative_gap_percent | mean_runtime_seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        relative_gap = row["relative_gap_percent"]
        relative_text = "" if relative_gap is None else f"{relative_gap:.2f}"
        lines.append(
            "| "
            f"{row['agent']} | "
            f"{row['episodes']} | "
            f"{row['mean_score']:.2f} | "
            f"{row['std_score']:.2f} | "
            f"{row['min_score']:.2f} | "
            f"{row['max_score']:.2f} | "
            f"{row['exact_optimum']:.2f} | "
            f"{row['absolute_gap']:.2f} | "
            f"{relative_text} | "
            f"{row['mean_runtime_seconds']:.4f} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_comparison(rows: list[dict[str, Any]]) -> None:
    print("Agent comparison against exact optimum")
    for row in rows:
        relative_gap = row["relative_gap_percent"]
        relative_text = "n/a" if relative_gap is None else f"{relative_gap:.2f}%"
        print(
            f"- {row['agent']}: mean={row['mean_score']:.2f}, "
            f"gap={row['absolute_gap']:.2f}, relative_gap={relative_text}, "
            f"episodes={row['episodes']}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare existing agents to the exact micro-map optimum."
    )
    parser.add_argument("--map", default=str(DEFAULT_MAP))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--exact-result", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--output-csv", default=str(DEFAULT_COMPARISON_CSV))
    parser.add_argument("--output-md", default=str(DEFAULT_COMPARISON_MD))
    parser.add_argument("--random-episodes", type=int, default=30)
    parser.add_argument("--mcts-episodes", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mcts-small-iterations", type=int, default=25)
    parser.add_argument("--mcts-large-iterations", type=int, default=100)
    parser.add_argument(
        "--use-existing-exact",
        action="store_true",
        help="Reuse an existing exact-result JSON instead of recomputing it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = compare_agents_to_exact(
        map_path=args.map,
        config_path=args.config,
        exact_result_path=args.exact_result,
        output_csv=args.output_csv,
        output_md=args.output_md,
        random_episodes=args.random_episodes,
        mcts_episodes=args.mcts_episodes,
        seed=args.seed,
        mcts_small_iterations=args.mcts_small_iterations,
        mcts_large_iterations=args.mcts_large_iterations,
        use_existing_exact=args.use_existing_exact,
    )
    print_comparison(rows)
    print(f"Wrote {args.output_csv}")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
