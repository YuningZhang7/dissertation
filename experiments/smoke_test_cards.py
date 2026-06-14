from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.card_loader import load_cards
from railways.environment import apply_action, get_legal_actions, reset_game

CARDS_PATH = PROJECT_ROOT / "data" / "cards_basic.json"


def test_card_file_loads_representative_types() -> None:
    cards = load_cards(CARDS_PATH)
    card_types = {card.card_type for card in cards.values()}
    assert "immediate_cash" in card_types
    assert "delivery_objective" in card_types
    assert "network_objective" in card_types
    assert "end_game_scoring" in card_types


def test_legal_card_actions_appear_when_cards_enabled() -> None:
    state = reset_game(card_path=CARDS_PATH)
    actions = get_legal_actions(state)
    card_actions = [
        action for action in actions if action.action_type == "select_operation_card"
    ]
    assert card_actions
    assert all("card_id" in action.params for action in card_actions)


def test_selecting_immediate_cash_card_applies_effect() -> None:
    state = reset_game(card_path=CARDS_PATH)
    before_money = state.player.money
    before_actions = state.actions_remaining

    _, success, message = apply_action(
        state,
        Action.select_operation_card("cash_grant_1"),
    )

    assert success, message
    assert state.player.money == before_money + 5
    assert "cash_grant_1" not in state.available_operation_cards
    assert "cash_grant_1" in state.player.owned_operation_cards
    assert "cash_grant_1" in state.player.completed_operation_cards
    assert state.player.active_operation_cards["cash_grant_1"].status == "used"
    assert state.actions_remaining == before_actions - 1


def test_delivery_objective_completes_after_matching_delivery() -> None:
    state = reset_game(card_path=CARDS_PATH)
    assert apply_action(state, Action.select_operation_card("deliver_red_1"))[1]
    assert apply_action(state, Action.build_track("A-B"))[1]

    _, success, message = apply_action(
        state,
        Action.deliver_good("B", "A", "red", path=["B", "A"]),
    )

    assert success, message
    assert state.player.operation_card_bonus == 3
    assert "deliver_red_1" in state.player.completed_operation_cards
    assert state.player.active_operation_cards["deliver_red_1"].progress == 1
    assert state.player.active_operation_cards["deliver_red_1"].status == "completed"


def test_network_objective_completes_after_connection() -> None:
    state = reset_game(card_path=CARDS_PATH)
    assert apply_action(state, Action.select_operation_card("connect_a_d_1"))[1]

    _, success, message = apply_action(state, Action.build_track("A-D"))

    assert success, message
    assert state.player.operation_card_bonus == 4
    assert "connect_a_d_1" in state.player.completed_operation_cards
    assert state.player.active_operation_cards["connect_a_d_1"].status == "completed"


def test_end_game_scoring_card_contributes_to_final_score() -> None:
    state = reset_game(card_path=CARDS_PATH)
    assert apply_action(state, Action.select_operation_card("builder_bonus_1"))[1]
    assert apply_action(state, Action.build_track("A-B"))[1]
    assert apply_action(state, Action.build_track("B-C"))[1]

    assert state.player.operation_card_bonus == 0
    assert state.final_score() == 2


def run_all() -> None:
    tests = [
        test_card_file_loads_representative_types,
        test_legal_card_actions_appear_when_cards_enabled,
        test_selecting_immediate_cash_card_applies_effect,
        test_delivery_objective_completes_after_matching_delivery,
        test_network_objective_completes_after_connection,
        test_end_game_scoring_card_contributes_to_final_score,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} card smoke tests passed.")


if __name__ == "__main__":
    run_all()
