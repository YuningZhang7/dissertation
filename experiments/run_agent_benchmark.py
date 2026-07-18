from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import statistics
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import create_agent, list_agent_names
from railways.actions import Action
from railways.environment import (
    apply_action,
    get_legal_actions,
    is_terminal,
    reset_game,
)


MAP_PATHS = {
    "official_like": PROJECT_ROOT / "data" / "official_like_route_segment_map.json",
    "expanded": PROJECT_ROOT
    / "data"
    / "expanded_official_style_route_segment_map.json",
}
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "results" / "agent_benchmark"
DEFAULT_AGENTS = (
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "objective_aware_greedy",
    "urbanization_aware_lookahead_greedy",
    "presentation_lookahead_greedy",
)
# Keep --quick lightweight; the depth-2 urbanization-aware agent is covered by
# its focused smoke test and can be selected explicitly for benchmark runs.
QUICK_AGENTS = (
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "objective_aware_greedy",
)
CSV_COLUMNS = [
    "map_name",
    "agent_name",
    "episode",
    "seed",
    "steps",
    "terminal",
    "success",
    "error",
    "final_score",
    "score",
    "money",
    "bonds",
    "locomotive_level",
    "delivered_goods_count",
    "major_line_bonus",
    "rail_baron_bonus",
    "rail_baron_objectives_completed",
    "claimed_major_lines_count",
    "completed_routes_count",
    "built_segments_count",
    "completed_segments_count",
    "empty_marker_count",
    "fallback_actions",
    "runtime_seconds",
    "delivery_actions",
    "build_actions",
    "upgrade_actions",
    "urbanize_actions",
    "pass_actions",
    "issue_bond_actions",
    "next_turn_actions",
    "failed_actions",
    "total_actions",
    "total_build_cost_estimate",
    "bonds_issued_during_episode",
    "score_delta",
    "final_score_per_step",
    "deliveries_per_bond",
    "completed_routes_per_bond",
    "major_line_claim_events",
    "rail_baron_claim_events",
    "urbanized_city_count",
]


def run_benchmark_episode(
    map_name: str,
    agent_name: str,
    episode: int,
    seed: int,
    max_steps: int,
    config_path: str | Path = CONFIG_PATH,
) -> dict[str, Any]:
    random.seed(seed)
    state = reset_game(map_path=MAP_PATHS[map_name], config_path=config_path)
    agent = create_agent(agent_name, seed=seed)
    steps = 0
    fallback_actions = 0
    success = True
    error = ""
    initial_bonds = state.player.bonds
    initial_score = state.player.score
    initial_major_claims = sum(line.claimed for line in state.major_lines.values())
    initial_rail_claims = state.player.rail_baron_objectives_completed
    initial_gray_city_ids = {
        city_id for city_id, city in state.cities.items() if city.is_gray
    }
    action_counts = {
        name: 0
        for name in (
            "delivery_actions",
            "build_actions",
            "upgrade_actions",
            "urbanize_actions",
            "pass_actions",
            "issue_bond_actions",
            "next_turn_actions",
        )
    }
    failed_actions = 0
    total_build_cost_estimate = 0
    started = time.perf_counter()
    try:
        while not is_terminal(state) and steps < max_steps:
            legal_actions = get_legal_actions(state)
            if not legal_actions:
                break
            try:
                action = agent.choose_action(state)
            except Exception as exc:
                success = False
                error = f"{type(exc).__name__}: {exc}"
                break
            if action is None or action not in legal_actions:
                fallback_actions += 1
                action = Action.pass_action()
            count_key = {
                "deliver_good": "delivery_actions",
                "build_track_segments": "build_actions",
                "upgrade_engine": "upgrade_actions",
                "urbanize": "urbanize_actions",
                "pass": "pass_actions",
                "issue_bond": "issue_bond_actions",
                "next_turn": "next_turn_actions",
            }.get(action.action_type)
            if count_key:
                action_counts[count_key] += 1
            if action.action_type == "build_track_segments":
                total_build_cost_estimate += sum(
                    state.segments[item].cost
                    for item in action.params.get("segment_ids", [])
                    if item in state.segments
                )
            _, applied, message = apply_action(state, action)
            if not applied:
                failed_actions += 1
                fallback_actions += 1
                fallback = Action.pass_action()
                if fallback not in get_legal_actions(state):
                    success = False
                    error = f"Action failed and no pass fallback was legal: {message}"
                    break
                _, fallback_applied, fallback_message = apply_action(state, fallback)
                if not fallback_applied:
                    success = False
                    error = f"Pass fallback failed: {fallback_message}"
                    break
            steps += 1
    except Exception as exc:
        success = False
        error = f"{type(exc).__name__}: {exc}"
    runtime_seconds = time.perf_counter() - started
    completed_routes = sum(route.completed for route in state.routes.values())
    final_bonds = state.player.bonds
    result = {
        "map_name": map_name,
        "agent_name": agent_name,
        "episode": episode,
        "seed": seed,
        "steps": steps,
        "terminal": is_terminal(state),
        "success": success,
        "error": error,
        "final_score": state.final_score(),
        "score": state.player.score,
        "money": state.player.money,
        "bonds": state.player.bonds,
        "locomotive_level": state.player.locomotive_level,
        "delivered_goods_count": state.player.delivered_goods_count,
        "major_line_bonus": state.player.major_line_bonus,
        "rail_baron_bonus": state.player.rail_baron_bonus,
        "rail_baron_objectives_completed": state.player.rail_baron_objectives_completed,
        "claimed_major_lines_count": sum(
            line.claimed for line in state.major_lines.values()
        ),
        "completed_routes_count": completed_routes,
        "built_segments_count": sum(
            segment.built for segment in state.segments.values()
        ),
        "completed_segments_count": sum(
            segment.completed for segment in state.segments.values()
        ),
        "empty_marker_count": sum(city.empty_marker for city in state.cities.values()),
        "fallback_actions": fallback_actions,
        "runtime_seconds": runtime_seconds,
        **action_counts,
        "failed_actions": failed_actions,
        "total_actions": sum(action_counts.values()),
        "total_build_cost_estimate": total_build_cost_estimate,
        "bonds_issued_during_episode": final_bonds - initial_bonds,
        "score_delta": state.player.score - initial_score,
        "final_score_per_step": state.final_score() / max(1, steps),
        "deliveries_per_bond": state.player.delivered_goods_count / max(1, final_bonds),
        "completed_routes_per_bond": completed_routes / max(1, final_bonds),
        "major_line_claim_events": sum(
            line.claimed for line in state.major_lines.values()
        )
        - initial_major_claims,
        "rail_baron_claim_events": (
            state.player.rail_baron_objectives_completed - initial_rail_claims
        ),
        "urbanized_city_count": sum(
            not state.cities[city_id].is_gray
            and state.cities[city_id].is_urbanized
            for city_id in initial_gray_city_ids
            if city_id in state.cities
        ),
    }
    return result


def summarise_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    summary: dict[str, dict[str, dict[str, Any]]] = {}
    for map_name in sorted({str(row["map_name"]) for row in rows}):
        summary[map_name] = {}
        map_rows = [row for row in rows if row["map_name"] == map_name]
        for agent_name in sorted({str(row["agent_name"]) for row in map_rows}):
            group = [row for row in map_rows if row["agent_name"] == agent_name]
            finals = [float(row["final_score"]) for row in group]
            metrics: dict[str, Any] = {
                "episodes": len(group),
                "success_rate": statistics.fmean(bool(row["success"]) for row in group),
                "mean_final_score": statistics.fmean(finals),
                "median_final_score": statistics.median(finals),
                "best_final_score": max(finals),
                "worst_final_score": min(finals),
                "std_final_score": statistics.stdev(finals) if len(finals) > 1 else 0.0,
            }
            for field in (
                "score",
                "money",
                "bonds",
                "delivered_goods_count",
                "major_line_bonus",
                "rail_baron_bonus",
                "rail_baron_objectives_completed",
                "claimed_major_lines_count",
                "completed_routes_count",
                "built_segments_count",
                "completed_segments_count",
                "empty_marker_count",
                "steps",
                "fallback_actions",
                "runtime_seconds",
                "delivery_actions",
                "build_actions",
                "upgrade_actions",
                "urbanize_actions",
                "pass_actions",
                "issue_bond_actions",
                "failed_actions",
                "total_actions",
                "total_build_cost_estimate",
                "bonds_issued_during_episode",
                "score_delta",
                "final_score_per_step",
                "deliveries_per_bond",
                "completed_routes_per_bond",
                "major_line_claim_events",
                "rail_baron_claim_events",
                "urbanized_city_count",
            ):
                metrics[f"mean_{field}"] = statistics.fmean(
                    float(row[field]) for row in group
                )
            summary[map_name][agent_name] = metrics
        _add_ranks(summary[map_name])
    return summary


def _add_ranks(groups: dict[str, dict[str, Any]]) -> None:
    rank_specs = (
        ("mean_final_score", "rank_by_mean_final_score", True),
        ("mean_bonds", "rank_by_mean_bonds", False),
        ("mean_delivered_goods_count", "rank_by_mean_delivered_goods_count", True),
    )
    for metric, rank_field, descending in rank_specs:
        ordered = sorted(
            groups,
            key=lambda name: (
                -groups[name][metric] if descending else groups[name][metric],
                name,
            ),
        )
        for rank, name in enumerate(ordered, 1):
            groups[name][rank_field] = rank


def write_outputs(
    rows: list[dict[str, Any]],
    summary: dict[str, dict[str, dict[str, Any]]],
    output_dir: str | Path,
    settings: dict[str, Any],
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "benchmark_rows.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (output / "benchmark_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "benchmark_summary.md").write_text(
        _markdown_summary(summary, settings),
        encoding="utf-8",
    )
    return output


def _markdown_summary(
    summary: dict[str, dict[str, dict[str, Any]]],
    settings: dict[str, Any],
) -> str:
    lines = [
        "# Agent Benchmark Summary",
        "",
        "## Settings",
        "",
        f"- Maps: {', '.join(settings['maps'])}",
        f"- Agents: {', '.join(settings['agents'])}",
        f"- Episodes per map-agent pair: {settings['episodes']}",
        f"- Maximum steps: {settings['max_steps']}",
        f"- Base seed: {settings['base_seed']}",
        f"- Config path: {settings['config_path']}",
        "",
    ]
    headers = (
        "Agent | Mean Final | Median Final | Best | Worst | Mean Deliveries | "
        "Mean Bonds | Mean Major Bonus | Mean Rail Baron Bonus | Mean Routes | "
        "Success Rate | Mean Runtime"
    )
    for map_name, agents in summary.items():
        lines.extend([f"## {map_name}", "", f"| {headers} |", "|" + " --- |" * 12])
        for agent_name, item in agents.items():
            lines.append(
                "| "
                + " | ".join(
                    [
                        agent_name,
                        f"{item['mean_final_score']:.2f}",
                        f"{item['median_final_score']:.2f}",
                        f"{item['best_final_score']:.0f}",
                        f"{item['worst_final_score']:.0f}",
                        f"{item['mean_delivered_goods_count']:.2f}",
                        f"{item['mean_bonds']:.2f}",
                        f"{item['mean_major_line_bonus']:.2f}",
                        f"{item['mean_rail_baron_bonus']:.2f}",
                        f"{item['mean_completed_routes_count']:.2f}",
                        f"{item['success_rate']:.2%}",
                        f"{item['mean_runtime_seconds']:.4f}s",
                    ]
                )
                + " |"
            )
        lines.extend(
            [
                "",
                "### Behaviour diagnostics",
                "",
                "| Agent | Build Actions | Delivery Actions | Upgrade Actions | Urbanize Actions | Urbanized Cities | Pass Actions | Bonds Issued | Build Cost | Final / Step | Deliveries / Bond | Routes / Bond | Failed Actions |",
                "|" + " --- |" * 13,
            ]
        )
        for agent_name, item in agents.items():
            lines.append(
                "| "
                + " | ".join(
                    [
                        agent_name,
                        f"{item['mean_build_actions']:.2f}",
                        f"{item['mean_delivery_actions']:.2f}",
                        f"{item['mean_upgrade_actions']:.2f}",
                        f"{item['mean_urbanize_actions']:.2f}",
                        f"{item['mean_urbanized_city_count']:.2f}",
                        f"{item['mean_pass_actions']:.2f}",
                        f"{item['mean_bonds_issued_during_episode']:.2f}",
                        f"{item['mean_total_build_cost_estimate']:.2f}",
                        f"{item['mean_final_score_per_step']:.3f}",
                        f"{item['mean_deliveries_per_bond']:.3f}",
                        f"{item['mean_completed_routes_per_bond']:.3f}",
                        f"{item['mean_failed_actions']:.2f}",
                    ]
                )
                + " |"
            )
        best = min(agents, key=lambda name: agents[name]["rank_by_mean_final_score"])
        lowest_bonds = min(agents, key=lambda name: agents[name]["rank_by_mean_bonds"])
        most_deliveries = min(
            agents,
            key=lambda name: agents[name]["rank_by_mean_delivered_goods_count"],
        )
        lines.extend(
            [
                "",
                "### Automatic observations",
                "",
                f"- Best mean final score: {best}.",
                f"- Lowest mean bonds: {lowest_bonds}.",
                f"- Most deliveries: {most_deliveries}.",
            ]
        )
        objective = agents.get("objective_aware_greedy")
        lookahead = agents.get("urbanization_aware_lookahead_greedy")
        if lookahead and objective and lookahead["mean_runtime_seconds"] > objective["mean_runtime_seconds"]:
            lines.append(
                "- urbanization_aware_lookahead_greedy is slower than the one-step objective-aware baseline."
            )
        lines.append("")
    lines.extend(
        [
            "These are development benchmark diagnostics, not final dissertation conclusions.",
            "",
        ]
    )
    return "\n".join(lines)


def run_benchmark(
    maps: list[str],
    agents: list[str],
    episodes: int = 10,
    max_steps: int = 100,
    base_seed: int = 42,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    config_path: str | Path = CONFIG_PATH,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, dict[str, Any]]], Path]:
    unknown_maps = sorted(set(maps) - set(MAP_PATHS))
    unknown_agents = sorted(set(agents) - set(list_agent_names()))
    if unknown_maps:
        raise ValueError(f"Unknown benchmark maps: {', '.join(unknown_maps)}")
    if unknown_agents:
        raise ValueError(f"Unknown benchmark agents: {', '.join(unknown_agents)}")
    if episodes <= 0 or max_steps <= 0:
        raise ValueError("episodes and max_steps must be positive")
    rows = [
        run_benchmark_episode(
            map_name, agent_name, index + 1, base_seed + index, max_steps, config_path
        )
        for map_name in maps
        for agent_name in agents
        for index in range(episodes)
    ]
    summary = summarise_rows(rows)
    settings = {
        "maps": maps,
        "agents": agents,
        "episodes": episodes,
        "max_steps": max_steps,
        "base_seed": base_seed,
        "config_path": str(config_path),
    }
    return rows, summary, write_outputs(rows, summary, output_dir, settings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run reproducible multi-seed agent benchmarks."
    )
    parser.add_argument("--maps", nargs="+", default=list(MAP_PATHS))
    parser.add_argument("--agents", nargs="+")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--base-seed", type=int, default=42)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--include-random", action="store_true")
    parser.add_argument("--quick", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    agents = list(args.agents or (QUICK_AGENTS if args.quick else DEFAULT_AGENTS))
    if args.include_random and "random" not in agents:
        agents.insert(0, "random")
    episodes = 2 if args.quick else args.episodes
    max_steps = 20 if args.quick else args.max_steps
    rows, summary, output = run_benchmark(
        args.maps, agents, episodes, max_steps, args.base_seed, args.output_dir
    )
    print(
        f"Wrote {len(rows)} episode rows and "
        f"{sum(map(len, summary.values()))} groups to {output}"
    )


if __name__ == "__main__":
    main()
