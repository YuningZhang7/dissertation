from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.mcts_agent import MCTSAgent
from agents.random_agent import RandomAgent
from exact.exact_solver import ExactSolver, replay_actions
from experiments.simulation_runner import run_episode
from railways.environment import apply_action, copy_state, final_score, get_legal_actions, reset_game
from railways.map_loader import load_config, load_map

MICRO_MAP = PROJECT_ROOT / "data" / "micro_map.json"
MICRO_CONFIG = PROJECT_ROOT / "data" / "micro_rules_config.json"


def test_micro_map_and_config_load() -> None:
    cities, edges, major_lines = load_map(MICRO_MAP)
    config = load_config(MICRO_CONFIG)
    assert len(cities) >= 4
    assert len(edges) >= 5
    assert major_lines
    assert config.max_turns <= 6


def test_copy_apply_does_not_mutate_original() -> None:
    state = reset_game(MICRO_MAP, MICRO_CONFIG)
    before = _state_signature(state)
    action = get_legal_actions(state)[0]
    copied = copy_state(state)
    _, success, _ = apply_action(copied, action)
    assert success
    assert _state_signature(state) == before
    assert _state_signature(copied) != before


def test_exact_solver_terminates_and_replays() -> None:
    state = reset_game(MICRO_MAP, MICRO_CONFIG)
    result = ExactSolver().solve(state)
    assert isinstance(result.optimal_score, int)
    assert result.expanded_states > 0
    replay_state, replay_ok, replay_message = replay_actions(
        state,
        result.optimal_actions,
    )
    assert replay_ok, replay_message
    assert replay_state.is_terminal()
    assert final_score(replay_state) == result.optimal_score


def test_existing_agents_run_on_micro_map() -> None:
    agents = [
        RandomAgent(seed=0),
        GreedyDeliveryAgent(seed=0),
        MCTSAgent(iterations=5, rollout_depth_limit=20, seed=0),
        MCTSAgent(
            iterations=5,
            rollout_depth_limit=20,
            evaluation_mode="major_line_aware",
            seed=0,
        ),
    ]
    for agent in agents:
        result = run_episode(
            agent,
            seed=0,
            max_steps=80,
            map_path=MICRO_MAP,
            config_path=MICRO_CONFIG,
        )
        assert result["terminal"] is True
        assert result["invalid_actions"] == 0


def _state_signature(state) -> tuple[Any, ...]:
    city_state = tuple(
        sorted((city_id, tuple(city.goods), city.empty_marker) for city_id, city in state.cities.items())
    )
    edge_state = tuple(
        sorted((edge_id, edge.built, edge.owner) for edge_id, edge in state.edges.items())
    )
    player_state = (
        state.player.money,
        state.player.score,
        state.player.bonds,
        state.player.locomotive_level,
        tuple(sorted(state.player.built_edges)),
        state.player.major_line_bonus,
    )
    return (
        city_state,
        edge_state,
        player_state,
        state.turn,
        state.phase,
        state.actions_remaining,
    )


def run_all() -> None:
    tests = [
        test_micro_map_and_config_load,
        test_copy_apply_does_not_mutate_original,
        test_exact_solver_terminates_and_replays,
        test_existing_agents_run_on_micro_map,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} exact smoke tests passed.")


if __name__ == "__main__":
    run_all()
