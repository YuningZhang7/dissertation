from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.random_agent import RandomAgent
from experiments.simulation_runner import run_episode
from railways.environment import reset_game
from railways.map_loader import load_config, load_map
from railways.rules import get_legal_build_segment_actions

MAP_PATHS = [
    PROJECT_ROOT / "data" / "official_like_route_segment_map.json",
    PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json",
]
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
MAP_CONFIG_PAIRS = [(map_path, CONFIG_PATH) for map_path in MAP_PATHS]


def test_maps_load_successfully() -> None:
    for map_path in MAP_PATHS:
        cities, edges, _, routes, segments = load_map(map_path, include_routes=True)
        assert cities, f"{map_path.name} has no cities"
        assert edges == {}
        assert routes, f"{map_path.name} has no routes"
        assert segments, f"{map_path.name} has no track segments"


def test_maps_have_legal_initial_builds() -> None:
    for map_path, config_path in MAP_CONFIG_PAIRS:
        state = reset_game(map_path=map_path, config_path=config_path)
        assert get_legal_build_segment_actions(
            state
        ), f"{map_path.name} has no legal segment builds"


def test_route_endpoints_reference_valid_cities() -> None:
    for map_path in MAP_PATHS:
        cities, _, _, routes, _ = load_map(map_path, include_routes=True)
        city_ids = set(cities)
        for route in routes.values():
            assert route.city_a in city_ids, f"{route.id} has invalid city_a"
            assert route.city_b in city_ids, f"{route.id} has invalid city_b"


def test_major_lines_reference_valid_cities() -> None:
    for map_path in MAP_PATHS:
        cities, _, major_lines = load_map(map_path)
        city_ids = set(cities)
        for major_line in major_lines.values():
            assert major_line.source in city_ids, f"{major_line.id} has invalid source"
            assert major_line.target in city_ids, f"{major_line.id} has invalid target"


def test_goods_colours_are_valid() -> None:
    for map_path, config_path in MAP_CONFIG_PAIRS:
        config = load_config(config_path)
        allowed_colours = set(config.allowed_good_colors)
        cities, _, _ = load_map(map_path)
        for city in cities.values():
            if city.demand_color is not None:
                assert city.demand_color in allowed_colours
            for good in city.goods:
                assert good in allowed_colours


def test_random_agent_short_episode_does_not_crash() -> None:
    for map_path, config_path in MAP_CONFIG_PAIRS:
        result = run_episode(
            RandomAgent(seed=1),
            seed=1,
            max_steps=80,
            map_path=map_path,
            config_path=config_path,
        )
        assert result["actions_taken"] > 0
        assert result["invalid_actions"] >= 0


def test_greedy_delivery_short_episode_does_not_crash() -> None:
    for map_path, config_path in MAP_CONFIG_PAIRS:
        result = run_episode(
            GreedyDeliveryAgent(seed=2),
            seed=2,
            max_steps=80,
            map_path=map_path,
            config_path=config_path,
        )
        assert result["actions_taken"] > 0
        assert result["invalid_actions"] >= 0


def run_all() -> None:
    tests = [
        test_maps_load_successfully,
        test_maps_have_legal_initial_builds,
        test_route_endpoints_reference_valid_cities,
        test_major_lines_reference_valid_cities,
        test_goods_colours_are_valid,
        test_random_agent_short_episode_does_not_crash,
        test_greedy_delivery_short_episode_does_not_crash,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} map smoke tests passed.")


if __name__ == "__main__":
    run_all()
