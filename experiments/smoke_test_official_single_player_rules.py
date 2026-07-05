from __future__ import annotations

import math
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.models import PHASE_ACTION
from railways.rules import deliver_good, get_legal_deliveries, run_income_phase, urbanize


MAP_PATH = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def make_official_state():
    return reset_game(map_path=MAP_PATH, config_path=CONFIG_PATH)


def complete_a_h_route(state) -> None:
    _, success, message = apply_action(
        state,
        Action.build_track_segments(["A-H-1", "A-H-2"]),
    )
    assert success, message


def test_official_config_and_route_segment_state() -> None:
    state = make_official_state()

    assert state.player.money == 0
    assert state.player.bonds == 0
    assert state.actions_remaining == 3
    assert state.config.actions_per_turn == 3
    assert state.config.max_locomotive_level == 8
    assert state.config.end_condition == "empty_city_markers"
    assert state.routes
    assert state.segments
    assert state.edges == {}


def test_only_segment_build_actions_are_exposed() -> None:
    state = make_official_state()
    action_types = {action.action_type for action in get_legal_actions(state)}

    assert "build_track_segments" in action_types
    assert "build_track" not in action_types
    assert "issue_bond" not in action_types
    assert not hasattr(Action, "build_track")
    assert not hasattr(Action, "issue_bond")


def test_paid_action_automatically_issues_minimum_financing() -> None:
    state = make_official_state()
    build_action = next(
        action
        for action in get_legal_actions(state)
        if action.action_type == "build_track_segments"
    )
    total_cost = sum(
        state.segments[segment_id].cost
        for segment_id in build_action.params["segment_ids"]
    )
    expected_bonds = math.ceil(total_cost / state.config.bond_value)
    starting_actions = state.actions_remaining

    _, success, message = apply_action(state, build_action)

    assert success, message
    assert state.player.bonds == expected_bonds
    assert state.player.money == expected_bonds * state.config.bond_value - total_cost
    assert state.actions_remaining == starting_actions - 1
    assert any("automatically" in entry for entry in state.action_history)


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


def test_urbanize_uses_route_segment_map_cities() -> None:
    state = make_official_state()
    assert not urbanize(state, "A", "red")[0]

    city = state.cities["J"]
    city.empty_marker = True
    starting_actions = state.actions_remaining
    success, message = urbanize(state, "J", "purple")

    assert success, message
    assert city.is_urbanized
    assert city.demand_color == "purple"
    assert not city.empty_marker
    assert state.actions_remaining == starting_actions - 1


def test_delivery_requires_completed_route() -> None:
    state = make_official_state()
    state.player.locomotive_level = 2

    success, message = deliver_good(
        state,
        "A",
        "H",
        "blue",
        path=["A", "H"],
    )

    assert not success
    assert "completed route" in message
    assert get_legal_deliveries(state) == []


def test_completed_route_enables_delivery() -> None:
    state = make_official_state()
    complete_a_h_route(state)
    state.player.locomotive_level = 2
    matching = [
        action
        for action in get_legal_deliveries(state)
        if action.params["source"] == "A"
        and action.params["target"] == "H"
        and action.params["good_color"] == "blue"
    ]

    assert matching
    starting_actions = state.actions_remaining
    _, success, message = apply_action(state, matching[0])

    assert success, message
    assert "blue" not in state.cities["A"].goods
    assert state.player.delivered_goods_count == 1
    assert state.actions_remaining == starting_actions - 1


def test_gray_city_delivery_is_rejected() -> None:
    state = make_official_state()
    state.cities["J"].demand_color = "blue"

    success, message = deliver_good(state, "A", "J", "blue")

    assert not success
    assert "gray city" in message


def run_all() -> None:
    tests = [
        test_official_config_and_route_segment_state,
        test_only_segment_build_actions_are_exposed,
        test_paid_action_automatically_issues_minimum_financing,
        test_income_interest_preserves_automatic_financing,
        test_final_score_subtracts_bond_penalty,
        test_urbanize_uses_route_segment_map_cities,
        test_delivery_requires_completed_route,
        test_completed_route_enables_delivery,
        test_gray_city_delivery_is_rejected,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} official single-player smoke tests passed.")


if __name__ == "__main__":
    run_all()
