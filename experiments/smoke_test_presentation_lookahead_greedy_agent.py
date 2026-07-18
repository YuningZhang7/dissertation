from __future__ import annotations

from pathlib import Path
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.presentation_lookahead_greedy_agent import PresentationLookaheadGreedyAgent
from agents.registry import create_agent, list_agent_names
from railways.environment import apply_action, get_legal_actions, is_terminal, reset_game


MAP_PATH = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def test_agent_is_registered() -> None:
    assert "presentation_lookahead_greedy" in list_agent_names()
    agent = create_agent("presentation_lookahead_greedy", seed=42)
    assert isinstance(agent, PresentationLookaheadGreedyAgent)


def test_agent_returns_legal_initial_action() -> None:
    random.seed(42)
    state = reset_game(MAP_PATH, CONFIG_PATH)
    action = create_agent("presentation_lookahead_greedy", seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_runs_several_steps_without_error() -> None:
    trace = _run_trace(max_steps=10)
    assert len(trace) == 10
    assert all(row["legal"] for row in trace)
    assert all(row["success"] for row in trace)


def test_early_game_urbanize_is_conservative() -> None:
    trace = _run_trace(max_steps=20)
    urbanize_count = sum(row["action_type"] == "urbanize" for row in trace)
    assert urbanize_count <= 1, trace


def test_no_action_returned_outside_legal_action_set() -> None:
    trace = _run_trace(max_steps=35)
    assert all(row["legal"] for row in trace)


def _run_trace(max_steps: int, seed: int = 42) -> list[dict[str, object]]:
    random.seed(seed)
    state = reset_game(MAP_PATH, CONFIG_PATH)
    agent = create_agent("presentation_lookahead_greedy", seed=seed)
    trace: list[dict[str, object]] = []
    for step in range(1, max_steps + 1):
        if is_terminal(state):
            break
        legal_actions = get_legal_actions(state)
        action = agent.choose_action(state)
        legal = action in legal_actions
        _, success, message = apply_action(state, action)
        trace.append(
            {
                "step": step,
                "action_type": action.action_type,
                "legal": legal,
                "success": success,
                "message": message,
            }
        )
    return trace


def run_all() -> None:
    tests = [
        test_agent_is_registered,
        test_agent_returns_legal_initial_action,
        test_agent_runs_several_steps_without_error,
        test_early_game_urbanize_is_conservative,
        test_no_action_returned_outside_legal_action_set,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} presentation lookahead greedy smoke tests passed.")


if __name__ == "__main__":
    run_all()
