from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, reset_game


MAP_PATH = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def apply_or_raise(state, action: Action) -> str:
    _, success, message = apply_action(state, action)
    if not success:
        raise RuntimeError(message)
    return message


def run_demo() -> None:
    state = reset_game(map_path=MAP_PATH, config_path=CONFIG_PATH)
    print(
        "Initial:",
        f"money={state.player.money}",
        f"bonds={state.player.bonds}",
        f"engine={state.player.locomotive_level}",
    )

    print(
        apply_or_raise(
            state,
            Action.build_track_segments(["A-H-1", "A-H-2"]),
        )
    )
    print(apply_or_raise(state, Action.upgrade_engine()))
    print(
        apply_or_raise(
            state,
            Action.deliver_good("A", "H", "blue", path=["A", "H"]),
        )
    )

    claimed_major_lines = [
        line.id for line in state.major_lines.values() if line.claimed
    ]
    print(
        "Final:",
        f"money={state.player.money}",
        f"bonds={state.player.bonds}",
        f"score={state.player.score}",
        f"deliveries={state.player.delivered_goods_count}",
    )
    print("Claimed major lines:", claimed_major_lines or "none")


if __name__ == "__main__":
    run_demo()
