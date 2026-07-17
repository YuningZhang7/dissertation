from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, reset_game
from railways.rules import check_rail_baron_objective


OFFICIAL_LIKE_MAP = (
    PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
)
EXPANDED_MAP = (
    PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)


def make_state(objective_id: str | None = None):
    return reset_game(
        map_path=OFFICIAL_LIKE_MAP,
        config_path=OFFICIAL_CONFIG,
        rail_baron_objective_id=objective_id,
    )


def build_segments(state, segment_ids: list[str]) -> None:
    _, success, message = apply_action(
        state,
        Action.build_track_segments(segment_ids),
    )
    assert success, message


def claimed_a_f_state():
    state = make_state("RB-A-F")
    build_segments(state, ["A-H-1", "A-H-2"])
    build_segments(state, ["F-H-1", "F-H-2"])
    return state


def test_objective_loads_and_is_active() -> None:
    state = make_state()
    assert state.rail_baron_objectives
    assert state.active_rail_baron_objective_id is not None


def test_default_active_objective_is_deterministic() -> None:
    first = make_state()
    second = make_state()
    assert first.active_rail_baron_objective_id == "RB-A-F"
    assert first.active_rail_baron_objective_id == (
        second.active_rail_baron_objective_id
    )


def test_completed_connection_claims_objective() -> None:
    state = claimed_a_f_state()
    objective = state.rail_baron_objectives["RB-A-F"]

    assert objective.claimed
    assert state.player.rail_baron_bonus == objective.bonus_points
    assert state.player.rail_baron_objectives_completed == 1
    assert state.final_score() == (
        state.player.score
        - state.player.bonds * state.config.bond_final_penalty
        + state.player.major_line_bonus
        + state.player.rail_baron_bonus
        + state.player.operation_card_bonus
    )


def test_bonus_is_awarded_only_once() -> None:
    state = claimed_a_f_state()
    previous_bonus = state.player.rail_baron_bonus

    assert not check_rail_baron_objective(state)
    assert not check_rail_baron_objective(state)
    assert state.player.rail_baron_bonus == previous_bonus
    assert state.player.rail_baron_objectives_completed == 1


def test_unrelated_connection_does_not_claim_objective() -> None:
    state = make_state("RB-A-F")
    build_segments(state, ["B-C-1", "B-C-2", "B-C-3"])

    assert not state.rail_baron_objectives["RB-A-F"].claimed
    assert state.player.rail_baron_bonus == 0
    assert state.player.rail_baron_objectives_completed == 0


def test_expanded_map_objectives_load() -> None:
    state = reset_game(map_path=EXPANDED_MAP, config_path=OFFICIAL_CONFIG)
    assert len(state.rail_baron_objectives) >= 6
    assert state.active_rail_baron_objective_id == "RB-A-N"


def test_copy_and_reset_preserve_independent_objective_state() -> None:
    state = make_state("RB-A-F")
    copied = state.copy()
    copied.rail_baron_objectives["RB-A-F"].claimed = True
    assert not state.rail_baron_objectives["RB-A-F"].claimed

    claimed_state = claimed_a_f_state()
    claimed_state.reset()
    assert not claimed_state.rail_baron_objectives["RB-A-F"].claimed
    assert claimed_state.active_rail_baron_objective_id == "RB-A-F"
    assert claimed_state.player.rail_baron_bonus == 0
    assert claimed_state.player.rail_baron_objectives_completed == 0


def run_all() -> None:
    tests = [
        test_objective_loads_and_is_active,
        test_default_active_objective_is_deterministic,
        test_completed_connection_claims_objective,
        test_bonus_is_awarded_only_once,
        test_unrelated_connection_does_not_claim_objective,
        test_expanded_map_objectives_load,
        test_copy_and_reset_preserve_independent_objective_state,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} Rail Baron objective smoke tests passed.")


if __name__ == "__main__":
    run_all()
