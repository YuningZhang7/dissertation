from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.animate_agent_episode import run_agent_episode_animation


class FailingAgent:
    def choose_action(self, state):
        raise RuntimeError("intentional smoke-test failure")


def test_tiny_agent_animation_writes_required_artifacts() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir, returned_summary = run_agent_episode_animation(
            map_name="official_like",
            agent_name="objective_aware_greedy",
            seed=42,
            max_steps=5,
            output_root=temp_dir,
        )

        frames_dir = run_dir / "frames"
        frame_paths = sorted(frames_dir.glob("frame_*.png"))
        summary_path = run_dir / "episode_summary.json"
        history_path = run_dir / "episode_history.json"
        index_path = run_dir / "index.html"

        assert run_dir.exists()
        assert frames_dir.exists()
        assert len(frame_paths) >= 2
        assert index_path.exists()
        assert (run_dir / "episode_log.txt").exists()
        assert summary_path.exists()
        assert history_path.exists()

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        required_summary_fields = {
            "map_name",
            "map_path",
            "agent_name",
            "seed",
            "max_steps",
            "frame_mode",
            "steps_executed",
            "terminal",
            "final_score",
            "money",
            "bonds",
            "locomotive_level",
            "delivered_goods_count",
            "major_line_bonus",
            "rail_baron_bonus",
            "rail_baron_objectives_completed",
            "claimed_major_lines_count",
            "completed_routes_count",
            "built_segments_count",
            "completed_segments_count",
            "fallback_actions",
            "success",
            "error",
            "frames_count",
        }
        assert summary == returned_summary
        assert required_summary_fields.issubset(summary)
        assert summary["agent_name"] == "objective_aware_greedy"
        assert summary["frames_count"] == len(frame_paths)
        assert all(frame.stat().st_size > 0 for frame in frame_paths)
        assert all(
            frame.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
            for frame in frame_paths
        )
        log_text = (run_dir / "episode_log.txt").read_text(encoding="utf-8")
        assert "chosen=" in log_text
        assert "completed_routes=" in log_text
        html = index_path.read_text(encoding="utf-8")
        assert "Action History" in html
        assert "Play" in html
        assert "Pause" in html
        assert "frameData" in html
        assert "viewerImage" in html
        assert html.count("<figure") == 0


def test_events_frame_mode_writes_sparse_frames_and_full_history() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir, summary = run_agent_episode_animation(
            map_name="official_like",
            agent_name="objective_aware_greedy",
            seed=42,
            max_steps=10,
            frame_mode="events",
            output_root=temp_dir,
        )

        frame_paths = sorted((run_dir / "frames").glob("frame_*.png"))
        history = json.loads(
            (run_dir / "episode_history.json").read_text(encoding="utf-8")
        )
        assert summary["frame_mode"] == "events"
        assert summary["frames_count"] >= 2
        assert summary["frames_count"] <= summary["steps_executed"] + 1
        assert summary["frames_count"] == len(frame_paths)
        assert len(history) >= summary["steps_executed"]
        assert all("event_labels" in entry for entry in history)
        assert all("frame_index" in entry for entry in history)


def test_agent_exception_still_writes_failure_summary() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "experiments.animate_agent_episode.create_agent",
            return_value=FailingAgent(),
        ):
            run_dir, summary = run_agent_episode_animation(
                map_name="official_like",
                agent_name="objective_aware_greedy",
                seed=42,
                max_steps=5,
                output_root=temp_dir,
            )

        saved_summary = json.loads(
            (run_dir / "episode_summary.json").read_text(encoding="utf-8")
        )
        assert not summary["success"]
        assert summary["steps_executed"] == 0
        assert summary["frames_count"] == 1
        assert "intentional smoke-test failure" in summary["error"]
        assert saved_summary == summary
        assert (run_dir / "episode_log.txt").exists()
        assert (run_dir / "index.html").exists()
        assert (run_dir / "episode_history.json").exists()


def run_all() -> None:
    tests = [
        test_tiny_agent_animation_writes_required_artifacts,
        test_events_frame_mode_writes_sparse_frames_and_full_history,
        test_agent_exception_still_writes_failure_summary,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} agent animation smoke tests passed.")


if __name__ == "__main__":
    run_all()
