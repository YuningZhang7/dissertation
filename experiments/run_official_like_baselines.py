from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import statistics
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import create_agent
from railways.actions import Action
from railways.environment import (
    apply_action,
    get_legal_actions,
    is_terminal,
    reset_game,
)


OFFICIAL_LIKE_MAP = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "results"
DEFAULT_OUTPUT_CSV = DEFAULT_OUTPUT_DIR / "official_like_baselines.csv"
DEFAULT_OUTPUT_SUMMARY = (
    DEFAULT_OUTPUT_DIR / "official_like_baselines_summary.json"
)
BASELINE_AGENT_NAMES = (
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "route_segment_greedy",
    "objective_aware_greedy",
    "adaptive_objective_greedy",
)
CSV_COLUMNS = [
    "agent_name",
    "episode",
    "seed",
    "steps",
    "terminal",
    "final_score",
    "money",
    "bonds",
    "locomotive_level",
    "delivered_goods_count",
    "major_line_bonus",
    "active_rail_baron_objective_id",
    "rail_baron_bonus",
    "rail_baron_objectives_completed",
    "claimed_major_lines_count",
    "completed_routes_count",
    "built_segments_count",
    "completed_segments_count",
    "empty_marker_count",
    "fallback_actions",
    "success",
    "error",
]


def run_official_like_episode(
    agent_name: str,
    episode: int,
    seed: int,
    max_steps: int,
    map_path: str | Path = OFFICIAL_LIKE_MAP,
    config_path: str | Path = OFFICIAL_CONFIG,
) -> dict[str, Any]:
    random.seed(seed)
    state = reset_game(map_path=map_path, config_path=config_path)
    agent = create_agent(agent_name, seed=seed)
    steps = 0
    fallback_actions = 0
    episode_success = True
    error = ""

    try:
        while not is_terminal(state) and steps < max_steps:
            legal_actions = get_legal_actions(state)
            if not legal_actions:
                break

            try:
                action = agent.choose_action(state)
            except Exception as exc:
                episode_success = False
                error = f"{type(exc).__name__}: {exc}"
                break

            if action is None or action not in legal_actions:
                fallback_actions += 1
                action = Action.pass_action()

            _, applied, message = apply_action(state, action)
            if not applied:
                fallback_actions += 1
                fallback = Action.pass_action()
                if fallback not in get_legal_actions(state):
                    episode_success = False
                    error = f"Action failed and no pass fallback was legal: {message}"
                    break
                _, fallback_applied, fallback_message = apply_action(state, fallback)
                if not fallback_applied:
                    episode_success = False
                    error = f"Pass fallback failed: {fallback_message}"
                    break

            steps += 1
    except Exception as exc:
        episode_success = False
        error = f"{type(exc).__name__}: {exc}"

    return {
        "agent_name": agent_name,
        "episode": episode,
        "seed": seed,
        "steps": steps,
        "terminal": is_terminal(state),
        "final_score": state.final_score(),
        "money": state.player.money,
        "bonds": state.player.bonds,
        "locomotive_level": state.player.locomotive_level,
        "delivered_goods_count": state.player.delivered_goods_count,
        "major_line_bonus": state.player.major_line_bonus,
        "active_rail_baron_objective_id": (
            state.active_rail_baron_objective_id or ""
        ),
        "rail_baron_bonus": state.player.rail_baron_bonus,
        "rail_baron_objectives_completed": (
            state.player.rail_baron_objectives_completed
        ),
        "claimed_major_lines_count": sum(
            1 for line in state.major_lines.values() if line.claimed
        ),
        "completed_routes_count": sum(
            1 for route in state.routes.values() if route.completed
        ),
        "built_segments_count": sum(
            1 for segment in state.segments.values() if segment.built
        ),
        "completed_segments_count": sum(
            1 for segment in state.segments.values() if segment.completed
        ),
        "empty_marker_count": sum(
            1 for city in state.cities.values() if city.empty_marker
        ),
        "fallback_actions": fallback_actions,
        "success": episode_success,
        "error": error,
    }


def summarise_results(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, int | float]]:
    summary: dict[str, dict[str, int | float]] = {}
    for agent_name in BASELINE_AGENT_NAMES:
        agent_rows = [row for row in rows if row["agent_name"] == agent_name]
        if not agent_rows:
            continue

        summary[agent_name] = {
            "episodes": len(agent_rows),
            "mean_final_score": statistics.fmean(
                float(row["final_score"]) for row in agent_rows
            ),
            "best_final_score": max(int(row["final_score"]) for row in agent_rows),
            "mean_delivered_goods_count": statistics.fmean(
                float(row["delivered_goods_count"]) for row in agent_rows
            ),
            "mean_completed_routes_count": statistics.fmean(
                float(row["completed_routes_count"]) for row in agent_rows
            ),
            "mean_bonds": statistics.fmean(
                float(row["bonds"]) for row in agent_rows
            ),
            "mean_steps": statistics.fmean(
                float(row["steps"]) for row in agent_rows
            ),
            "success_rate": statistics.fmean(
                1.0 if bool(row["success"]) else 0.0 for row in agent_rows
            ),
        }
    return summary


def write_results_csv(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_json(
    summary: dict[str, dict[str, int | float]],
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, sort_keys=True)
        file.write("\n")


def run_baseline_experiment(
    episodes_per_agent: int = 20,
    max_steps_per_episode: int = 300,
    base_seed: int = 42,
    output_csv: str | Path = DEFAULT_OUTPUT_CSV,
    output_summary: str | Path = DEFAULT_OUTPUT_SUMMARY,
    map_path: str | Path = OFFICIAL_LIKE_MAP,
    config_path: str | Path = OFFICIAL_CONFIG,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int | float]]]:
    if episodes_per_agent <= 0:
        raise ValueError("episodes_per_agent must be positive.")
    if max_steps_per_episode <= 0:
        raise ValueError("max_steps_per_episode must be positive.")

    rows: list[dict[str, Any]] = []
    for agent_name in BASELINE_AGENT_NAMES:
        for episode_index in range(episodes_per_agent):
            episode_seed = base_seed + episode_index
            rows.append(
                run_official_like_episode(
                    agent_name=agent_name,
                    episode=episode_index + 1,
                    seed=episode_seed,
                    max_steps=max_steps_per_episode,
                    map_path=map_path,
                    config_path=config_path,
                )
            )

    summary = summarise_results(rows)
    write_results_csv(rows, output_csv)
    write_summary_json(summary, output_summary)
    return rows, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate baseline agents on the official-like route scenario."
    )
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-summary", default=str(DEFAULT_OUTPUT_SUMMARY))
    parser.add_argument("--map-path", default=str(OFFICIAL_LIKE_MAP))
    parser.add_argument("--config-path", default=str(OFFICIAL_CONFIG))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows, summary = run_baseline_experiment(
        episodes_per_agent=args.episodes,
        max_steps_per_episode=args.max_steps,
        base_seed=args.seed,
        output_csv=args.output_csv,
        output_summary=args.output_summary,
        map_path=args.map_path,
        config_path=args.config_path,
    )
    print(f"Wrote {len(rows)} episode rows to {args.output_csv}")
    print(f"Wrote {len(summary)} agent summaries to {args.output_summary}")
    for agent_name, metrics in summary.items():
        print(
            f"- {agent_name}: mean_final_score="
            f"{metrics['mean_final_score']:.2f}, "
            f"mean_deliveries={metrics['mean_delivered_goods_count']:.2f}, "
            f"success_rate={metrics['success_rate']:.2f}"
        )


if __name__ == "__main__":
    main()
