from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.models import PHASE_ACTION, PHASE_GAME_OVER
from railways.rules import (
    build_track,
    check_major_lines,
    deliver_good,
    find_all_legal_delivery_paths,
    get_legal_build_actions,
    next_turn,
    pay_money,
    run_income_phase,
    upgrade_engine,
)


def test_build_affordable_edge() -> None:
    state = reset_game()
    ok, _ = build_track(state, "A-B")
    assert ok
    assert state.edges["A-B"].built
    assert state.edges["A-B"].owner == "player"
    assert state.player.money == 17


def test_first_build_can_start_anywhere() -> None:
    state = reset_game()
    legal_edge_ids = {action.params["edge_id"] for action in get_legal_build_actions(state)}
    assert "C-H" in legal_edge_ids
    ok, _ = build_track(state, "C-H")
    assert ok


def test_connected_building_rejects_disconnected_second_edge() -> None:
    state = reset_game()
    assert build_track(state, "A-B")[0]
    legal_edge_ids = {action.params["edge_id"] for action in get_legal_build_actions(state)}
    assert "C-F" not in legal_edge_ids
    ok, message = build_track(state, "C-F")
    assert not ok
    assert "not connected" in message


def test_connected_building_allows_edge_touching_network() -> None:
    state = reset_game()
    assert build_track(state, "A-B")[0]
    ok, _ = build_track(state, "B-C")
    assert ok
    assert state.edges["B-C"].built


def test_build_unaffordable_edge_fails_without_auto_bonds() -> None:
    state = reset_game()
    state.config = replace(state.config, auto_issue_bonds_when_needed=False)
    state.player.money = 0
    ok, _ = build_track(state, "C-H")
    assert not ok
    assert not state.edges["C-H"].built
    assert state.player.bonds == 0


def test_no_issue_bond_in_legal_actions() -> None:
    state = reset_game()
    actions = get_legal_actions(state)
    assert actions
    assert all(action.action_type != "issue_bond" for action in actions)


def test_auto_financing_builds_without_separate_action() -> None:
    state = reset_game()
    state.config = replace(
        state.config,
        allow_voluntary_bonds=False,
        auto_issue_bonds_when_needed=True,
    )
    state.player.money = 0
    starting_actions = state.actions_remaining

    ok, message = build_track(state, "C-H")
    assert ok, message
    assert state.edges["C-H"].built
    assert state.player.bonds == 2
    assert state.player.money == 4
    assert state.actions_remaining == starting_actions - 1
    assert any("automatically" in item for item in state.action_history)
    assert all(
        action.action_type != "issue_bond"
        for action in get_legal_actions(state)
    )


def test_apply_action_rejects_issue_bond_external_action() -> None:
    state = reset_game()
    before_money = state.player.money
    before_bonds = state.player.bonds
    before_actions = state.actions_remaining

    _, success, message = apply_action(state, Action("issue_bond"))

    assert not success
    assert (
        "not a legal player action" in message
        or "financing is handled internally" in message
    )
    assert state.player.money == before_money
    assert state.player.bonds == before_bonds
    assert state.actions_remaining == before_actions


def test_no_start_city_or_train_position_required() -> None:
    state = reset_game()
    for field_name in [
        "start_city",
        "starting_city",
        "home_city",
        "train_position",
        "current_city",
        "player_start",
    ]:
        assert not hasattr(state, field_name)

    state.config = replace(state.config, require_connected_track_building=False)
    legal_edge_ids = {
        action.params["edge_id"]
        for action in get_legal_build_actions(state)
    }
    assert {"A-B", "C-H"}.issubset(legal_edge_ids)
    assert build_track(state, "A-B")[0]
    ok, message = build_track(state, "C-H")
    assert ok, message


def test_delivery_without_built_path_fails() -> None:
    state = reset_game()
    ok, _ = deliver_good(state, "B", "A", "red")
    assert not ok
    assert state.player.score == 0


def test_delivery_with_built_path_succeeds() -> None:
    state = reset_game()
    assert build_track(state, "A-B")[0]
    ok, _ = deliver_good(state, "B", "A", "red")
    assert ok
    assert state.player.score == 1
    assert state.player.delivered_goods_count == 1


def test_delivery_fails_when_path_exceeds_engine_level() -> None:
    state = reset_game()
    assert build_track(state, "C-F")[0]
    assert build_track(state, "E-F")[0]
    assert build_track(state, "D-E")[0]
    ok, _ = deliver_good(state, "C", "D", "green")
    assert not ok
    assert state.player.locomotive_level == 1


def test_legal_deliveries_include_explicit_paths() -> None:
    state = reset_game()
    state.player.money = 100
    state.player.locomotive_level = 3
    for edge_id in ["C-F", "E-F", "D-E", "A-D", "A-B", "B-C"]:
        assert build_track(state, edge_id)[0]

    paths = find_all_legal_delivery_paths(state, "C", "D", "green")
    assert ["C", "F", "E", "D"] in paths
    assert ["C", "B", "A", "D"] in paths


def test_explicit_delivery_path_succeeds() -> None:
    state = reset_game()
    state.player.money = 100
    state.player.locomotive_level = 3
    for edge_id in ["C-F", "E-F", "D-E"]:
        assert build_track(state, edge_id)[0]

    ok, _ = deliver_good(state, "C", "D", "green", path=["C", "F", "E", "D"])
    assert ok
    assert state.player.score == 3


def test_explicit_delivery_path_rejects_unbuilt_segment() -> None:
    state = reset_game()
    state.player.locomotive_level = 3
    assert build_track(state, "A-B")[0]
    ok, message = deliver_good(state, "B", "A", "red", path=["B", "C", "A"])
    assert not ok
    assert "not built" in message


def test_explicit_delivery_path_rejects_matching_city_skip() -> None:
    state = reset_game()
    state.player.locomotive_level = 3
    for edge_id in ["A-B", "A-D", "D-E"]:
        assert build_track(state, edge_id)[0]

    ok, message = deliver_good(state, "B", "E", "red", path=["B", "A", "D", "E"])
    assert not ok
    assert "skips" in message


def test_upgrade_engine_costs_money_and_increases_level() -> None:
    state = reset_game()
    ok, _ = upgrade_engine(state)
    assert ok
    assert state.player.locomotive_level == 2
    assert state.player.money == 15


def test_pay_money_auto_financing_increases_certificate_count() -> None:
    state = reset_game()
    state.config = replace(
        state.config,
        allow_voluntary_bonds=False,
        auto_issue_bonds_when_needed=True,
    )
    state.player.money = 0

    ok, message = pay_money(
        state,
        7,
        allow_auto_bonds=state.config.auto_issue_bonds_when_needed,
    )

    assert ok, message
    assert state.player.money == 3
    assert state.player.bonds == 2
    assert any("automatically" in item for item in state.action_history)
    assert all(action.action_type != "issue_bond" for action in get_legal_actions(state))


def test_pay_money_does_not_auto_finance_when_disabled() -> None:
    state = reset_game()
    state.config = replace(state.config, auto_issue_bonds_when_needed=False)
    state.player.money = 0

    ok, message = pay_money(
        state,
        7,
        allow_auto_bonds=state.config.auto_issue_bonds_when_needed,
    )

    assert not ok
    assert "Need $7" in message
    assert state.player.money == 0
    assert state.player.bonds == 0


def test_income_phase_adds_income_and_subtracts_interest() -> None:
    state = reset_game()
    state.player.score = 5
    state.player.bonds = 1
    state.player.money = 0
    run_income_phase(state)
    assert state.player.money == 4


def test_final_score_subtracts_bond_penalty() -> None:
    state = reset_game()
    state.player.score = 10
    state.player.bonds = 2
    assert state.final_score() == 8


def test_empty_city_marker_added_when_last_good_removed() -> None:
    state = reset_game()
    assert build_track(state, "A-B")[0]
    ok, _ = deliver_good(state, "A", "B", "blue")
    assert ok
    assert state.cities["A"].empty_marker


def test_empty_marker_end_condition_triggers_when_limit_reached() -> None:
    state = reset_game()
    state.config = replace(
        state.config,
        end_condition="empty_city_markers",
        empty_city_marker_limit=1,
        extra_turn_after_end_trigger=True,
    )
    assert build_track(state, "A-B")[0]
    assert deliver_good(state, "A", "B", "blue")[0]
    assert state.end_triggered
    assert state.extra_turns_remaining == 1
    assert state.phase == PHASE_ACTION


def test_empty_marker_extra_turn_logic_reaches_game_over() -> None:
    state = reset_game()
    state.config = replace(
        state.config,
        end_condition="empty_city_markers",
        empty_city_marker_limit=1,
        extra_turn_after_end_trigger=True,
    )
    assert build_track(state, "A-B")[0]
    assert deliver_good(state, "A", "B", "blue")[0]

    assert next_turn(state)[0]
    assert state.phase == PHASE_ACTION
    assert state.turn == 2
    assert state.extra_turns_remaining == 0

    assert next_turn(state)[0]
    assert state.phase == PHASE_GAME_OVER


def test_empty_marker_without_extra_turn_reaches_game_over_after_current_turn() -> None:
    state = reset_game()
    state.config = replace(
        state.config,
        end_condition="empty_city_markers",
        empty_city_marker_limit=1,
        extra_turn_after_end_trigger=False,
    )
    assert build_track(state, "A-B")[0]
    assert deliver_good(state, "A", "B", "blue")[0]
    assert next_turn(state)[0]
    assert state.phase == PHASE_GAME_OVER


def test_major_line_claiming_adds_bonus_once() -> None:
    state = reset_game()
    state.player.money = 100
    for edge_id in ["A-B", "B-C", "C-H"]:
        assert build_track(state, edge_id)[0]

    line = state.major_lines["A-H"]
    assert line.claimed
    assert state.player.major_line_bonus == line.bonus_points
    assert state.final_score() == line.bonus_points
    assert any("claimed major line A-H" in item for item in state.action_history)

    check_major_lines(state)
    assert state.player.major_line_bonus == line.bonus_points


def run_all() -> None:
    tests = [
        test_build_affordable_edge,
        test_first_build_can_start_anywhere,
        test_connected_building_rejects_disconnected_second_edge,
        test_connected_building_allows_edge_touching_network,
        test_build_unaffordable_edge_fails_without_auto_bonds,
        test_no_issue_bond_in_legal_actions,
        test_auto_financing_builds_without_separate_action,
        test_apply_action_rejects_issue_bond_external_action,
        test_no_start_city_or_train_position_required,
        test_delivery_without_built_path_fails,
        test_delivery_with_built_path_succeeds,
        test_delivery_fails_when_path_exceeds_engine_level,
        test_legal_deliveries_include_explicit_paths,
        test_explicit_delivery_path_succeeds,
        test_explicit_delivery_path_rejects_unbuilt_segment,
        test_explicit_delivery_path_rejects_matching_city_skip,
        test_upgrade_engine_costs_money_and_increases_level,
        test_pay_money_auto_financing_increases_certificate_count,
        test_pay_money_does_not_auto_finance_when_disabled,
        test_income_phase_adds_income_and_subtracts_interest,
        test_final_score_subtracts_bond_penalty,
        test_empty_city_marker_added_when_last_good_removed,
        test_empty_marker_end_condition_triggers_when_limit_reached,
        test_empty_marker_extra_turn_logic_reaches_game_over,
        test_empty_marker_without_extra_turn_reaches_game_over_after_current_turn,
        test_major_line_claiming_adds_bonus_once,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} smoke tests passed.")


if __name__ == "__main__":
    run_all()
