from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app
from agents.registry import AGENT_CLASSES, create_agent, list_agent_names
from railways.environment import (
    DEFAULT_CARDS_PATH,
    apply_action,
    get_legal_actions,
    reset_game,
)


EXPECTED_AGENTS = ["random", "greedy_delivery", "greedy_expansion"]


def test_app_imports() -> None:
    assert hasattr(app, "main")
    assert hasattr(app, "create_game_state")


def test_registry_exposes_only_included_agents() -> None:
    assert list(AGENT_CLASSES) == EXPECTED_AGENTS
    assert list_agent_names() == EXPECTED_AGENTS


def test_each_agent_chooses_a_legal_action() -> None:
    state = reset_game(card_path=DEFAULT_CARDS_PATH)
    legal_actions = get_legal_actions(state)
    for seed, name in enumerate(EXPECTED_AGENTS):
        action = create_agent(name, seed=seed).choose_action(state)
        assert action in legal_actions, (name, action)


def test_each_agent_runs_a_short_valid_episode() -> None:
    for seed, name in enumerate(EXPECTED_AGENTS):
        state = reset_game(card_path=DEFAULT_CARDS_PATH)
        agent = create_agent(name, seed=seed)
        invalid_actions = 0

        for _ in range(60):
            if state.is_terminal():
                break
            legal_actions = get_legal_actions(state)
            action = agent.choose_action(state)
            if action not in legal_actions:
                invalid_actions += 1
                break
            _, success, _ = apply_action(state, action)
            if not success:
                invalid_actions += 1
                break

        assert invalid_actions == 0, name


def run_all() -> None:
    tests = [
        test_app_imports,
        test_registry_exposes_only_included_agents,
        test_each_agent_chooses_a_legal_action,
        test_each_agent_runs_a_short_valid_episode,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} supervisor-demo smoke tests passed.")


if __name__ == "__main__":
    run_all()
