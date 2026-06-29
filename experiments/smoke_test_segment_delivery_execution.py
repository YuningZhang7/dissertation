from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.rules import get_legal_deliveries, uses_route_segment_delivery


ROUTE_MAP = PROJECT_ROOT / "data" / "mini_route_segment_map.json"
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
LEGACY_MAP = PROJECT_ROOT / "data" / "toy_map.json"
LEGACY_CONFIG = PROJECT_ROOT / "data" / "rules_config.json"


def make_segment_state():
    return reset_game(map_path=ROUTE_MAP, config_path=OFFICIAL_CONFIG)


def complete_route(state, segment_ids: list[str]) -> None:
    _, success, message = apply_action(
        state,
        Action.build_track_segments(segment_ids),
    )
    assert success, message


def complete_a_b_route(state) -> None:
    complete_route(state, ["A-B-1", "A-B-2"])


def test_delivery_mode_matches_map_format() -> None:
    segment_state = make_segment_state()
    legacy_state = reset_game(map_path=LEGACY_MAP, config_path=LEGACY_CONFIG)

    assert uses_route_segment_delivery(segment_state)
    assert not uses_route_segment_delivery(legacy_state)


def test_no_segment_delivery_before_route_completion() -> None:
    state = make_segment_state()

    legal_deliveries = get_legal_deliveries(state)

    assert legal_deliveries == []
    assert all(
        action.action_type != "deliver_good" for action in get_legal_actions(state)
    )


def test_completed_route_generates_legal_delivery() -> None:
    state = make_segment_state()
    complete_a_b_route(state)
    state.player.locomotive_level = 2

    legal = get_legal_actions(state)
    matching_deliveries = [
        action
        for action in legal
        if action.action_type == "deliver_good"
        and action.params["source"] == "A"
        and action.params["target"] == "B"
        and action.params["good_color"] == "blue"
        and action.params["path"] == ["A", "B"]
    ]

    assert matching_deliveries
    assert matching_deliveries[0].params["path_length"] == 2
    assert matching_deliveries[0].params["score"] == 2


def test_segment_delivery_removes_good_scores_and_places_ecm() -> None:
    state = make_segment_state()
    complete_a_b_route(state)
    state.player.locomotive_level = 2
    starting_score = state.player.score
    starting_actions = state.actions_remaining

    _, success, message = apply_action(
        state,
        Action.deliver_good("A", "B", "blue", path=["A", "B"]),
    )

    assert success, message
    assert "blue" not in state.cities["A"].goods
    assert state.cities["A"].empty_marker
    assert state.player.score == starting_score + 2
    assert state.player.delivered_goods_count == 1
    assert state.actions_remaining == starting_actions - 1


def test_segment_delivery_rejects_route_over_locomotive_level() -> None:
    state = make_segment_state()
    complete_a_b_route(state)
    starting_actions = state.actions_remaining

    assert all(
        not (
            action.params["source"] == "A"
            and action.params["target"] == "B"
        )
        for action in get_legal_deliveries(state)
    )

    _, success, message = apply_action(
        state,
        Action.deliver_good("A", "B", "blue", path=["A", "B"]),
    )

    assert not success
    assert "exceeds locomotive" in message
    assert state.cities["A"].goods == ["blue"]
    assert state.actions_remaining == starting_actions


def test_segment_delivery_selects_shortest_path_when_omitted() -> None:
    state = make_segment_state()
    complete_a_b_route(state)
    state.player.locomotive_level = 2

    _, success, message = apply_action(
        state,
        Action.deliver_good("A", "B", "blue"),
    )

    assert success, message
    assert state.player.score == 2
    assert "blue" not in state.cities["A"].goods


def test_incomplete_route_cannot_execute_delivery() -> None:
    state = make_segment_state()
    complete_route(state, ["A-B-1"])
    state.player.locomotive_level = 2

    _, success, message = apply_action(
        state,
        Action.deliver_good("A", "B", "blue", path=["A", "B"]),
    )

    assert not success
    assert "completed route segments" in message
    assert state.cities["A"].goods == ["blue"]


def test_multi_route_delivery_scores_total_segment_distance() -> None:
    state = make_segment_state()
    state.cities["B"].demand_color = "red"
    state.cities["C"].is_gray = False
    state.cities["C"].demand_color = "blue"
    complete_a_b_route(state)
    complete_route(state, ["B-C-1", "B-C-2", "B-C-3"])
    state.player.locomotive_level = 5

    _, success, message = apply_action(
        state,
        Action.deliver_good("A", "C", "blue", path=["A", "B", "C"]),
    )

    assert success, message
    assert state.player.score == 5
    assert state.player.delivered_goods_count == 1


def test_gray_target_remains_illegal_in_segment_mode() -> None:
    state = make_segment_state()
    state.cities["C"].demand_color = "red"
    complete_route(state, ["B-C-1", "B-C-2", "B-C-3"])
    state.player.locomotive_level = 3

    assert all(action.params["target"] != "C" for action in get_legal_deliveries(state))
    _, success, message = apply_action(
        state,
        Action.deliver_good("B", "C", "red", path=["B", "C"]),
    )

    assert not success
    assert "gray city" in message
    assert state.cities["B"].goods == ["red"]


def test_legacy_delivery_execution_is_unchanged() -> None:
    state = reset_game(map_path=LEGACY_MAP, config_path=LEGACY_CONFIG)
    _, success, message = apply_action(state, Action.build_track("A-B"))
    assert success, message
    starting_score = state.player.score
    starting_actions = state.actions_remaining

    _, success, message = apply_action(
        state,
        Action.deliver_good("A", "B", "blue", path=["A", "B"]),
    )

    assert success, message
    assert state.player.score == starting_score + 1
    assert state.player.delivered_goods_count == 1
    assert state.actions_remaining == starting_actions - 1


def run_all() -> None:
    tests = [
        test_delivery_mode_matches_map_format,
        test_no_segment_delivery_before_route_completion,
        test_completed_route_generates_legal_delivery,
        test_segment_delivery_removes_good_scores_and_places_ecm,
        test_segment_delivery_rejects_route_over_locomotive_level,
        test_segment_delivery_selects_shortest_path_when_omitted,
        test_incomplete_route_cannot_execute_delivery,
        test_multi_route_delivery_scores_total_segment_distance,
        test_gray_target_remains_illegal_in_segment_mode,
        test_legacy_delivery_execution_is_unchanged,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} segment delivery execution smoke tests passed.")


if __name__ == "__main__":
    run_all()
