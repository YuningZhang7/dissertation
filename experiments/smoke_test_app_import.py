from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app
from agents.registry import list_agent_names
from streamlit.testing.v1 import AppTest


def test_app_imports() -> None:
    assert hasattr(app, "main")
    assert hasattr(app, "create_game_state")


def test_create_game_state_loads_cards() -> None:
    state = app.create_game_state("official_like")
    assert state.operation_cards
    assert state.available_operation_cards
    assert state.routes
    assert state.segments
    assert state.edges == {}


def test_app_exposes_registered_agents() -> None:
    assert list_agent_names() == [
        "random",
        "greedy_delivery",
        "greedy_expansion",
        "objective_aware_greedy",
        "lookahead_greedy",
    ]


def test_app_renders_registered_agent_options() -> None:
    rendered = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run(timeout=20)
    assert not rendered.exception
    agent_selectors = [item for item in rendered.selectbox if item.label == "Agent"]
    assert len(agent_selectors) == 1
    assert list(agent_selectors[0].options) == [
        "random",
        "greedy_delivery",
        "greedy_expansion",
        "objective_aware_greedy",
        "lookahead_greedy",
    ]


def run_all() -> None:
    tests = [
        test_app_imports,
        test_create_game_state_loads_cards,
        test_app_exposes_registered_agents,
        test_app_renders_registered_agent_options,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} app import smoke tests passed.")


if __name__ == "__main__":
    run_all()
