from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, reset_game
from railways.rules import (
    completed_route_path_segment_length,
    find_all_completed_route_delivery_paths,
    find_all_legal_delivery_paths,
    get_built_graph,
    get_completed_route_graph,
    validate_completed_route_delivery_path,
)


ROUTE_MAP = PROJECT_ROOT / "data" / "mini_route_segment_map.json"
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
LEGACY_MAP = PROJECT_ROOT / "data" / "toy_map.json"
LEGACY_CONFIG = PROJECT_ROOT / "data" / "rules_config.json"


def make_segment_state():
    return reset_game(map_path=ROUTE_MAP, config_path=OFFICIAL_CONFIG)


def apply_segment_build(state, segment_ids: list[str]):
    return apply_action(state, Action.build_track_segments(segment_ids))


def complete_a_b_route(state) -> None:
    _, success, message = apply_segment_build(state, ["A-B-1", "A-B-2"])
    assert success, message


def test_incomplete_segments_are_not_in_completed_route_graph() -> None:
    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["A-B-1"])
    assert success, message

    graph = get_completed_route_graph(state)

    assert not graph.has_edge("A", "B")


def test_completed_route_graph_contains_segment_metadata() -> None:
    state = make_segment_state()
    complete_a_b_route(state)

    graph = get_completed_route_graph(state)

    assert graph.has_edge("A", "B")
    assert graph["A"]["B"]["route_id"] == "A-B"
    assert graph["A"]["B"]["segment_ids"] == ["A-B-1", "A-B-2"]
    assert graph["A"]["B"]["segment_count"] == 2


def test_completed_route_graph_requires_built_player_owned_segments() -> None:
    state = make_segment_state()
    complete_a_b_route(state)

    state.segments["A-B-1"].owner = None
    assert not get_completed_route_graph(state).has_edge("A", "B")

    state.segments["A-B-1"].owner = "player"
    state.segments["A-B-1"].built = False
    assert not get_completed_route_graph(state).has_edge("A", "B")


def test_completed_route_path_length_uses_segment_count() -> None:
    state = make_segment_state()
    complete_a_b_route(state)

    assert completed_route_path_segment_length(state, ["A", "B"]) == 2
    assert completed_route_path_segment_length(state, ["A", "C"]) == 10**9


def test_completed_route_validation_respects_locomotive_level() -> None:
    state = make_segment_state()
    complete_a_b_route(state)

    valid, message = validate_completed_route_delivery_path(
        state,
        ["A", "B"],
        "A",
        "B",
        "blue",
    )
    assert not valid
    assert "exceeds locomotive" in message

    state.player.locomotive_level = 2
    valid, message = validate_completed_route_delivery_path(
        state,
        ["A", "B"],
        "A",
        "B",
        "blue",
    )
    assert valid, message


def test_path_search_finds_completed_route_after_engine_upgrade() -> None:
    state = make_segment_state()
    complete_a_b_route(state)
    state.player.locomotive_level = 2

    paths = find_all_completed_route_delivery_paths(state, "A", "B", "blue")

    assert ["A", "B"] in paths


def test_cleanup_keeps_incomplete_route_out_of_delivery_graph() -> None:
    state = make_segment_state()
    _, success, message = apply_segment_build(state, ["B-C-1"])
    assert success, message

    assert apply_action(state, Action.pass_action())[1]
    assert apply_action(state, Action.pass_action())[1]

    assert not state.segments["B-C-1"].built
    assert not get_completed_route_graph(state).has_edge("B", "C")


def test_legacy_edge_delivery_helpers_still_work() -> None:
    state = reset_game(map_path=LEGACY_MAP, config_path=LEGACY_CONFIG)
    _, success, message = apply_action(state, Action.build_track("A-B"))
    assert success, message

    graph = get_built_graph(state)
    paths = find_all_legal_delivery_paths(state, "A", "B", "blue")

    assert graph.has_edge("A", "B")
    assert ["A", "B"] in paths
    assert not get_completed_route_graph(state).has_edge("A", "B")


def run_all() -> None:
    tests = [
        test_incomplete_segments_are_not_in_completed_route_graph,
        test_completed_route_graph_contains_segment_metadata,
        test_completed_route_graph_requires_built_player_owned_segments,
        test_completed_route_path_length_uses_segment_count,
        test_completed_route_validation_respects_locomotive_level,
        test_path_search_finds_completed_route_after_engine_upgrade,
        test_cleanup_keeps_incomplete_route_out_of_delivery_graph,
        test_legacy_edge_delivery_helpers_still_work,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} completed-route delivery helper smoke tests passed.")


if __name__ == "__main__":
    run_all()
