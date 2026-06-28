from __future__ import annotations

from pathlib import Path

from railways.actions import Action
from railways.game_state import GameState
from railways.models import PHASE_ACTION
from railways.rules import (
    apply_action as apply_rule_action,
    get_legal_operation_card_actions,
    get_legal_build_actions,
    get_legal_build_segment_actions,
    get_legal_deliveries,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
    is_terminal as rules_is_terminal,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP_PATH = PROJECT_ROOT / "data" / "toy_map.json"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "data" / "rules_config.json"
DEFAULT_CARDS_PATH = PROJECT_ROOT / "data" / "cards_basic.json"


def reset_game(
    map_path: str | Path = DEFAULT_MAP_PATH,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    card_path: str | Path | None = None,
) -> GameState:
    return GameState.from_files(map_path, config_path, card_path=card_path)


def get_legal_actions(state: GameState) -> list[Action]:
    if is_terminal(state):
        return []

    actions: list[Action] = []
    actions.extend(get_legal_build_actions(state))
    actions.extend(get_legal_build_segment_actions(state))
    actions.extend(get_legal_deliveries(state))

    upgrade_action = get_legal_upgrade_action(state)
    if upgrade_action is not None:
        actions.append(upgrade_action)

    actions.extend(get_legal_urbanize_actions(state))
    actions.extend(get_legal_operation_card_actions(state))

    if state.phase == PHASE_ACTION and state.config.allow_voluntary_bonds:
        actions.append(Action.issue_bond())

    actions.append(Action.pass_action())
    actions.append(Action.next_turn())
    return actions


def apply_action(state: GameState, action: Action) -> tuple[GameState, bool, str]:
    success, message = apply_rule_action(state, action)
    return state, success, message


def copy_state(state: GameState) -> GameState:
    return state.copy()


def is_terminal(state: GameState) -> bool:
    return rules_is_terminal(state)


def final_score(state: GameState) -> int:
    return state.final_score()
