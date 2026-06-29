from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, reset_game
from railways.rules import get_active_rail_baron_objective


OFFICIAL_LIKE_MAP = (
    PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)


def apply_or_raise(state, action: Action) -> str:
    _, success, message = apply_action(state, action)
    if not success:
        raise RuntimeError(message)
    return message


def run_demo() -> None:
    state = reset_game(
        map_path=OFFICIAL_LIKE_MAP,
        config_path=OFFICIAL_CONFIG,
        rail_baron_objective_id="RB-A-F",
    )
    objective = get_active_rail_baron_objective(state)
    if objective is None:
        raise RuntimeError("Expected an active Rail Baron objective.")

    print(
        "Active objective:",
        f"{objective.id} ({objective.source}->{objective.target}, "
        f"bonus={objective.bonus_points})",
    )
    print(
        apply_or_raise(
            state,
            Action.build_track_segments(["A-H-1", "A-H-2"]),
        )
    )
    print(
        apply_or_raise(
            state,
            Action.build_track_segments(["F-H-1", "F-H-2"]),
        )
    )
    print(
        "Result:",
        f"claimed={objective.claimed}",
        f"rail_baron_bonus={state.player.rail_baron_bonus}",
        f"completed={state.player.rail_baron_objectives_completed}",
        f"final_score={state.final_score()}",
    )


if __name__ == "__main__":
    run_demo()
