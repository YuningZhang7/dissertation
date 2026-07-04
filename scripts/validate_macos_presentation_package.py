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
    for source_path in PACKAGE_ROOT.rglob("*.py"):
        source = source_path.read_text(encoding="utf-8")
        assert not any(name in source for name in FORBIDDEN_AGENT_NAMES), source_path


def validate_imports_and_registry() -> None:
    code = (
        "import json; "
        "from agents.registry import list_agent_names; "
        "from replay import replay_interface; "
        "print(json.dumps(list_agent_names()))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PACKAGE_ROOT,
        env=_clean_subprocess_env(),
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout.strip()) == EXPECTED_AGENTS


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
