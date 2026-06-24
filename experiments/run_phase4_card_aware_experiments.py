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

from agents.card_aware_greedy_agent import CardAwareGreedyAgent
from agents.mcts_agent import MCTSAgent
from agents.registry import create_agent
from experiments.run_experiments import write_results_csv
from experiments.simulation_runner import run_episode
from railways.environment import DEFAULT_CARDS_PATH, DEFAULT_CONFIG_PATH


DEFAULT_MAPS = [
    PROJECT_ROOT / "data" / "toy_map.json",
    PROJECT_ROOT / "data" / "toy_medium_map.json",
    PROJECT_ROOT / "data" / "semi_realistic_map.json",
]
DEFAULT_AGENTS = [
    "greedy_delivery",
    "greedy_expansion",
    "card_aware_greedy",
    "mcts",
    "mcts_majorline",
    "mcts_card_rollout",
    "mcts_majorline_card_rollout",
]
SUMMARY_COLUMNS = [
    "map",
    "agent",
    "episodes",
    "mean_final_score",
    "std_final_score",
    "mean_raw_score",
    "mean_major_line_bonus",
    "mean_operation_card_bonus",
    "mean_end_game_card_bonus",
    "mean_financing_penalty",
    "mean_cards_selected",
    "mean_cards_completed",
    "mean_invalid_actions",
    "mean_runtime_seconds",
]
DEFAULT_RAW_OUTPUT = (
    PROJECT_ROOT / "results" / "raw" / "phase4d_card_aware_results.csv"
)
DEFAULT_SUMMARY_CSV = (
    PROJECT_ROOT / "results" / "summary" / "phase4d_card_aware_summary.csv"
)
DEFAULT_SUMMARY_MD = (
    PROJECT_ROOT / "results" / "summary" / "phase4d_card_aware_summary.md"
)


def run_phase4d_card_aware_experiments(
    maps: list[str | Path] | None = None,
    agents: list[str] | None = None,
    episodes: int = 30,
    seed: int = 0,
    max_steps: int = 500,
    mcts_iterations: int = 25,
    mcts_rollout_depth: int = 40,
    output: str | Path = DEFAULT_RAW_OUTPUT,
    summary_csv: str | Path = DEFAULT_SUMMARY_CSV,
    summary_md: str | Path = DEFAULT_SUMMARY_MD,
) -> list[dict[str, Any]]:
    selected_maps = [Path(path) for path in (maps or DEFAULT_MAPS)]
    selected_agents = agents or DEFAULT_AGENTS
    rows: list[dict[str, Any]] = []

    for map_path in selected_maps:
        for agent_name in selected_agents:
            print(f"[card-enabled] {map_path.stem} / {agent_name}: {episodes} episodes")
            for episode_index in range(episodes):
                episode_seed = seed + episode_index
                agent = _create_phase4d_agent(
                    agent_name,
                    episode_seed,
                    mcts_iterations,
                    mcts_rollout_depth,
                )
                result = run_episode(
                    agent,
                    seed=episode_seed,
                    max_steps=max_steps,
                    map_path=map_path,
                    config_path=DEFAULT_CONFIG_PATH,
                    card_path=DEFAULT_CARDS_PATH,
                )
                result["agent"] = agent_name
                rows.append(result)

    write_results_csv(rows, output)
    summaries = summarise_phase4d_rows(rows)
    _write_csv(summaries, summary_csv, SUMMARY_COLUMNS)
    _write_summary_markdown(summaries, summary_md)
    return summaries


def summarise_phase4d_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["map"]), str(row["agent"])), []).append(row)

    summaries = [
        _summarise_group(map_name, agent, group)
        for (map_name, agent), group in grouped.items()
    ]
    summaries.sort(key=lambda row: (row["map"], row["agent"]))
    return summaries


def _summarise_group(
    map_name: str,
    agent: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    final_scores = _numbers(rows, "final_score")
    return {
        "map": map_name,
        "agent": agent,
        "episodes": len(rows),
        "mean_final_score": statistics.fmean(final_scores),
        "std_final_score": (
            statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0
        ),
        "mean_raw_score": statistics.fmean(_numbers(rows, "raw_score")),
        "mean_major_line_bonus": statistics.fmean(_numbers(rows, "major_line_bonus")),
        "mean_operation_card_bonus": statistics.fmean(
            _numbers(rows, "operation_card_bonus")
        ),
        "mean_end_game_card_bonus": statistics.fmean(
            _numbers(rows, "end_game_card_bonus")
        ),
        "mean_financing_penalty": statistics.fmean(
            _numbers(rows, "financing_penalty")
        ),
        "mean_cards_selected": statistics.fmean(_numbers(rows, "cards_selected")),
        "mean_cards_completed": statistics.fmean(_numbers(rows, "cards_completed")),
        "mean_invalid_actions": statistics.fmean(_numbers(rows, "invalid_actions")),
        "mean_runtime_seconds": statistics.fmean(_numbers(rows, "runtime_seconds")),
    }


def _numbers(rows: list[dict[str, Any]], column: str) -> list[float]:
    return [float(row[column]) for row in rows]


def _create_phase4d_agent(
    name: str,
    seed: int,
    mcts_iterations: int,
    mcts_rollout_depth: int,
):
    if name == "card_aware_greedy":
        return CardAwareGreedyAgent(seed=seed)
    if name == "mcts":
        return MCTSAgent(
            seed=seed,
            iterations=mcts_iterations,
            rollout_depth_limit=mcts_rollout_depth,
        )
    if name == "mcts_majorline":
        return MCTSAgent(
            seed=seed,
            iterations=mcts_iterations,
            rollout_depth_limit=mcts_rollout_depth,
            evaluation_mode="major_line_aware",
        )
    if name == "mcts_card_rollout":
        return MCTSAgent(
            seed=seed,
            iterations=mcts_iterations,
            rollout_depth_limit=mcts_rollout_depth,
            rollout_policy="card_aware",
        )
    if name == "mcts_majorline_card_rollout":
        return MCTSAgent(
            seed=seed,
            iterations=mcts_iterations,
            rollout_depth_limit=mcts_rollout_depth,
            rollout_policy="card_aware",
            evaluation_mode="major_line_aware",
        )
    return create_agent(name, seed=seed)


def _write_csv(
    rows: list[dict[str, Any]],
    output_path: str | Path,
    columns: list[str],
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary_markdown(
    rows: list[dict[str, Any]],
    output_path: str | Path,
) -> None:
    lines = [
        "# Phase 4D Card-Aware Agent Summary",
        "",
        "| map | agent | episodes | mean final | std | raw | major line | op card | end card | financing penalty | cards selected | cards completed | invalid | runtime (s) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['map']} | "
            f"{row['agent']} | "
            f"{row['episodes']} | "
            f"{row['mean_final_score']:.2f} | "
            f"{row['std_final_score']:.2f} | "
            f"{row['mean_raw_score']:.2f} | "
            f"{row['mean_major_line_bonus']:.2f} | "
            f"{row['mean_operation_card_bonus']:.2f} | "
            f"{row['mean_end_game_card_bonus']:.2f} | "
            f"{row['mean_financing_penalty']:.2f} | "
            f"{row['mean_cards_selected']:.2f} | "
            f"{row['mean_cards_completed']:.2f} | "
            f"{row['mean_invalid_actions']:.2f} | "
            f"{row['mean_runtime_seconds']:.4f} |"
        )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 4D card-aware agent experiments."
    )
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--mcts-iterations", type=int, default=25)
    parser.add_argument("--mcts-rollout-depth", type=int, default=40)
    parser.add_argument("--maps", default=",".join(str(path) for path in DEFAULT_MAPS))
    parser.add_argument("--agents", default=",".join(DEFAULT_AGENTS))
    parser.add_argument("--output", default=str(DEFAULT_RAW_OUTPUT))
    parser.add_argument("--summary-csv", default=str(DEFAULT_SUMMARY_CSV))
    parser.add_argument("--summary-md", default=str(DEFAULT_SUMMARY_MD))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = run_phase4d_card_aware_experiments(
        maps=_parse_list(args.maps),
        agents=_parse_list(args.agents),
        episodes=args.episodes,
        seed=args.seed,
        max_steps=args.max_steps,
        mcts_iterations=args.mcts_iterations,
        mcts_rollout_depth=args.mcts_rollout_depth,
        output=args.output,
        summary_csv=args.summary_csv,
        summary_md=args.summary_md,
    )
    print(f"Wrote {len(summaries)} Phase 4D summary rows.")
    print(f"raw: {args.output}")
    print(f"summary_csv: {args.summary_csv}")
    print(f"summary_md: {args.summary_md}")


if __name__ == "__main__":
    main()
