from __future__ import annotations

from pathlib import Path
import random
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import create_agent, list_agent_names
from agents.urbanization_aware_lookahead_greedy_agent import (
    _candidate_actions,
    _score_urbanize_action,
)
from experiments.animate_agent_episode import run_agent_episode_animation
from experiments.run_agent_benchmark import run_benchmark
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game


OFFICIAL_LIKE_MAP = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
EXPANDED_MAP = PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
AGENT_NAME = "urbanization_aware_lookahead_greedy"


def make_state(map_path: Path = OFFICIAL_LIKE_MAP):
    return reset_game(map_path=map_path, config_path=OFFICIAL_CONFIG)


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
            (key, value.built, value.completed, value.owner)
            for key, value in state.segments.items()
        ),
        tuple((key, value.completed) for key, value in state.routes.items()),
        tuple((key, value.claimed) for key, value in state.major_lines.items()),
        tuple(
            (key, value.claimed)
            for key, value in state.rail_baron_objectives.items()
        ),
        tuple(
            (
                key,
                value.demand_color,
                tuple(value.goods),
                value.is_gray,
                value.is_urbanized,
                value.empty_marker,
            )
            for key, value in state.cities.items()
        ),
        tuple(state.action_history),
    )


def test_agent_is_registered() -> None:
    assert AGENT_NAME in list_agent_names()
    assert create_agent(AGENT_NAME, seed=42).name == AGENT_NAME


def test_agent_returns_legal_action() -> None:
    state = make_state()
    action = create_agent(AGENT_NAME, seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_is_deterministic() -> None:
    first = create_agent(AGENT_NAME, seed=1).choose_action(make_state())
    second = create_agent(AGENT_NAME, seed=999).choose_action(make_state())
    assert first == second


def test_action_selection_does_not_mutate_state() -> None:
    state = make_state()
    before = state_signature(state)
    create_agent(AGENT_NAME, seed=42).choose_action(state)
    assert state_signature(state) == before


def test_action_selection_preserves_global_random_state() -> None:
    state = make_state()
    random.seed(67890)
    before_random_state = random.getstate()

    create_agent(AGENT_NAME, seed=42).choose_action(state)

    assert random.getstate() == before_random_state


def test_agent_supports_official_like_map() -> None:
    state = make_state(OFFICIAL_LIKE_MAP)
    action = create_agent(AGENT_NAME, seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_supports_expanded_map() -> None:
    state = make_state(EXPANDED_MAP)
    action = create_agent(AGENT_NAME, seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_does_not_choose_issue_bond() -> None:
    state = make_state()
    action = create_agent(AGENT_NAME, seed=42).choose_action(state)
    assert action.action_type != "issue_bond"
    assert all(action.action_type != "issue_bond" for action in get_legal_actions(state))


def test_action_urbanize_equality_and_hash() -> None:
    first = Action.urbanize("J", demand_color="red")
    second = Action.urbanize("J", demand_color="red")
    different = Action.urbanize("J", demand_color="blue")

    assert first == second
    assert hash(first) == hash(second)
    assert first != different
    assert hash(first) != hash(different)


def test_common_action_types_are_hashable() -> None:
    actions = [
        Action.build_track_segments(["A-H-1", "A-H-2"]),
        Action.deliver_good("A", "F", "red", path=["A", "H", "F"]),
        Action.urbanize("J", demand_color="red"),
        Action.upgrade_engine(),
        Action.pass_action(),
        Action.next_turn(),
    ]

    hashes = [hash(action) for action in actions]

    assert len(hashes) == len(actions)
    assert hash(Action.build_track_segments(["A-H-1", "A-H-2"])) == hash(
        Action.build_track_segments(["A-H-1", "A-H-2"])
    )
    assert hash(Action.deliver_good("A", "F", "red", path=["A", "H", "F"])) == hash(
        Action.deliver_good("A", "F", "red", path=["A", "H", "F"])
    )


def test_legal_actions_include_colored_urbanize_actions() -> None:
    state = make_state()
    legal_urbanize = [
        action for action in get_legal_actions(state) if action.action_type == "urbanize"
    ]
    gray_city_ids = [city.id for city in state.cities.values() if city.is_gray]
    expected = {
        Action.urbanize(city_id, demand_color=color)
        for city_id in gray_city_ids
        for color in state.config.allowed_good_colors
    }

    assert legal_urbanize
    assert set(legal_urbanize) == expected
    assert all(
        action.params.get("demand_color") in state.config.allowed_good_colors
        for action in legal_urbanize
    )
    assert all(action.params.get("demand_color") is not None for action in legal_urbanize)


def test_colored_urbanize_apply_sets_selected_demand() -> None:
    state = make_state()
    city_id = next(city.id for city in state.cities.values() if city.is_gray)
    color = state.config.allowed_good_colors[0]
    action = Action.urbanize(city_id, demand_color=color)

    assert action in get_legal_actions(state)
    _, success, message = apply_action(state, action)

    assert success, message
    assert state.cities[city_id].demand_color == color
    assert not state.cities[city_id].is_gray


def test_agent_can_return_colored_urbanize_action() -> None:
    state = make_state()
    state.routes = {}
    state.segments = {}
    state.player.locomotive_level = state.config.max_locomotive_level

    action = create_agent(AGENT_NAME, seed=42).choose_action(state)

    assert action.action_type == "urbanize"
    assert action.params.get("demand_color") in state.config.allowed_good_colors
    assert action in get_legal_actions(state)


def test_agent_considers_deterministic_urbanize_candidates() -> None:
    state = make_state()
    legal_actions = get_legal_actions(state)
    candidates = _candidate_actions(state, legal_actions)
    urbanize_candidates = [
        candidate for candidate in candidates if candidate.action.action_type == "urbanize"
    ]

    assert urbanize_candidates
    assert all(candidate.action == candidate.return_action for candidate in urbanize_candidates)
    assert all(candidate.action in legal_actions for candidate in urbanize_candidates)
    assert all(
        candidate.action.params.get("demand_color") in state.config.allowed_good_colors
        for candidate in urbanize_candidates
    )


def test_urbanize_has_positive_potential_and_preserves_random_state() -> None:
    state = make_state()
    random.seed(12345)
    before_random_state = random.getstate()

    scores = [
        _score_urbanize_action(state, Action.urbanize(city.id, color))
        for city in state.cities.values()
        if city.is_gray
        for color in state.config.allowed_good_colors
    ]

    assert random.getstate() == before_random_state
    assert max(scores) > 0


def test_replay_compatibility() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir, summary = run_agent_episode_animation(
            map_name="official_like",
            agent_name=AGENT_NAME,
            seed=42,
            max_steps=3,
            frame_mode="events",
            output_root=temp_dir,
        )
        assert summary["success"] is True
        assert summary["fallback_actions"] == 0
        assert (run_dir / "index.html").exists()
        assert (run_dir / "episode_summary.json").exists()


def test_benchmark_compatibility() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        rows, summary, output = run_benchmark(
            maps=["official_like"],
            agents=[AGENT_NAME],
            episodes=1,
            max_steps=3,
            base_seed=42,
            output_dir=temp_dir,
        )
        assert len(rows) == 1
        assert rows[0]["success"] is True
        assert "urbanize_actions" in rows[0]
        assert "urbanized_city_count" in rows[0]
        assert AGENT_NAME in summary["official_like"]
        assert (output / "benchmark_rows.csv").exists()
        assert (output / "benchmark_summary.json").exists()


def run_all() -> None:
    tests = [
        test_agent_is_registered,
        test_agent_returns_legal_action,
        test_agent_is_deterministic,
        test_action_selection_does_not_mutate_state,
        test_action_selection_preserves_global_random_state,
        test_agent_supports_official_like_map,
        test_agent_supports_expanded_map,
        test_agent_does_not_choose_issue_bond,
        test_action_urbanize_equality_and_hash,
        test_common_action_types_are_hashable,
        test_legal_actions_include_colored_urbanize_actions,
        test_colored_urbanize_apply_sets_selected_demand,
        test_agent_can_return_colored_urbanize_action,
        test_agent_considers_deterministic_urbanize_candidates,
        test_urbanize_has_positive_potential_and_preserves_random_state,
        test_replay_compatibility,
        test_benchmark_compatibility,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} urbanization-aware lookahead greedy smoke tests passed.")


if __name__ == "__main__":
    run_all()
