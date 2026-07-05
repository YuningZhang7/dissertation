from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.rules import pay_money


LEGACY_MAP = PROJECT_ROOT / "data" / "toy_map.json"


def test_default_runtime_loads_route_segments() -> None:
    state = reset_game()
    assert state.routes
    assert state.segments
    assert state.edges == {}


def test_legacy_edge_map_is_rejected() -> None:
    try:
        reset_game(map_path=LEGACY_MAP)
    except ValueError as exc:
        assert "Route-segment runtime requires" in str(exc)
    else:
        raise AssertionError("Legacy edge-only map should be rejected.")


def test_legal_actions_expose_only_segment_construction() -> None:
    state = reset_game()
    state.config = replace(state.config, allow_voluntary_bonds=True)
    action_types = {action.action_type for action in get_legal_actions(state)}

    assert "build_track_segments" in action_types
    assert "build_track" not in action_types
    assert "issue_bond" not in action_types


def test_unknown_legacy_actions_are_rejected() -> None:
    state = reset_game()
    starting = (state.player.money, state.player.bonds, state.actions_remaining)

    for action_type in ("build_track", "issue_bond"):
        _, success, message = apply_action(state, Action(action_type))
        assert not success
        assert "Unknown action type" in message

    assert (state.player.money, state.player.bonds, state.actions_remaining) == starting


def test_auto_financing_builds_segment_without_separate_action() -> None:
    state = reset_game()
    state.player.money = 0
    action = next(
        action
        for action in get_legal_actions(state)
        if action.action_type == "build_track_segments"
    )
    starting_actions = state.actions_remaining

    _, success, message = apply_action(state, action)

    assert success, message
    assert state.player.bonds > 0
    assert state.actions_remaining == starting_actions - 1
    assert any("automatically" in item for item in state.action_history)


def test_pay_money_does_not_auto_finance_when_disabled() -> None:
    state = reset_game()
    state.player.money = 0

    ok, message = pay_money(state, 7, allow_auto_bonds=False)

    assert not ok
    assert "Need $7" in message
    assert state.player.money == 0
    assert state.player.bonds == 0


def test_partial_route_cannot_deliver() -> None:
    state = reset_game()
    _, success, message = apply_action(
        state,
        Action.build_track_segments(["A-H-1"]),
    )
    assert success, message
    state.player.locomotive_level = 2

    _, success, message = apply_action(
        state,
        Action.deliver_good("A", "H", "blue", path=["A", "H"]),
    )

    assert not success
    assert "completed route" in message


def test_final_score_subtracts_bond_penalty() -> None:
    state = reset_game()
    state.player.score = 10
    state.player.bonds = 3
    assert state.final_score() == 7


def run_all() -> None:
    tests = [
        test_default_runtime_loads_route_segments,
        test_legacy_edge_map_is_rejected,
        test_legal_actions_expose_only_segment_construction,
        test_unknown_legacy_actions_are_rejected,
        test_auto_financing_builds_segment_without_separate_action,
        test_pay_money_does_not_auto_finance_when_disabled,
        test_partial_route_cannot_deliver,
        test_final_score_subtracts_bond_penalty,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} route-segment runtime smoke tests passed.")


if __name__ == "__main__":
    run_all()
