from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.models import PHASE_ACTION, PHASE_INCOME
from railways.rules import deliver_good, get_legal_deliveries, run_income_phase, urbanize


MAP_PATH = PROJECT_ROOT / "data" / "toy_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def make_official_state():
    return reset_game(map_path=MAP_PATH, config_path=CONFIG_PATH)


def test_official_config_and_initial_state() -> None:
    state = make_official_state()

    assert state.player.money == 0
    assert state.player.bonds == 0
    assert state.actions_remaining == 3
    assert state.config.actions_per_turn == 3
    assert state.config.max_locomotive_level == 8
    assert state.config.end_condition == "empty_city_markers"


def test_voluntary_bond_is_legal_and_does_not_consume_action() -> None:
    state = make_official_state()
    bond_action = Action.issue_bond()
    starting_actions = state.actions_remaining

    assert bond_action.action_type == "issue_bond"
    assert bond_action in get_legal_actions(state)

    _, success, message = apply_action(state, bond_action)

    assert success, message
    assert state.player.money == state.config.bond_value
    assert state.player.bonds == 1
    assert state.actions_remaining == starting_actions
    assert state.phase == PHASE_ACTION
    assert any("issued one bond" in entry for entry in state.action_history)


def test_voluntary_bond_is_rejected_outside_action_phase() -> None:
    state = make_official_state()
    state.phase = PHASE_INCOME

    _, success, message = apply_action(state, Action.issue_bond())

    assert not success
    assert "not action" in message
    assert state.player.money == 0
    assert state.player.bonds == 0


def test_income_interest_preserves_automatic_financing() -> None:
    state = make_official_state()
    state.player.money = 0
    state.player.bonds = 1

    run_income_phase(state)

    assert state.player.money == 4
    assert state.player.bonds == 2
    assert any("automatically" in entry for entry in state.action_history)


def test_final_score_subtracts_bond_penalty() -> None:
    state = make_official_state()
    state.player.score = 10
    state.player.bonds = 3

    assert state.final_score() == 7


def test_urbanize_rejects_non_gray_city() -> None:
    state = make_official_state()
    starting_actions = state.actions_remaining

    success, message = urbanize(state, "A", "red")

    assert not success
    assert "not a gray city" in message
    assert state.actions_remaining == starting_actions


def test_urbanize_gray_city_and_remove_empty_marker() -> None:
    state = make_official_state()
    city = state.cities["H"]
    city.empty_marker = True
    starting_actions = state.actions_remaining
    starting_goods = len(city.goods)

    success, message = urbanize(state, "H", "purple")

    assert success, message
    assert state.actions_remaining == starting_actions - 1
    assert not city.is_gray
    assert city.is_urbanized
    assert city.demand_color == "purple"
    assert not city.empty_marker
    assert len(city.goods) == starting_goods + state.config.new_goods_on_urbanize


def test_gray_city_delivery_is_rejected_and_not_generated() -> None:
    state = make_official_state()
    target = state.cities["H"]
    target.demand_color = "green"
    edge = state.edges["C-H"]
    edge.built = True
    edge.owner = "player"

    legal_deliveries = get_legal_deliveries(state)
    assert all(action.params["target"] != "H" for action in legal_deliveries)

    success, message = deliver_good(
        state,
        "C",
        "H",
        "green",
        path=["C", "H"],
    )

    assert not success
    assert "gray city" in message
    assert "green" in state.cities["C"].goods


def run_all() -> None:
    tests = [
        test_official_config_and_initial_state,
        test_voluntary_bond_is_legal_and_does_not_consume_action,
        test_voluntary_bond_is_rejected_outside_action_phase,
        test_income_interest_preserves_automatic_financing,
        test_final_score_subtracts_bond_penalty,
        test_urbanize_rejects_non_gray_city,
        test_urbanize_gray_city_and_remove_empty_marker,
        test_gray_city_delivery_is_rejected_and_not_generated,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} official single-player smoke tests passed.")


if __name__ == "__main__":
    run_all()
