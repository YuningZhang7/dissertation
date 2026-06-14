from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app


def test_app_imports() -> None:
    assert hasattr(app, "main")
    assert hasattr(app, "create_game_state")


def test_create_game_state_loads_cards() -> None:
    state = app.create_game_state("toy_map")
    assert state.operation_cards
    assert state.available_operation_cards


def run_all() -> None:
    tests = [
        test_app_imports,
        test_create_game_state_loads_cards,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} app import smoke tests passed.")


if __name__ == "__main__":
    run_all()
