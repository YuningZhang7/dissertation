from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, reset_game
from railways.rules import check_major_lines, uses_route_segment_delivery


ROUTE_MAP = PROJECT_ROOT / "data" / "mini_route_segment_map.json"
OFFICIAL_CONFIG = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
LEGACY_MAP = PROJECT_ROOT / "data" / "toy_map.json"
LEGACY_CONFIG = PROJECT_ROOT / "data" / "rules_config.json"


def make_segment_state():
    return reset_game(map_path=ROUTE_MAP, config_path=OFFICIAL_CONFIG)


def build_segments(state, segment_ids: list[str]) -> None:
    _, success, message = apply_action(
        state,
        Action.build_track_segments(segment_ids),
    )
    assert success, message


def complete_a_b(state) -> None:
    build_segments(state, ["A-B-1", "A-B-2"])


def complete_b_c(state) -> None:
    build_segments(state, ["B-C-1", "B-C-2", "B-C-3"])


def test_single_completed_route_does_not_claim_multi_route_line() -> None:
    state = make_segment_state()

    complete_a_b(state)

    assert not state.major_lines["A-C"].claimed
    assert state.player.major_line_bonus == 0


def test_completed_multi_route_path_claims_major_line() -> None:
    state = make_segment_state()

    complete_a_b(state)
    complete_b_c(state)

    assert state.major_lines["A-C"].claimed
    assert state.player.major_line_bonus == 5
    assert any("claimed major line A-C" in entry for entry in state.action_history)


def test_completed_route_major_line_is_awarded_once() -> None:
    state = make_segment_state()
    complete_a_b(state)
    complete_b_c(state)
    bonus_after_claim = state.player.major_line_bonus
    claim_entries_after_claim = sum(
        "claimed major line A-C" in entry for entry in state.action_history
    )

    check_major_lines(state)
    _, success, message = apply_action(state, Action.pass_action())

    assert success, message
    assert state.player.major_line_bonus == bonus_after_claim
    assert state.major_lines["A-C"].claimed
    assert claim_entries_after_claim == 1
    assert (
        sum("claimed major line A-C" in entry for entry in state.action_history)
        == 1
    )


def test_incomplete_segments_do_not_claim_and_are_cleaned() -> None:
    state = make_segment_state()
    complete_a_b(state)
    build_segments(state, ["B-C-1"])

    assert not state.major_lines["A-C"].claimed
    assert state.player.major_line_bonus == 0

    _, success, message = apply_action(state, Action.pass_action())

    assert success, message
    assert not state.segments["B-C-1"].built
    assert not state.major_lines["A-C"].claimed
    assert state.player.major_line_bonus == 0


def test_legacy_major_line_claiming_is_unchanged() -> None:
    state = reset_game(map_path=LEGACY_MAP, config_path=LEGACY_CONFIG)
    assert not uses_route_segment_delivery(state)

    for edge_id in ["A-B", "B-C", "C-H"]:
        _, success, message = apply_action(state, Action.build_track(edge_id))
        assert success, message

    assert state.major_lines["A-H"].claimed
    assert state.player.major_line_bonus == 3
    assert any("claimed major line A-H" in entry for entry in state.action_history)

    check_major_lines(state)
    assert state.player.major_line_bonus == 3


def run_all() -> None:
    tests = [
        test_single_completed_route_does_not_claim_multi_route_line,
        test_completed_multi_route_path_claims_major_line,
        test_completed_route_major_line_is_awarded_once,
        test_incomplete_segments_do_not_claim_and_are_cleaned,
        test_legacy_major_line_claiming_is_unchanged,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} route major-line smoke tests passed.")


if __name__ == "__main__":
    run_all()
