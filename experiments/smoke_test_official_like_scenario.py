from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.rules import get_route_segments, uses_route_segment_delivery


OFFICIAL_LIKE_MAP = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def make_state():
    return reset_game(map_path=OFFICIAL_LIKE_MAP, config_path=OFFICIAL_CONFIG)


def build_segments(state, segment_ids: list[str]) -> None:
    _, success, message = apply_action(
        state,
        Action.build_track_segments(segment_ids),
    )
    assert success, message


def test_map_loads_with_medium_route_segment_structure() -> None:
    state = make_state()

    assert len(state.cities) == 10
    assert len(state.routes) == 15
    assert len(state.segments) == 38
    assert len(state.major_lines) == 4
    assert state.edges == {}
    assert uses_route_segment_delivery(state)


def test_city_palette_goods_and_gray_cities_are_valid() -> None:
    state = make_state()
    allowed_colors = set(state.config.allowed_good_colors)
    demand_colors = {
        city.demand_color
        for city in state.cities.values()
        if city.demand_color is not None
    }
    gray_cities = [city for city in state.cities.values() if city.is_gray]

    assert {"red", "blue", "yellow", "green", "black", "purple"}.issubset(
        demand_colors
    )
    assert len(gray_cities) == 2
    assert all(not city.is_urbanized for city in gray_cities)
    assert all(
        good in allowed_colors
        for city in state.cities.values()
        for good in city.goods
    )


def test_routes_have_consistent_segments_terrain_and_costs() -> None:
    state = make_state()
    allowed_costs = {
        "plain": {2},
        "water": {3},
        "mountain": {4, 5},
    }

    for route in state.routes.values():
        route_segments = get_route_segments(state, route.id)
        assert 1 <= len(route_segments) <= 4
        assert route_segments[0].source_node == route.city_a
        assert route_segments[-1].target_node == route.city_b
        for segment in route_segments:
            assert segment.id.startswith(f"{route.id}-")
            assert segment.terrain in allowed_costs
            assert segment.cost in allowed_costs[segment.terrain]


def test_initial_legal_segment_build_actions_exist() -> None:
    state = make_state()
    segment_builds = [
        action
        for action in get_legal_actions(state)
        if action.action_type == "build_track_segments"
    ]

    assert segment_builds
    assert any(action.params["segment_ids"] == ["A-H-1", "A-H-2"] for action in segment_builds)


def test_short_route_enables_segment_distance_delivery() -> None:
    state = make_state()
    build_segments(state, ["A-H-1", "A-H-2"])
    assert state.routes["A-H"].completed
    state.player.locomotive_level = 2

    deliveries = [
        action
        for action in get_legal_actions(state)
        if action.action_type == "deliver_good"
        and action.params["source"] == "A"
        and action.params["target"] == "H"
        and action.params["good_color"] == "blue"
    ]
    assert deliveries
    assert deliveries[0].params["path_length"] == 2

    _, success, message = apply_action(state, deliveries[0])
    assert success, message
    assert state.player.score == 2
    assert state.player.delivered_goods_count == 1


def test_multi_route_path_claims_major_line() -> None:
    state = make_state()

    build_segments(state, ["A-H-1", "A-H-2"])
    build_segments(state, ["F-H-1", "F-H-2"])

    assert state.major_lines["A-F"].claimed
    assert state.player.major_line_bonus == 8
    assert any("claimed major line A-F" in entry for entry in state.action_history)


def test_income_cleanup_removes_incomplete_scenario_track() -> None:
    state = make_state()
    build_segments(state, ["H-G-1"])
    assert state.segments["H-G-1"].built
    assert not state.segments["H-G-1"].completed

    assert apply_action(state, Action.pass_action())[1]
    assert apply_action(state, Action.pass_action())[1]

    assert not state.segments["H-G-1"].built
    assert state.segments["H-G-1"].owner is None


def run_all() -> None:
    tests = [
        test_map_loads_with_medium_route_segment_structure,
        test_city_palette_goods_and_gray_cities_are_valid,
        test_routes_have_consistent_segments_terrain_and_costs,
        test_initial_legal_segment_build_actions_exist,
        test_short_route_enables_segment_distance_delivery,
        test_multi_route_path_claims_major_line,
        test_income_cleanup_removes_incomplete_scenario_track,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} official-like scenario smoke tests passed.")


if __name__ == "__main__":
    run_all()
