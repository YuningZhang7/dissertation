from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.rules import get_route_segments, uses_route_segment_delivery


EXPANDED_MAP = (
    PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)


def make_state():
    return reset_game(map_path=EXPANDED_MAP, config_path=OFFICIAL_CONFIG)


def build_segments(state, segment_ids: list[str]) -> None:
    _, success, message = apply_action(
        state,
        Action.build_track_segments(segment_ids),
    )
    assert success, message


def test_map_loads_with_expanded_structure() -> None:
    state = make_state()

    assert 22 <= len(state.cities) <= 26
    assert 40 <= len(state.routes) <= 50
    assert 90 <= len(state.segments) <= 130
    assert len(state.major_lines) >= 8
    assert state.edges == {}
    assert uses_route_segment_delivery(state)


def test_gray_cities_are_valid() -> None:
    gray_cities = [city for city in make_state().cities.values() if city.is_gray]

    assert len(gray_cities) >= 5
    assert all(city.demand_color is None for city in gray_cities)
    assert all(city.goods == [] for city in gray_cities)
    assert all(not city.is_urbanized for city in gray_cities)


def test_goods_and_demand_colours_are_balanced() -> None:
    state = make_state()
    allowed = set(state.config.allowed_good_colors)
    demand_colours = [
        city.demand_color
        for city in state.cities.values()
        if city.demand_color is not None
    ]
    goods = [good for city in state.cities.values() for good in city.goods]

    assert set(demand_colours).issubset(allowed)
    assert set(goods).issubset(allowed)
    demand_counts = Counter(demand_colours)
    goods_counts = Counter(goods)
    assert all(demand_counts[colour] >= 3 for colour in allowed)
    assert all(goods_counts[colour] >= 3 for colour in allowed)


def test_routes_and_segments_are_consistent() -> None:
    state = make_state()
    terrain_costs = {
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
            assert segment.terrain in terrain_costs
            assert segment.cost in terrain_costs[segment.terrain]


def test_initial_legal_segment_build_actions_exist() -> None:
    segment_builds = [
        action
        for action in get_legal_actions(make_state())
        if action.action_type == "build_track_segments"
    ]
    assert segment_builds


def test_short_route_enables_delivery() -> None:
    state = make_state()
    build_segments(state, ["J-K-1", "J-K-2"])
    state.player.locomotive_level = 2

    deliveries = [
        action
        for action in get_legal_actions(state)
        if action.action_type == "deliver_good"
        and action.params["source"] == "J"
        and action.params["target"] == "K"
        and action.params["good_color"] == "blue"
    ]
    assert deliveries

    _, success, message = apply_action(state, deliveries[0])
    assert success, message
    assert state.player.delivered_goods_count == 1


def test_central_connector_major_line_can_be_claimed() -> None:
    state = make_state()
    build_segments(state, ["J-K-1", "J-K-2"])
    build_segments(state, ["K-L-1", "K-L-2"])

    assert state.major_lines["Central-Connector"].claimed
    assert state.player.major_line_bonus >= 5


def test_income_cleanup_removes_incomplete_track() -> None:
    state = make_state()
    build_segments(state, ["A-J-1"])
    assert state.segments["A-J-1"].built
    assert not state.segments["A-J-1"].completed

    assert apply_action(state, Action.pass_action())[1]
    assert apply_action(state, Action.pass_action())[1]

    assert not state.segments["A-J-1"].built
    assert state.segments["A-J-1"].owner is None


def run_all() -> None:
    tests = [
        test_map_loads_with_expanded_structure,
        test_gray_cities_are_valid,
        test_goods_and_demand_colours_are_balanced,
        test_routes_and_segments_are_consistent,
        test_initial_legal_segment_build_actions_exist,
        test_short_route_enables_delivery,
        test_central_connector_major_line_can_be_claimed,
        test_income_cleanup_removes_incomplete_track,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} expanded official-style map smoke tests passed.")


if __name__ == "__main__":
    run_all()
