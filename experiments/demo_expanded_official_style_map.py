from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, reset_game


EXPANDED_MAP = (
    PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
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
    state = reset_game(map_path=EXPANDED_MAP, config_path=OFFICIAL_CONFIG)
    print(
        "Initial:",
        f"money={state.player.money}",
        f"bonds={state.player.bonds}",
        f"engine={state.player.locomotive_level}",
    )

    print(
        apply_or_raise(
            state,
            Action.build_track_segments(["J-K-1", "J-K-2"]),
        )
    )
    print(apply_or_raise(state, Action.upgrade_engine()))
    print(
        apply_or_raise(
            state,
            Action.deliver_good("J", "K", "blue", path=["J", "K"]),
        )
    )
    print(
        apply_or_raise(
            state,
            Action.build_track_segments(["K-L-1", "K-L-2"]),
        )
    )

    completed_routes = sum(route.completed for route in state.routes.values())
    built_segments = sum(segment.built for segment in state.segments.values())
    claimed_major_lines = [
        line.id for line in state.major_lines.values() if line.claimed
    ]
    print(
        "Final:",
        f"money={state.player.money}",
        f"bonds={state.player.bonds}",
        f"score={state.player.score}",
        f"deliveries={state.player.delivered_goods_count}",
        f"completed_routes={completed_routes}",
        f"built_segments={built_segments}",
    )
    print("Claimed major lines:", claimed_major_lines or "none")


if __name__ == "__main__":
    run_demo()
