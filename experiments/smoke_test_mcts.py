from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.mcts_agent import MCTSAgent, estimate_major_line_progress
from experiments.simulation_runner import run_episode
from railways.environment import get_legal_actions, reset_game
from railways.models import PHASE_GAME_OVER


def test_mcts_returns_legal_action() -> None:
    state = reset_game()
    agent = MCTSAgent(iterations=5, rollout_depth_limit=20, seed=0)
    action = agent.choose_action(state)
    assert action in get_legal_actions(state)


def test_mcts_choose_action_does_not_mutate_state() -> None:
    state = reset_game()
    before = _state_signature(state)
    agent = MCTSAgent(iterations=5, rollout_depth_limit=20, seed=1)
    agent.choose_action(state)
    after = _state_signature(state)
    assert before == after


def test_major_line_aware_mcts_returns_legal_action() -> None:
    state = reset_game(PROJECT_ROOT / "data" / "semi_realistic_map.json")
    agent = MCTSAgent(
        iterations=5,
        rollout_depth_limit=20,
        evaluation_mode="major_line_aware",
        seed=6,
    )
    before = _state_signature(state)
    action = agent.choose_action(state)
    after = _state_signature(state)
    assert action in get_legal_actions(state)
    assert before == after


def test_major_line_progress_estimate_is_non_negative() -> None:
    state = reset_game(PROJECT_ROOT / "data" / "semi_realistic_map.json")
    assert estimate_major_line_progress(state) >= 0.0


def test_mcts_completes_episode_on_toy_map() -> None:
    agent = MCTSAgent(iterations=5, rollout_depth_limit=20, seed=2)
    result = run_episode(
        agent,
        seed=2,
        max_steps=160,
        map_path=PROJECT_ROOT / "data" / "toy_map.json",
    )
    assert result["terminal"] is True
    assert result["actions_taken"] > 0


def test_mcts_completes_episode_on_medium_map() -> None:
    agent = MCTSAgent(iterations=5, rollout_depth_limit=20, seed=3)
    result = run_episode(
        agent,
        seed=3,
        max_steps=180,
        map_path=PROJECT_ROOT / "data" / "toy_medium_map.json",
    )
    assert result["terminal"] is True
    assert result["actions_taken"] > 0


def test_mcts_returns_pass_when_no_legal_actions_exist() -> None:
    state = reset_game()
    state.phase = PHASE_GAME_OVER
    agent = MCTSAgent(iterations=5, rollout_depth_limit=20, seed=4)
    action = agent.choose_action(state)
    assert action.action_type == "pass"
    assert get_legal_actions(state) == []


def test_mcts_smoke_runtime_is_reasonable() -> None:
    state = reset_game()
    agent = MCTSAgent(iterations=5, rollout_depth_limit=20, seed=5)
    start = time.perf_counter()
    agent.choose_action(state)
    runtime = time.perf_counter() - start
    assert runtime < 10.0


def _state_signature(state) -> tuple[Any, ...]:
    cities = tuple(
        sorted(
            (
                city_id,
                tuple(city.goods),
                city.demand_color,
                city.empty_marker,
                city.is_urbanized,
            )
            for city_id, city in state.cities.items()
        )
    )
    edges = tuple(
        sorted(
            (edge_id, edge.built, edge.owner)
            for edge_id, edge in state.edges.items()
        )
    )
    major_lines = tuple(
        sorted(
            (line_id, line.claimed)
            for line_id, line in state.major_lines.items()
        )
    )
    player = (
        state.player.money,
        state.player.score,
        state.player.bonds,
        state.player.locomotive_level,
        state.player.delivered_goods_count,
        tuple(sorted(state.player.built_edges)),
        state.player.major_line_bonus,
        state.player.rail_baron_bonus,
        state.player.operation_card_bonus,
    )
    return (
        cities,
        edges,
        major_lines,
        player,
        state.turn,
        state.phase,
        state.actions_remaining,
        state.end_triggered,
        state.extra_turns_remaining,
        tuple(state.action_history),
    )


def run_all() -> None:
    tests = [
        test_mcts_returns_legal_action,
        test_mcts_choose_action_does_not_mutate_state,
        test_major_line_aware_mcts_returns_legal_action,
        test_major_line_progress_estimate_is_non_negative,
        test_mcts_completes_episode_on_toy_map,
        test_mcts_completes_episode_on_medium_map,
        test_mcts_returns_pass_when_no_legal_actions_exist,
        test_mcts_smoke_runtime_is_reasonable,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} MCTS smoke tests passed.")


if __name__ == "__main__":
    run_all()
