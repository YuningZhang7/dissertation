from __future__ import annotations

from html import escape
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from railways.actions import Action
from railways.environment import apply_action, reset_game
from railways.visualization import render_game_state


OFFICIAL_LIKE_MAP = (
    PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiments" / "outputs" / "replay_frames"


def apply_or_raise(state, action: Action) -> None:
    _, success, message = apply_action(state, action)
    if not success:
        raise RuntimeError(message)


def generate_replay_frames(output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    state = reset_game(
        map_path=OFFICIAL_LIKE_MAP,
        config_path=OFFICIAL_CONFIG,
        rail_baron_objective_id="RB-A-F",
    )

    frames: list[Path] = []

    def capture(filename: str) -> None:
        frames.append(render_game_state(state, output / filename))

    capture("frame_00_initial.png")
    apply_or_raise(
        state,
        Action.build_track_segments(["A-H-1", "A-H-2"]),
    )
    capture("frame_01_build_AH.png")
    apply_or_raise(
        state,
        Action.build_track_segments(["F-H-1", "F-H-2"]),
    )
    capture("frame_02_build_FH_claim_rail_baron.png")
    apply_or_raise(state, Action.upgrade_engine())
    capture("frame_03_upgrade_engine.png")
    apply_or_raise(
        state,
        Action.deliver_good("A", "H", "blue", path=["A", "H"]),
    )
    capture("frame_04_delivery_AH.png")

    _write_html_index(output, frames)
    return frames


def _write_html_index(output_dir: Path, frames: list[Path]) -> Path:
    items = "\n".join(
        (
            "<figure>"
            f'<img src="{escape(frame.name)}" alt="{escape(frame.stem)}">'
            f"<figcaption>{escape(frame.stem)}</figcaption>"
            "</figure>"
        )
        for frame in frames
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Railways replay frames</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; background: #f7f8fa; }}
    figure {{ margin: 0 0 2rem; }}
    img {{ max-width: 100%; border: 1px solid #bbb; background: white; }}
    figcaption {{ margin-top: 0.4rem; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Railways replay frames</h1>
  {items}
</body>
</html>
"""
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


def main() -> None:
    frames = generate_replay_frames()
    print(f"Generated {len(frames)} replay frames in {DEFAULT_OUTPUT_DIR}")
    for frame in frames:
        print(f"- {frame}")
    print(f"- {DEFAULT_OUTPUT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
