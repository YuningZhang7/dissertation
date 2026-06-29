from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game


ROUTE_MAP = PROJECT_ROOT / "data" / "mini_route_segment_map.json"
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
LEGACY_MAP = PROJECT_ROOT / "data" / "toy_map.json"
LEGACY_CONFIG = PROJECT_ROOT / "data" / "rules_config.json"


def make_segment_state():
    return reset_game(map_path=ROUTE_MAP, config_path=OFFICIAL_CONFIG)


def apply_segment_build(state, segment_ids: list[str]):
    return apply_action(state, Action.build_track_segments(segment_ids))


def test_legal_segment_build_actions_are_generated() -> None:
    state = make_segment_state()

    segment_actions = [
        action
        for action in get_legal_actions(state)
        if action.action_type == "build_track_segments"
    ]

    assert segment_actions
    assert all(1 <= len(action.params["segment_ids"]) <= 4 for action in segment_actions)


def test_build_one_segment_uses_automatic_financing() -> None:
    state = make_segment_state()
    starting_actions = state.actions_remaining

    _, success, message = apply_segment_build(state, ["A-B-1"])

    assert success, message
    assert state.segments["A-B-1"].built
    assert state.segments["A-B-1"].owner == "player"
    assert not state.segments["A-B-1"].completed
    assert not state.routes["A-B"].completed
    assert state.player.money == 3
    assert state.player.bonds == 1
    assert state.actions_remaining == starting_actions - 1


def test_build_multiple_consecutive_segments_succeeds() -> None:
    state = make_segment_state()
    starting_actions = state.actions_remaining

    _, success, message = apply_segment_build(state, ["A-B-1", "A-B-2"])

    assert success, message
    assert state.segments["A-B-1"].built
    assert state.segments["A-B-2"].built
    assert state.segments["A-B-1"].owner == "player"
    assert state.segments["A-B-2"].owner == "player"
    assert state.player.money == 0
    assert state.player.bonds == 1
    assert state.actions_remaining == starting_actions - 1


def test_isolated_middle_segment_is_rejected() -> None:
    state = make_segment_state()
    starting_actions = state.actions_remaining

    _, success, message = apply_segment_build(state, ["B-C-2"])

    assert not success
    assert "city" in message or "endpoint" in message
    assert not state.segments["B-C-2"].built
    assert state.actions_remaining == starting_actions


def test_build_can_start_from_either_city_end() -> None:
    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["B-C-1"])
    assert success, message
    assert state.segments["B-C-1"].built
    assert state.segments["B-C-1"].owner == "player"

    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["B-C-3"])
    assert success, message
    assert state.segments["B-C-3"].built
    assert state.segments["B-C-3"].owner == "player"


def test_build_can_continue_from_incomplete_endpoint() -> None:
    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["B-C-1"])
    assert success, message

    _, success, message = apply_segment_build(state, ["B-C-2"])

    assert success, message
    assert state.segments["B-C-1"].built
    assert state.segments["B-C-2"].built
    assert not state.routes["B-C"].completed


def test_completed_route_marks_all_segments_completed() -> None:
    state = make_segment_state()

    _, success, message = apply_segment_build(state, ["A-B-1", "A-B-2"])

    assert success, message
    assert state.routes["A-B"].completed
    assert state.segments["A-B-1"].completed
    assert state.segments["A-B-2"].completed
    assert any("completed route A-B" in entry for entry in state.action_history)


def test_income_removes_incomplete_segments() -> None:
    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["B-C-1"])
    assert success, message
    assert state.segments["B-C-1"].built
    assert not state.segments["B-C-1"].completed

    assert apply_action(state, Action.pass_action())[1]
    assert apply_action(state, Action.pass_action())[1]

    assert not state.segments["B-C-1"].built
    assert state.segments["B-C-1"].owner is None
    assert any("removed 1 incomplete" in entry for entry in state.action_history)


def test_completed_route_survives_income_cleanup() -> None:
    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["A-B-1", "A-B-2"])
    assert success, message
    assert state.routes["A-B"].completed

    assert apply_action(state, Action.pass_action())[1]
    assert apply_action(state, Action.pass_action())[1]

    assert state.segments["A-B-1"].built
    assert state.segments["A-B-2"].built
    assert state.segments["A-B-1"].completed
    assert state.segments["A-B-2"].completed


def test_legal_actions_exclude_isolated_middle_segment() -> None:
    state = make_segment_state()
    segment_actions = [
        action
        for action in get_legal_actions(state)
        if action.action_type == "build_track_segments"
    ]
    segment_id_lists = [action.params["segment_ids"] for action in segment_actions]

    assert ["B-C-2"] not in segment_id_lists
    assert ["B-C-1"] in segment_id_lists
    assert ["B-C-3"] in segment_id_lists


def test_empty_segment_list_is_rejected() -> None:
    state = make_segment_state()
    starting_actions = state.actions_remaining

    _, success, message = apply_segment_build(state, [])

    assert not success
    assert "at least one" in message
    assert state.actions_remaining == starting_actions


def test_more_than_four_segments_are_rejected() -> None:
    state = make_segment_state()
    starting_actions = state.actions_remaining

    _, success, message = apply_segment_build(
        state,
        ["one", "two", "three", "four", "five"],
    )

    assert not success
    assert "at most 4" in message
    assert state.actions_remaining == starting_actions


def test_non_consecutive_segments_are_rejected() -> None:
    state = make_segment_state()
    starting_actions = state.actions_remaining

    _, success, message = apply_segment_build(state, ["B-C-1", "B-C-3"])

    assert not success
    assert "consecutive" in message
    assert not state.segments["B-C-1"].built
    assert not state.segments["B-C-3"].built
    assert state.actions_remaining == starting_actions


def test_segments_from_different_routes_are_rejected() -> None:
    state = make_segment_state()

    _, success, message = apply_segment_build(state, ["A-B-1", "B-C-1"])

    assert not success
    assert "same route" in message
    assert not state.segments["A-B-1"].built
    assert not state.segments["B-C-1"].built


def test_reverse_route_order_is_rejected() -> None:
    state = make_segment_state()

    _, success, message = apply_segment_build(state, ["A-B-2", "A-B-1"])

    assert not success
    assert "increasing route order" in message


def test_unknown_segment_is_rejected() -> None:
    state = make_segment_state()

    _, success, message = apply_segment_build(state, ["unknown-segment"])

    assert not success
    assert "do not exist" in message


def test_already_built_segment_is_rejected_without_another_action() -> None:
    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["A-B-1"])
    assert success, message
    actions_after_first_build = state.actions_remaining
    money_after_first_build = state.player.money

    _, success, message = apply_segment_build(state, ["A-B-1"])

    assert not success
    assert "already built" in message
    assert state.actions_remaining == actions_after_first_build
    assert state.player.money == money_after_first_build


def test_legacy_map_has_only_legacy_build_actions() -> None:
    state = reset_game(map_path=LEGACY_MAP, config_path=LEGACY_CONFIG)
    actions = get_legal_actions(state)

    assert any(action.action_type == "build_track" for action in actions)
    assert all(action.action_type != "build_track_segments" for action in actions)


def run_all() -> None:
    tests = [
        test_legal_segment_build_actions_are_generated,
        test_build_one_segment_uses_automatic_financing,
        test_build_multiple_consecutive_segments_succeeds,
        test_isolated_middle_segment_is_rejected,
        test_build_can_start_from_either_city_end,
        test_build_can_continue_from_incomplete_endpoint,
        test_completed_route_marks_all_segments_completed,
        test_income_removes_incomplete_segments,
        test_completed_route_survives_income_cleanup,
        test_legal_actions_exclude_isolated_middle_segment,
        test_empty_segment_list_is_rejected,
        test_more_than_four_segments_are_rejected,
        test_non_consecutive_segments_are_rejected,
        test_segments_from_different_routes_are_rejected,
        test_reverse_route_order_is_rejected,
        test_unknown_segment_is_rejected,
        test_already_built_segment_is_rejected_without_another_action,
        test_legacy_map_has_only_legacy_build_actions,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} segment build smoke tests passed.")


if __name__ == "__main__":
    run_all()
