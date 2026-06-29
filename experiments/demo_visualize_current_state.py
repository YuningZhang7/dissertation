from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.environment import reset_game
from railways.visualization import render_game_state


OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)
MAPS = {
    "official_like": (
        PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
    ),
    "expanded_official_style": (
        PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
    ),
}
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "outputs" / "current_state"


def render_current_states(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> list[Path]:
    output = Path(output_dir)
    rendered: list[Path] = []
    for map_name, map_path in MAPS.items():
        state = reset_game(map_path=map_path, config_path=OFFICIAL_CONFIG)
        rendered.append(
            render_game_state(state, output / f"{map_name}.png")
        )
    return rendered


def main() -> None:
    for path in render_current_states():
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
