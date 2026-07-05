from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.random_agent import RandomAgent
from experiments.simulation_runner import run_episode
from railways.actions import Action
from railways.card_loader import load_cards
from railways.cards import compute_end_game_card_bonus, update_cards_after_build
from railways.environment import apply_action, get_legal_actions, reset_game

CARDS_PATH = PROJECT_ROOT / "data" / "cards_basic.json"


def complete_route(state, route_id: str) -> None:
    _, success, message = apply_action(
        state,
        Action.build_track_segments(state.routes[route_id].segment_ids),
    )
    assert success, message


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


def test_reset_game_without_cards_has_empty_card_state() -> None:
    state = reset_game(card_path=None)
    assert state.operation_cards == {}
    assert state.available_operation_cards == []
    assert state.player.owned_operation_cards == []
    assert state.player.active_operation_cards == {}
    assert state.player.completed_operation_cards == set()


def test_reset_game_with_cards_loads_card_state() -> None:
    state = reset_game(card_path=CARDS_PATH)
    assert state.operation_cards
    assert state.available_operation_cards
    assert state.player.owned_operation_cards == []
    assert state.player.completed_operation_cards == set()


def test_card_action_order_is_deterministic() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.available_operation_cards = list(reversed(state.available_operation_cards))

    card_ids = [
        action.params["card_id"]
        for action in get_legal_actions(state)
        if action.action_type == "select_operation_card"
    ]

    assert card_ids == sorted(card_ids)


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


def test_objective_card_selection_consumes_one_action_only() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.actions_remaining = 6

    assert apply_action(state, Action.select_operation_card("deliver_red_1"))[1]
    assert state.actions_remaining == 5
    complete_route(state, "A-H")
    complete_route(state, "H-B")
    state.player.locomotive_level = 4
    assert apply_action(
        state, Action.deliver_good("B", "A", "red", path=["B", "H", "A"])
    )[1]
    assert state.actions_remaining == 2


def test_delivery_objective_completes_after_matching_delivery() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.actions_remaining = 6
    assert apply_action(state, Action.select_operation_card("deliver_red_1"))[1]
    complete_route(state, "A-H")
    complete_route(state, "H-B")
    state.player.locomotive_level = 4

    _, success, message = apply_action(
        state,
        Action.deliver_good("B", "A", "red", path=["B", "H", "A"]),
    )

    assert success, message
    assert state.player.operation_card_bonus == 3
    assert "deliver_red_1" in state.player.completed_operation_cards
    assert state.player.active_operation_cards["deliver_red_1"].progress == 1
    assert state.player.active_operation_cards["deliver_red_1"].status == "completed"


def test_delivery_objective_does_not_award_twice() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.player.money = 100
    state.actions_remaining = 10

    assert apply_action(state, Action.select_operation_card("deliver_red_1"))[1]
    complete_route(state, "A-H")
    complete_route(state, "H-B")
    state.player.locomotive_level = 4
    assert apply_action(
        state, Action.deliver_good("B", "A", "red", path=["B", "H", "A"])
    )[1]
    bonus_after_first = state.player.operation_card_bonus

    complete_route(state, "F-H")
    assert apply_action(
        state, Action.deliver_good("F", "A", "red", path=["F", "H", "A"])
    )[1]

    assert bonus_after_first == 3
    assert state.player.operation_card_bonus == bonus_after_first
    assert state.player.active_operation_cards["deliver_red_1"].progress == 1


def test_network_objective_completes_after_connection() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.actions_remaining = 5
    assert apply_action(state, Action.select_operation_card("connect_a_d_1"))[1]

    complete_route(state, "A-H")
    _, success, message = apply_action(
        state,
        Action.build_track_segments(state.routes["D-H"].segment_ids),
    )

    assert success, message
    assert state.player.operation_card_bonus == 4
    assert "connect_a_d_1" in state.player.completed_operation_cards
    assert state.player.active_operation_cards["connect_a_d_1"].status == "completed"


def test_network_objective_does_not_award_twice() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.actions_remaining = 5
    assert apply_action(state, Action.select_operation_card("connect_a_d_1"))[1]
    complete_route(state, "A-H")
    complete_route(state, "D-H")
    bonus_after_connection = state.player.operation_card_bonus

    update_cards_after_build(state)

    assert bonus_after_connection == 4
    assert state.player.operation_card_bonus == bonus_after_connection


def test_end_game_scoring_card_contributes_to_final_score() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.actions_remaining = 5
    assert apply_action(state, Action.select_operation_card("builder_bonus_1"))[1]
    complete_route(state, "A-H")
    complete_route(state, "H-B")
    actions_before_final_score = state.actions_remaining

    assert state.player.operation_card_bonus == 0
    assert compute_end_game_card_bonus(state) == 2
    assert state.actions_remaining == actions_before_final_score


def test_final_score_combines_card_and_existing_bonuses() -> None:
    state = reset_game(card_path=CARDS_PATH)
    state.player.score = 7
    state.player.bonds = 2
    state.player.major_line_bonus = 3
    state.player.rail_baron_bonus = 1
    state.player.operation_card_bonus = 4
    state.player.owned_operation_cards.append("builder_bonus_1")
    for route_id in ("A-H", "H-B", "D-H"):
        state.routes[route_id].completed = True

    assert state.final_score() == 16


def test_random_agent_runs_with_cards_enabled() -> None:
    result = run_episode(
        RandomAgent(seed=0),
        seed=0,
        max_steps=100,
        card_path=CARDS_PATH,
    )
    assert result["invalid_actions"] == 0


def test_greedy_delivery_runs_with_cards_enabled() -> None:
    result = run_episode(
        GreedyDeliveryAgent(seed=0),
        seed=0,
        max_steps=100,
        card_path=CARDS_PATH,
    )
    assert result["invalid_actions"] == 0


def run_all() -> None:
    tests = [
        test_card_file_loads_representative_types,
        test_legal_card_actions_appear_when_cards_enabled,
        test_reset_game_without_cards_has_empty_card_state,
        test_reset_game_with_cards_loads_card_state,
        test_card_action_order_is_deterministic,
        test_selecting_immediate_cash_card_applies_effect,
        test_objective_card_selection_consumes_one_action_only,
        test_delivery_objective_completes_after_matching_delivery,
        test_delivery_objective_does_not_award_twice,
        test_network_objective_completes_after_connection,
        test_network_objective_does_not_award_twice,
        test_end_game_scoring_card_contributes_to_final_score,
        test_final_score_combines_card_and_existing_bonuses,
        test_random_agent_runs_with_cards_enabled,
        test_greedy_delivery_runs_with_cards_enabled,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} card smoke tests passed.")


if __name__ == "__main__":
    run_all()
