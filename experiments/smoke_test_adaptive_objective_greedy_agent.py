from __future__ import annotations

from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.adaptive_objective_greedy_agent import (
    _adaptive_features,
    _rail_baron_roi_progress,
    _score_action,
    _weights_for_state,
)
from agents.objective_aware_greedy_agent import _rail_baron_remaining_distance
from agents.registry import create_agent
from experiments.animate_agent_episode import run_agent_episode_animation
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game


OFFICIAL_LIKE_MAP = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
EXPANDED_MAP = (
    PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
)
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def make_state():
    return reset_game(
        map_path=OFFICIAL_LIKE_MAP,
        config_path=OFFICIAL_CONFIG,
        rail_baron_objective_id="RB-A-F",
    )


def state_signature(state) -> tuple:
    return (
        state.turn,
        state.phase,
        state.actions_remaining,
        state.player.money,
        state.player.bonds,
        state.player.score,
        state.player.locomotive_level,
        tuple(
            (key, value.built, value.completed)
            for key, value in state.segments.items()
        ),
        tuple((key, value.completed) for key, value in state.routes.items()),
        tuple((key, value.claimed) for key, value in state.major_lines.items()),
        tuple(
            (key, value.claimed)
            for key, value in state.rail_baron_objectives.items()
        ),
        tuple((key, tuple(value.goods)) for key, value in state.cities.items()),
    )


def test_agent_is_registered() -> None:
    agent = create_agent("adaptive_objective_greedy", seed=42)
    assert agent.name == "adaptive_objective_greedy"


def test_agent_returns_legal_action() -> None:
    state = make_state()
    action = create_agent("adaptive_objective_greedy", seed=42).choose_action(
        state
    )
    assert action in get_legal_actions(state)


def test_agent_is_deterministic() -> None:
    first = create_agent("adaptive_objective_greedy", seed=42).choose_action(
        make_state()
    )
    second = create_agent("adaptive_objective_greedy", seed=99).choose_action(
        make_state()
    )
    assert first == second


def test_action_selection_does_not_mutate_state() -> None:
    state = make_state()
    before = state_signature(state)
    create_agent("adaptive_objective_greedy", seed=42).choose_action(state)
    assert state_signature(state) == before


def test_agent_prefers_objective_progress() -> None:
    state = make_state()
    before_distance = _rail_baron_remaining_distance(state)
    action = create_agent("adaptive_objective_greedy", seed=42).choose_action(state)
    assert action.action_type == "build_track_segments"
    candidate = state.copy()
    _, applied, message = apply_action(candidate, action)
    assert applied, message
    assert (
        _rail_baron_remaining_distance(candidate) < before_distance
        or _rail_baron_roi_progress(state, candidate) > 0
    )


def test_objective_build_outscores_debt_heavy_build() -> None:
    state = make_state()
    weights = _weights_for_state(state)
    before = _adaptive_features(state)
    useful = Action.build_track_segments(["A-H-1", "A-H-2"])
    unrelated = Action.build_track_segments(["E-J-1", "E-J-2", "E-J-3"])
    assert _score_action(state, useful, before, weights) > _score_action(
        state,
        unrelated,
        before,
        weights,
    )


def test_agent_supports_expanded_map() -> None:
    state = reset_game(map_path=EXPANDED_MAP, config_path=OFFICIAL_CONFIG)
    action = create_agent("adaptive_objective_greedy", seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_animation_compatibility() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir, summary = run_agent_episode_animation(
            map_name="official_like",
            agent_name="adaptive_objective_greedy",
            seed=42,
            max_steps=10,
            frame_mode="events",
            output_root=temp_dir,
        )
        assert summary["success"] is True
        assert summary["fallback_actions"] == 0
        assert (run_dir / "index.html").exists()
        assert (run_dir / "episode_summary.json").exists()
        assert (run_dir / "episode_history.json").exists()


def run_all() -> None:
    tests = [
        test_agent_is_registered,
        test_agent_returns_legal_action,
        test_agent_is_deterministic,
        test_action_selection_does_not_mutate_state,
        test_agent_prefers_objective_progress,
        test_objective_build_outscores_debt_heavy_build,
        test_agent_supports_expanded_map,
        test_agent_animation_compatibility,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} adaptive objective greedy smoke tests passed.")


if __name__ == "__main__":
    run_all()
