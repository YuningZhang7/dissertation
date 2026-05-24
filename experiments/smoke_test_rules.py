from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.environment import reset_game
from railways.rules import (
    build_track,
    deliver_good,
    issue_bond,
    run_income_phase,
    upgrade_engine,
)


def test_build_affordable_edge() -> None:
    state = reset_game()
    ok, _ = build_track(state, "A-B")
    assert ok
    assert state.edges["A-B"].built
    assert state.edges["A-B"].owner == "player"
    assert state.player.money == 17


def test_build_unaffordable_edge_fails_without_auto_bonds() -> None:
    state = reset_game()
    state.player.money = 0
    ok, _ = build_track(state, "C-H")
    assert not ok
    assert not state.edges["C-H"].built
    assert state.player.bonds == 0


def test_delivery_without_built_path_fails() -> None:
    state = reset_game()
    ok, _ = deliver_good(state, "B", "A", "red")
    assert not ok
    assert state.player.score == 0


def test_delivery_with_built_path_succeeds() -> None:
    state = reset_game()
    assert build_track(state, "A-B")[0]
    ok, _ = deliver_good(state, "B", "A", "red")
    assert ok
    assert state.player.score == 1
    assert state.player.delivered_goods_count == 1


def test_delivery_fails_when_path_exceeds_engine_level() -> None:
    state = reset_game()
    assert build_track(state, "C-F")[0]
    assert build_track(state, "E-F")[0]
    assert build_track(state, "D-E")[0]
    ok, _ = deliver_good(state, "C", "D", "green")
    assert not ok
    assert state.player.locomotive_level == 1


def test_upgrade_engine_costs_money_and_increases_level() -> None:
    state = reset_game()
    ok, _ = upgrade_engine(state)
    assert ok
    assert state.player.locomotive_level == 2
    assert state.player.money == 15


def test_bonds_increase_money_and_count() -> None:
    state = reset_game()
    ok, _ = issue_bond(state)
    assert ok
    assert state.player.money == 25
    assert state.player.bonds == 1


def test_income_phase_adds_income_and_subtracts_interest() -> None:
    state = reset_game()
    state.player.score = 5
    state.player.bonds = 1
    state.player.money = 0
    run_income_phase(state)
    assert state.player.money == 4


def test_final_score_subtracts_bond_penalty() -> None:
    state = reset_game()
    state.player.score = 10
    state.player.bonds = 2
    assert state.final_score() == 8


def test_empty_city_marker_added_when_last_good_removed() -> None:
    state = reset_game()
    assert build_track(state, "A-B")[0]
    ok, _ = deliver_good(state, "A", "B", "blue")
    assert ok
    assert state.cities["A"].empty_marker


def run_all() -> None:
    tests = [
        test_build_affordable_edge,
        test_build_unaffordable_edge_fails_without_auto_bonds,
        test_delivery_without_built_path_fails,
        test_delivery_with_built_path_succeeds,
        test_delivery_fails_when_path_exceeds_engine_level,
        test_upgrade_engine_costs_money_and_increases_level,
        test_bonds_increase_money_and_count,
        test_income_phase_adds_income_and_subtracts_interest,
        test_final_score_subtracts_bond_penalty,
        test_empty_city_marker_added_when_last_good_removed,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} smoke tests passed.")


if __name__ == "__main__":
    run_all()
