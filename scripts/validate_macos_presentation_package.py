from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "dist" / "railway_replay_presentation"
ZIP_PATH = PROJECT_ROOT / "dist" / "railway_replay_presentation.zip"
EXPECTED_AGENTS = [
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "objective_aware_greedy",
]
FORBIDDEN_NAME_PARTS = (
    "benchmark",
    "smoke_test",
    "route_segment_greedy",
    "adaptive_objective_greedy",
)
FORBIDDEN_AGENT_NAMES = (
    "route_segment_greedy",
    "adaptive_objective_greedy",
)


def _clean_subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=PACKAGE_ROOT, env=env, check=True)


def validate_layout() -> None:
    required = (
        "README.md",
        "requirements.txt",
        "launch_replay_interface.command",
        "generate_static_replay.command",
        "railways/environment.py",
        "agents/registry.py",
        "agents/objective_aware_greedy_agent.py",
        "replay/replay_interface.py",
        "replay/animate_agent_episode.py",
        "data/official_like_route_segment_map.json",
        "data/expanded_official_style_route_segment_map.json",
    )
    for relative_path in required:
        assert (PACKAGE_ROOT / relative_path).is_file(), relative_path

    packaged_files = [
        str(path.relative_to(PACKAGE_ROOT)).replace("\\", "/").lower()
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file()
    ]
    for relative_path in packaged_files:
        assert not any(part in relative_path for part in FORBIDDEN_NAME_PARTS), (
            relative_path
        )
    assert not (PACKAGE_ROOT / "experiments").exists()
    assert not (PACKAGE_ROOT / "exact").exists()
    assert ZIP_PATH.is_file()
    packaged_data = {
        path.name for path in (PACKAGE_ROOT / "data").glob("*.json")
    }
    assert packaged_data == {
        "cards_basic.json",
        "official_single_player_rules_config.json",
        "official_like_route_segment_map.json",
        "expanded_official_style_route_segment_map.json",
    }
    for source_path in PACKAGE_ROOT.rglob("*.py"):
        source = source_path.read_text(encoding="utf-8")
        assert not any(name in source for name in FORBIDDEN_AGENT_NAMES), source_path


def validate_imports_and_registry() -> None:
    code = """
import json
from pathlib import Path
from agents.registry import list_agent_names
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from replay import replay_interface

state = reset_game(
    map_path=Path("data/official_like_route_segment_map.json"),
    config_path=Path("data/official_single_player_rules_config.json"),
)
legal_actions = get_legal_actions(state)
action_types = {action.action_type for action in legal_actions}
assert state.edges == {}
assert "build_track_segments" in action_types
assert "build_track" not in action_types
assert "issue_bond" not in action_types
assert not hasattr(Action, "build_track")
assert not hasattr(Action, "issue_bond")
build_action = next(
    action for action in legal_actions
    if action.action_type == "build_track_segments"
)
starting_actions = state.actions_remaining
_, success, message = apply_action(state, build_action)
assert success, message
assert state.player.bonds > 0
assert state.actions_remaining == starting_actions - 1
assert any("automatically" in entry for entry in state.action_history)
print(json.dumps(list_agent_names()))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PACKAGE_ROOT,
        env=_clean_subprocess_env(),
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout.strip()) == EXPECTED_AGENTS

    actions_source = (PACKAGE_ROOT / "railways" / "actions.py").read_text(
        encoding="utf-8"
    )
    assert "def issue_bond" not in actions_source
    assert "Action.issue_bond" not in actions_source
    assert "def build_track(" not in actions_source
    assert "Action.build_track" not in actions_source

    rules_source = (PACKAGE_ROOT / "railways" / "rules.py").read_text(
        encoding="utf-8"
    )
    assert "def build_track(" not in rules_source
    assert 'action.action_type == "build_track"' not in rules_source
    assert "get_legal_legacy_deliveries" not in rules_source
    assert "check_legacy_major_lines" not in rules_source
    assert "state.edges" not in rules_source


def validate_static_replay() -> None:
    with tempfile.TemporaryDirectory(prefix="railway-replay-validation-") as temp_dir:
        _run(
            [
                sys.executable,
                "replay/animate_agent_episode.py",
                "--map",
                "official_like",
                "--agent",
                "objective_aware_greedy",
                "--seed",
                "42",
                "--max-steps",
                "2",
                "--frame-mode",
                "events",
                "--output-dir",
                temp_dir,
            ],
            env=_clean_subprocess_env(),
        )
        run_dir = Path(temp_dir) / "official_like_objective_aware_greedy_seed42"
        for filename in (
            "index.html",
            "episode_log.txt",
            "episode_summary.json",
            "episode_history.json",
        ):
            assert (run_dir / filename).is_file(), filename


def validate_compilation_and_zip() -> None:
    with tempfile.TemporaryDirectory(prefix="railway-replay-pyc-") as cache_dir:
        env = dict(os.environ)
        env["PYTHONPYCACHEPREFIX"] = cache_dir
        _run(
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "railways",
                "agents",
                "replay",
            ],
            env=env,
        )
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = set(archive.namelist())
        assert (
            "railway_replay_presentation/replay/replay_interface.py" in names
        )
        assert not any(
            part in name.lower()
            for name in names
            for part in FORBIDDEN_NAME_PARTS
        )


def main() -> None:
    validate_layout()
    print("PASS package layout and exclusions")
    validate_imports_and_registry()
    print("PASS packaged imports and agent registry")
    validate_static_replay()
    print("PASS packaged static replay generation")
    validate_compilation_and_zip()
    print("PASS packaged compilation and ZIP archive")


if __name__ == "__main__":
    main()
