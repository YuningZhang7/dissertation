from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.objective_aware_greedy_agent import (
    _rail_baron_remaining_distance,
    _score_build_action,
)
from agents.registry import create_agent
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game


OFFICIAL_LIKE_MAP = (
    PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
)
EXPANDED_MAP = (
    PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)


def make_official_state():
    return reset_game(
        map_path=OFFICIAL_LIKE_MAP,
        config_path=OFFICIAL_CONFIG,
        rail_baron_objective_id="RB-A-F",
    )


def test_agent_is_registered() -> None:
    agent = create_agent("objective_aware_greedy", seed=42)
    assert agent.name == "objective_aware_greedy"


def test_agent_returns_legal_action() -> None:
    state = make_official_state()
    action = create_agent("objective_aware_greedy", seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_is_deterministic() -> None:
    first_state = make_official_state()
    second_state = make_official_state()
    first = create_agent("objective_aware_greedy", seed=42).choose_action(first_state)
    second = create_agent("objective_aware_greedy", seed=42).choose_action(second_state)
    assert first == second


def test_agent_prefers_rail_baron_progress() -> None:
    state = make_official_state()
    before_distance = _rail_baron_remaining_distance(state)
    action = create_agent("objective_aware_greedy", seed=42).choose_action(state)
    assert action.action_type == "build_track_segments"
    candidate = state.copy()
    _, applied, message = apply_action(candidate, action)
    assert applied, message
    assert _rail_baron_remaining_distance(candidate) < before_distance


def test_objective_build_outscores_unrelated_expensive_build() -> None:
    state = make_official_state()
    useful = Action.build_track_segments(["A-H-1", "A-H-2"])
    unrelated = Action.build_track_segments(["E-J-1", "E-J-2", "E-J-3"])
    legal_actions = get_legal_actions(state)
    before = (
        state.player.money,
        state.player.bonds,
        tuple(segment.built for segment in state.segments.values()),
        tuple(state.action_history),
    )
    assert useful in legal_actions
    assert unrelated in legal_actions
    assert _score_build_action(state, useful) > _score_build_action(state, unrelated)
    assert before == (
        state.player.money,
        state.player.bonds,
        tuple(segment.built for segment in state.segments.values()),
        tuple(state.action_history),
    )


def test_agent_does_not_crash_on_expanded_map() -> None:
    state = reset_game(map_path=EXPANDED_MAP, config_path=OFFICIAL_CONFIG)
    action = create_agent("objective_aware_greedy", seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def run_all() -> None:
    tests = [
        test_agent_is_registered,
        test_agent_returns_legal_action,
        test_agent_is_deterministic,
        test_agent_prefers_rail_baron_progress,
        test_objective_build_outscores_unrelated_expensive_build,
        test_agent_does_not_crash_on_expanded_map,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} objective-aware greedy agent smoke tests passed.")


if __name__ == "__main__":
    run_all()
