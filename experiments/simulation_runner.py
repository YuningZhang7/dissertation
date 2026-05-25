from __future__ import annotations

from pathlib import Path
import random
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.base_agent import BaseAgent
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, is_terminal, reset_game
from railways.rules import count_empty_city_markers


def run_episode(
    agent: BaseAgent,
    seed: int | None = None,
    max_steps: int = 1000,
) -> dict[str, Any]:
    if seed is not None:
        agent.seed = seed
        agent.rng = random.Random(seed)

    state = reset_game()
    fallback_rng = random.Random(seed)
    actions_taken = 0
    invalid_actions = 0
    start_time = time.perf_counter()

    while not is_terminal(state) and actions_taken < max_steps:
        action = agent.choose_action(state)
        legal_actions = get_legal_actions(state)

        if not _is_legal_action(action, legal_actions):
            invalid_actions += 1
            action = fallback_rng.choice(legal_actions) if legal_actions else Action.pass_action()

        _, success, _ = apply_action(state, action)
        if not success:
            invalid_actions += 1
            _, _, _ = apply_action(state, Action.pass_action())

        actions_taken += 1

    runtime_seconds = time.perf_counter() - start_time
    return {
        "agent": agent.name,
        "seed": seed,
        "final_score": state.final_score(),
        "raw_score": state.player.score,
        "bonds": state.player.bonds,
        "money": state.player.money,
        "deliveries": state.player.delivered_goods_count,
        "built_edges": len(state.player.built_edges),
        "major_line_bonus": state.player.major_line_bonus,
        "rail_baron_bonus": state.player.rail_baron_bonus,
        "operation_card_bonus": state.player.operation_card_bonus,
        "empty_markers": count_empty_city_markers(state),
        "turns": state.turn,
        "actions_taken": actions_taken,
        "invalid_actions": invalid_actions,
        "runtime_seconds": runtime_seconds,
        "terminal": state.is_terminal(),
    }


def _is_legal_action(action: Action, legal_actions: list[Action]) -> bool:
    return action in legal_actions
