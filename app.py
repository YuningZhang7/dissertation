from __future__ import annotations

from pathlib import Path

from experiments.agent_replay_app import main
from railways.environment import DEFAULT_CARDS_PATH, reset_game
from railways.game_state import GameState


BASE_DIR = Path(__file__).resolve().parent
MAP_OPTIONS = {
    "official_like": BASE_DIR / "data" / "official_like_route_segment_map.json",
    "expanded_official_style": (
        BASE_DIR / "data" / "expanded_official_style_route_segment_map.json"
    ),
}


def create_game_state(map_name: str = "official_like") -> GameState:
    """Create a route-segment state for compatibility with the root entry point."""
    if map_name not in MAP_OPTIONS:
        raise ValueError(
            f"Unknown route-segment map {map_name!r}. "
            f"Available maps: {', '.join(MAP_OPTIONS)}"
        )
    return reset_game(
        map_path=MAP_OPTIONS[map_name],
        card_path=DEFAULT_CARDS_PATH,
    )


if __name__ == "__main__":
    main()
