from __future__ import annotations

import math
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
ROUTE_MAP_PATH = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
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


def test_bonds_are_not_selectable_actions() -> None:
    state = reset_game(map_path=ROUTE_MAP_PATH, config_path=CONFIG_PATH)

    assert not hasattr(Action, "issue_bond")
    assert state.phase == PHASE_ACTION
    assert state.player.money == 0
    assert state.config.allow_voluntary_bonds is False
    assert state.config.auto_issue_bonds_when_needed is True
    assert all(
        action.action_type != "issue_bond" for action in get_legal_actions(state)
    )


def test_paid_action_automatically_issues_minimum_financing() -> None:
    state = reset_game(map_path=ROUTE_MAP_PATH, config_path=CONFIG_PATH)
    legal_actions = get_legal_actions(state)
    build_action = next(
        action
        for action in legal_actions
        if action.action_type == "build_track_segments"
    )
    starting_actions = state.actions_remaining
    starting_bonds = state.player.bonds
    total_cost = sum(
        state.segments[segment_id].cost
        for segment_id in build_action.params["segment_ids"]
    )
    expected_bonds = math.ceil(total_cost / state.config.bond_value)

    _, success, message = apply_action(state, build_action)

    assert success, message
    assert state.player.bonds == starting_bonds + expected_bonds
    assert state.player.money == expected_bonds * state.config.bond_value - total_cost
    assert state.actions_remaining == starting_actions - 1
    assert any("automatically" in entry for entry in state.action_history)
    assert all(
        action.action_type != "issue_bond" for action in get_legal_actions(state)
    )


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


def test_delivery_rejects_unowned_first_link() -> None:
    state = make_official_state()
    state.cities["A"].goods = ["blue"]
    state.cities["B"].demand_color = "blue"
    state.cities["B"].is_gray = False
    edge = state.edges["A-B"]
    edge.built = True
    edge.owner = None

    success, message = deliver_good(
        state,
        "A",
        "B",
        "blue",
        path=["A", "B"],
    )

    assert not success
    assert "player-owned" in message
    assert state.cities["A"].goods == ["blue"]


def test_delivery_accepts_player_owned_first_link() -> None:
    state = make_official_state()
    state.cities["A"].goods = ["blue"]
    state.cities["B"].demand_color = "blue"
    state.cities["B"].is_gray = False
    edge = state.edges["A-B"]
    edge.built = True
    edge.owner = "player"
    starting_actions = state.actions_remaining

    success, message = deliver_good(
        state,
        "A",
        "B",
        "blue",
        path=["A", "B"],
    )

    assert success, message
    assert "blue" not in state.cities["A"].goods
    assert state.player.score >= 1
    assert state.actions_remaining == starting_actions - 1


def test_legal_deliveries_require_player_owned_first_link() -> None:
    state = make_official_state()
    state.cities["A"].goods = ["blue"]
    state.cities["B"].demand_color = "blue"
    state.cities["B"].is_gray = False
    edge = state.edges["A-B"]
    edge.built = True
    edge.owner = None

    legal_deliveries = get_legal_deliveries(state)
    assert all(
        not (
            action.params["source"] == "A"
            and action.params["target"] == "B"
        )
        for action in legal_deliveries
    )

    edge.owner = "player"
    legal_deliveries = get_legal_deliveries(state)
    assert any(
        action.params["source"] == "A"
        and action.params["target"] == "B"
        and action.params["good_color"] == "blue"
        for action in legal_deliveries
    )


def run_all() -> None:
    tests = [
        test_official_config_and_initial_state,
        test_bonds_are_not_selectable_actions,
        test_paid_action_automatically_issues_minimum_financing,
        test_income_interest_preserves_automatic_financing,
        test_final_score_subtracts_bond_penalty,
        test_urbanize_rejects_non_gray_city,
        test_urbanize_gray_city_and_remove_empty_marker,
        test_gray_city_delivery_is_rejected_and_not_generated,
        test_delivery_rejects_unowned_first_link,
        test_delivery_accepts_player_owned_first_link,
        test_legal_deliveries_require_player_owned_first_link,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} official single-player smoke tests passed.")


if __name__ == "__main__":
    run_all()
