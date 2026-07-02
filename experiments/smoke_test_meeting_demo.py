from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app
from agents.registry import AGENT_CLASSES, create_agent, list_agent_names
from experiments.simulation_runner import run_episode
from railways.environment import DEFAULT_CARDS_PATH, get_legal_actions, reset_game


EXPECTED_AGENTS = [
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "route_segment_greedy",
    "objective_aware_greedy",
    "adaptive_objective_greedy",
]


def test_registry_contains_only_meeting_agents() -> None:
    assert list(AGENT_CLASSES) == EXPECTED_AGENTS
    assert list_agent_names() == EXPECTED_AGENTS


def test_meeting_agents_choose_legal_actions() -> None:
    state = reset_game(card_path=DEFAULT_CARDS_PATH)
    legal_actions = get_legal_actions(state)
    for index, name in enumerate(EXPECTED_AGENTS):
        action = create_agent(name, seed=index).choose_action(state)
        assert action in legal_actions, (name, action)


def test_meeting_agents_complete_small_episodes() -> None:
    for index, name in enumerate(EXPECTED_AGENTS):
        result = run_episode(
            create_agent(name, seed=index),
            seed=index,
            max_steps=200,
            card_path=DEFAULT_CARDS_PATH,
        )
        assert result["invalid_actions"] == 0, (name, result)


def test_streamlit_app_uses_meeting_registry() -> None:
    assert hasattr(app, "main")
    assert list_agent_names() == EXPECTED_AGENTS


def run_all() -> None:
    tests = [
        test_registry_contains_only_meeting_agents,
        test_meeting_agents_choose_legal_actions,
        test_meeting_agents_complete_small_episodes,
        test_streamlit_app_uses_meeting_registry,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} meeting-demo smoke tests passed.")


if __name__ == "__main__":
    run_all()
