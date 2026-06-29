from __future__ import annotations

from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.demo_visualize_replay import generate_replay_frames
from railways.environment import reset_game
from railways.visualization import render_game_state


OFFICIAL_LIKE_MAP = (
    PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
)
OFFICIAL_CONFIG = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)


def assert_non_empty_png(path: Path) -> None:
    assert path.exists()
    assert path.stat().st_size > 0
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_game_state_writes_png() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        state = reset_game(
            map_path=OFFICIAL_LIKE_MAP,
            config_path=OFFICIAL_CONFIG,
        )
        output = render_game_state(state, Path(temp_dir) / "state.png")
        assert_non_empty_png(output)


def test_replay_demo_generates_multiple_frames_and_index() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "replay"
        frames = generate_replay_frames(output_dir)

        assert len(frames) >= 4
        assert all(frame.parent == output_dir for frame in frames)
        for frame in frames:
            assert_non_empty_png(frame)
        index_path = output_dir / "index.html"
        assert index_path.exists()
        assert index_path.stat().st_size > 0


def run_all() -> None:
    tests = [
        test_render_game_state_writes_png,
        test_replay_demo_generates_multiple_frames_and_index,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} visualization smoke tests passed.")


if __name__ == "__main__":
    run_all()
