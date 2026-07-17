from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.environment import reset_game
from railways.map_loader import load_map


LEGACY_MAP = PROJECT_ROOT / "data" / "toy_map.json"
ROUTE_MAP = PROJECT_ROOT / "data" / "mini_route_segment_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def test_legacy_edge_map_is_rejected_with_clear_error() -> None:
    try:
        load_map(LEGACY_MAP, include_routes=True)
    except ValueError as exc:
        assert "Route-segment runtime requires" in str(exc)
        assert "Legacy edge-only maps are not supported" in str(exc)
    else:
        raise AssertionError("Legacy edge-only map should be rejected.")


def test_route_segment_map_loads_models_and_generated_nodes() -> None:
    cities, edges, _, routes, segments = load_map(
        ROUTE_MAP,
        include_routes=True,
    )

    assert len(cities) == 3
    assert edges == {}
    assert len(routes) == 2
    assert len(segments) == 5
    assert routes["A-B"].segment_ids == ["A-B-1", "A-B-2"]

    first_segment = segments["A-B-1"]
    assert first_segment.route_id == "A-B"
    assert first_segment.index == 0
    assert first_segment.source_node == "A"
    assert first_segment.target_node == "A-B:n1"
    assert first_segment.terrain == "plain"
    assert first_segment.cost == 2
    assert segments["A-B-2"].target_node == "B"

    assert segments["B-C-1"].source_node == "B"
    assert segments["B-C-1"].target_node == "B-C:n1"
    assert segments["B-C-2"].source_node == "B-C:n1"
    assert segments["B-C-2"].target_node == "B-C:n2"
    assert segments["B-C-3"].target_node == "C"


def test_route_segment_major_line_loads() -> None:
    _, _, major_lines, _, _ = load_map(ROUTE_MAP, include_routes=True)

    assert "A-C" in major_lines
    assert major_lines["A-C"].source == "A"
    assert major_lines["A-C"].target == "C"
    assert major_lines["A-C"].bonus_points == 5


def test_game_state_copy_and_reset_preserve_route_data() -> None:
    state = reset_game(map_path=ROUTE_MAP, config_path=CONFIG_PATH)

    assert len(state.routes) == 2
    assert len(state.segments) == 5
    copied = state.copy()
    assert copied.routes == state.routes
    assert copied.segments == state.segments

    copied.routes["A-B"].completed = True
    copied.segments["A-B-1"].built = True
    assert not state.routes["A-B"].completed
    assert not state.segments["A-B-1"].built

    state.routes["A-B"].completed = True
    state.segments["A-B-1"].built = True
    state.reset()
    assert not state.routes["A-B"].completed
    assert not state.segments["A-B-1"].built


def run_all() -> None:
    tests = [
        test_legacy_edge_map_is_rejected_with_clear_error,
        test_route_segment_map_loads_models_and_generated_nodes,
        test_route_segment_major_line_loads,
        test_game_state_copy_and_reset_preserve_route_data,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} route-segment loader smoke tests passed.")


if __name__ == "__main__":
    run_all()
