from __future__ import annotations

import csv
from pathlib import Path
import random
import statistics
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import create_agent
from railways.environment import apply_action, get_legal_actions, is_terminal, reset_game


AGENTS = (
    "objective_aware_greedy",
    "presentation_lookahead_greedy",
)
MAP_PATH = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
OUTPUT_DIR = PROJECT_ROOT / "experiments" / "results" / "presentation_lookahead_diagnosis"
TRACE_COLUMNS = [
    "agent_name",
    "seed",
    "step",
    "action_type",
    "score",
    "money",
    "bonds",
    "delivered_goods_count",
    "completed_routes_count",
    "urbanized_city_count",
]
TUNING_SUMMARY_COLUMNS = [
    "agent_name",
    "runs",
    "mean_final_score",
    "median_final_score",
    "mean_deliveries",
    "mean_completed_routes",
    "mean_bonds",
    "mean_urbanize_actions",
    "mean_first20_urbanize",
    "success_count",
    "fallback_count",
]


def run_diagnosis(seed: int = 42, max_steps: int = 60) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for agent_name in AGENTS:
        agent_rows, summary = _run_agent_trace(agent_name, seed=seed, max_steps=max_steps)
        rows.extend(agent_rows)
        summaries.append(summary)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "presentation_lookahead_trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=TRACE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    _write_markdown(summaries, OUTPUT_DIR / "presentation_lookahead_diagnosis.md")
    return rows, summaries


def run_balanced_tuning_comparison(
    seeds: range = range(10),
    max_steps: int = 60,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    run_summaries: list[dict[str, Any]] = []
    for seed in seeds:
        for agent_name in AGENTS:
            agent_rows, summary = _run_agent_trace(
                agent_name,
                seed=seed,
                max_steps=max_steps,
            )
            rows.extend(agent_rows)
            run_summaries.append(summary)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trace_path = OUTPUT_DIR / "balanced_tuning_trace.csv"
    with trace_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=TRACE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = _summarize_runs(run_summaries)
    _write_tuning_summary_markdown(
        summary_rows,
        OUTPUT_DIR / "balanced_tuning_summary.md",
        seeds=seeds,
        max_steps=max_steps,
    )
    return rows, summary_rows


def _run_agent_trace(
    agent_name: str,
    *,
    seed: int,
    max_steps: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    random.seed(seed)
    state = reset_game(MAP_PATH, CONFIG_PATH)
    agent = create_agent(agent_name, seed=seed)
    rows: list[dict[str, Any]] = []
    start = time.perf_counter()

    for step in range(1, max_steps + 1):
        if is_terminal(state):
            break
        legal_actions = get_legal_actions(state)
        action = agent.choose_action(state)
        if action not in legal_actions:
            raise RuntimeError(f"{agent_name} returned illegal action at step {step}: {action}")
        _, success, message = apply_action(state, action)
        if not success:
            raise RuntimeError(
                f"{agent_name} action failed at step {step}: {action} ({message})"
            )
        rows.append(
            {
                "agent_name": agent_name,
                "seed": seed,
                "step": step,
                "action_type": action.action_type,
                "score": state.player.score,
                "money": state.player.money,
                "bonds": state.player.bonds,
                "delivered_goods_count": state.player.delivered_goods_count,
                "completed_routes_count": _completed_routes_count(state),
                "urbanized_city_count": _urbanized_city_count(state),
            }
        )

    runtime_seconds = time.perf_counter() - start
    first_20 = rows[:20]
    summary = {
        "agent_name": agent_name,
        "seed": seed,
        "steps": len(rows),
        "terminal": state.is_terminal(),
        "first_20_urbanize_actions": _count_actions(first_20, "urbanize"),
        "total_urbanize_actions": _count_actions(rows, "urbanize"),
        "bonds": state.player.bonds,
        "deliveries": state.player.delivered_goods_count,
        "completed_routes": _completed_routes_count(state),
        "urbanized_city_count": _urbanized_city_count(state),
        "final_score": state.final_score(),
        "runtime_seconds": runtime_seconds,
        "fallback_count": 0,
    }
    return rows, summary


def _write_markdown(summaries: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Presentation Lookahead Diagnosis",
        "",
        "Scenario: `official_like`, seed `42`, max steps `60`.",
        "",
        "| agent | first 20 urbanize | total urbanize | bonds | deliveries | completed routes | urbanized cities | final score | terminal | runtime seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for summary in summaries:
        lines.append(
            "| "
            f"{summary['agent_name']} | "
            f"{summary['first_20_urbanize_actions']} | "
            f"{summary['total_urbanize_actions']} | "
            f"{summary['bonds']} | "
            f"{summary['deliveries']} | "
            f"{summary['completed_routes']} | "
            f"{summary['urbanized_city_count']} | "
            f"{summary['final_score']} | "
            f"{summary['terminal']} | "
            f"{summary['runtime_seconds']:.4f} |"
        )
    presentation = next(
        item for item in summaries if item["agent_name"] == "presentation_lookahead_greedy"
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `presentation_lookahead_greedy` is the public replay-friendly lookahead agent.",
            "- It gates early/speculative urbanization and gives more weight to completed routes, deliveries, and bond control.",
            "- The original aggressive urbanization-aware lookahead remains internal helper code and is not part of the public demo agent set.",
            "- Remaining urbanization is expected to occur near the built network or when it opens direct delivery potential.",
            "",
            "## Presentation Summary",
            "",
            f"- Presentation lookahead first-20 urbanize actions: {presentation['first_20_urbanize_actions']}",
            f"- Presentation lookahead total urbanize actions: {presentation['total_urbanize_actions']}",
            f"- Presentation lookahead bonds: {presentation['bonds']}",
            f"- Presentation lookahead deliveries: {presentation['deliveries']}",
            f"- Presentation lookahead completed routes: {presentation['completed_routes']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _count_actions(rows: list[dict[str, Any]], action_type: str) -> int:
    return sum(row["action_type"] == action_type for row in rows)


def _summarize_runs(run_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for agent_name in AGENTS:
        group = [
            summary for summary in run_summaries if summary["agent_name"] == agent_name
        ]
        rows.append(
            {
                "agent_name": agent_name,
                "runs": len(group),
                "mean_final_score": statistics.fmean(
                    summary["final_score"] for summary in group
                ),
                "median_final_score": statistics.median(
                    summary["final_score"] for summary in group
                ),
                "mean_deliveries": statistics.fmean(
                    summary["deliveries"] for summary in group
                ),
                "mean_completed_routes": statistics.fmean(
                    summary["completed_routes"] for summary in group
                ),
                "mean_bonds": statistics.fmean(summary["bonds"] for summary in group),
                "mean_urbanize_actions": statistics.fmean(
                    summary["total_urbanize_actions"] for summary in group
                ),
                "mean_first20_urbanize": statistics.fmean(
                    summary["first_20_urbanize_actions"] for summary in group
                ),
                "success_count": sum(1 for summary in group if summary["terminal"]),
                "fallback_count": sum(summary["fallback_count"] for summary in group),
            }
        )
    return rows


def _write_tuning_summary_markdown(
    summary_rows: list[dict[str, Any]],
    path: Path,
    *,
    seeds: range,
    max_steps: int,
) -> None:
    lines = [
        "# Balanced Presentation Lookahead Tuning Summary",
        "",
        f"Scenario: `official_like`, seeds `{seeds.start}`-`{seeds.stop - 1}`, max steps `{max_steps}`.",
        "",
        "| agent | mean final_score | median final_score | mean deliveries | mean completed routes | mean bonds | mean urbanize actions | mean first20 urbanize | success count | fallback count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            f"{row['agent_name']} | "
            f"{row['mean_final_score']:.2f} | "
            f"{row['median_final_score']:.2f} | "
            f"{row['mean_deliveries']:.2f} | "
            f"{row['mean_completed_routes']:.2f} | "
            f"{row['mean_bonds']:.2f} | "
            f"{row['mean_urbanize_actions']:.2f} | "
            f"{row['mean_first20_urbanize']:.2f} | "
            f"{row['success_count']} | "
            f"{row['fallback_count']} |"
        )

    presentation = next(
        row for row in summary_rows if row["agent_name"] == "presentation_lookahead_greedy"
    )
    lines.extend(
        [
            "",
            "## Tuning Read",
            "",
            "- The balanced variant should keep early urbanization readable while allowing useful urbanize actions when they connect to deliveries, objectives, or the built network.",
            f"- Presentation mean first-20 urbanize actions: {presentation['mean_first20_urbanize']:.2f}.",
            f"- Presentation mean urbanize actions: {presentation['mean_urbanize_actions']:.2f}.",
            f"- Presentation mean bonds: {presentation['mean_bonds']:.2f}.",
            f"- Presentation mean deliveries: {presentation['mean_deliveries']:.2f}.",
            f"- Presentation mean final score: {presentation['mean_final_score']:.2f}.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _completed_routes_count(state) -> int:
    return sum(route.completed for route in state.routes.values())


def _urbanized_city_count(state) -> int:
    return sum(city.is_urbanized for city in state.cities.values())


def main() -> None:
    _, summaries = run_diagnosis()
    _, tuning_summaries = run_balanced_tuning_comparison()
    for summary in summaries:
        print(
            f"{summary['agent_name']}: "
            f"first20_urbanize={summary['first_20_urbanize_actions']}, "
            f"total_urbanize={summary['total_urbanize_actions']}, "
            f"bonds={summary['bonds']}, deliveries={summary['deliveries']}, "
            f"completed_routes={summary['completed_routes']}, "
            f"final_score={summary['final_score']}"
        )
    print("Balanced tuning comparison")
    for summary in tuning_summaries:
        print(
            f"{summary['agent_name']}: "
            f"mean_final_score={summary['mean_final_score']:.2f}, "
            f"mean_first20_urbanize={summary['mean_first20_urbanize']:.2f}, "
            f"mean_urbanize={summary['mean_urbanize_actions']:.2f}, "
            f"mean_bonds={summary['mean_bonds']:.2f}"
        )
    print(f"Wrote {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
