from __future__ import annotations

import csv
from pathlib import Path
import random
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import create_agent
from railways.environment import apply_action, get_legal_actions, is_terminal, reset_game


AGENTS = (
    "urbanization_aware_lookahead_greedy",
    "presentation_lookahead_greedy",
    "objective_aware_greedy",
)
MAP_PATH = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
OUTPUT_DIR = PROJECT_ROOT / "experiments" / "results" / "presentation_lookahead_diagnosis"
TRACE_COLUMNS = [
    "agent_name",
    "step",
    "action_type",
    "score",
    "money",
    "bonds",
    "delivered_goods_count",
    "completed_routes_count",
    "urbanized_city_count",
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
    original = next(
        item for item in summaries if item["agent_name"] == "urbanization_aware_lookahead_greedy"
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `presentation_lookahead_greedy` is intended for replay clarity, not maximum benchmark score.",
            "- It gates early/speculative urbanization and gives more weight to completed routes, deliveries, and bond control.",
            "- Lower first-20-step urbanization than the experimental lookahead agent indicates a more readable early replay.",
            "- Remaining urbanization is expected to occur near the built network or when it opens direct delivery potential.",
            "",
            "## Before/After Summary",
            "",
            f"- Original lookahead first-20 urbanize actions: {original['first_20_urbanize_actions']}",
            f"- Presentation lookahead first-20 urbanize actions: {presentation['first_20_urbanize_actions']}",
            f"- Original lookahead total urbanize actions: {original['total_urbanize_actions']}",
            f"- Presentation lookahead total urbanize actions: {presentation['total_urbanize_actions']}",
            f"- Original lookahead bonds: {original['bonds']}",
            f"- Presentation lookahead bonds: {presentation['bonds']}",
            f"- Original lookahead deliveries: {original['deliveries']}",
            f"- Presentation lookahead deliveries: {presentation['deliveries']}",
            f"- Original lookahead completed routes: {original['completed_routes']}",
            f"- Presentation lookahead completed routes: {presentation['completed_routes']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _count_actions(rows: list[dict[str, Any]], action_type: str) -> int:
    return sum(row["action_type"] == action_type for row in rows)


def _completed_routes_count(state) -> int:
    return sum(route.completed for route in state.routes.values())


def _urbanized_city_count(state) -> int:
    return sum(city.is_urbanized for city in state.cities.values())


def main() -> None:
    _, summaries = run_diagnosis()
    for summary in summaries:
        print(
            f"{summary['agent_name']}: "
            f"first20_urbanize={summary['first_20_urbanize_actions']}, "
            f"total_urbanize={summary['total_urbanize_actions']}, "
            f"bonds={summary['bonds']}, deliveries={summary['deliveries']}, "
            f"completed_routes={summary['completed_routes']}, "
            f"final_score={summary['final_score']}"
        )
    print(f"Wrote {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
