from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import create_agent
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game


OFFICIAL_LIKE_MAP = (
    PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)


def official_like_state():
    return reset_game(map_path=OFFICIAL_LIKE_MAP, config_path=OFFICIAL_CONFIG)


def test_agent_is_registered() -> None:
    assert create_agent("route_segment_greedy", seed=42) is not None


def test_agent_returns_legal_action() -> None:
    state = official_like_state()
    action = create_agent("route_segment_greedy", seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_prefers_delivery_when_available() -> None:
    state = official_like_state()
    _, success, message = apply_action(
        state,
        Action.build_track_segments(["A-H-1", "A-H-2"]),
    )
    assert success, message
    state.player.locomotive_level = 2

    action = create_agent("route_segment_greedy", seed=42).choose_action(state)
    assert action.action_type == "deliver_good"
    assert action.params["source"] == "A"
    assert action.params["target"] == "H"


def test_agent_completes_a_short_route_early() -> None:
    state = official_like_state()
    action = create_agent("route_segment_greedy", seed=42).choose_action(state)
    assert action.action_type == "build_track_segments"
    assert action in get_legal_actions(state)


def test_agent_is_deterministic_under_same_seed() -> None:
    state = official_like_state()
    first = create_agent("route_segment_greedy", seed=42).choose_action(state.copy())
    second = create_agent("route_segment_greedy", seed=42).choose_action(state.copy())
    assert first == second


def run_all() -> None:
    tests = [
        test_agent_is_registered,
        test_agent_returns_legal_action,
        test_agent_prefers_delivery_when_available,
        test_agent_completes_a_short_route_early,
        test_agent_is_deterministic_under_same_seed,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} route-segment greedy agent smoke tests passed.")


if __name__ == "__main__":
    run_all()
