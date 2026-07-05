from __future__ import annotations

from pathlib import Path
import shutil
import stat
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = PROJECT_ROOT / "dist"
PACKAGE_ROOT = DIST_ROOT / "railway_replay_presentation"
ZIP_PATH = DIST_ROOT / "railway_replay_presentation.zip"

RUNTIME_AGENT_FILES = (
    "base_agent.py",
    "random_agent.py",
    "greedy_delivery_agent.py",
    "greedy_expansion_agent.py",
    "objective_aware_greedy_agent.py",
)
RUNTIME_DATA_FILES = (
    "cards_basic.json",
    "official_single_player_rules_config.json",
    "official_like_route_segment_map.json",
    "expanded_official_style_route_segment_map.json",
)

AGENT_INIT = '''"""Agents included in the formal replay presentation package."""

from agents.base_agent import BaseAgent
from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.greedy_expansion_agent import GreedyExpansionAgent
from agents.objective_aware_greedy_agent import ObjectiveAwareGreedyAgent
from agents.random_agent import RandomAgent

__all__ = [
    "BaseAgent",
    "RandomAgent",
    "GreedyDeliveryAgent",
    "GreedyExpansionAgent",
    "ObjectiveAwareGreedyAgent",
]
'''

AGENT_REGISTRY = '''from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.greedy_expansion_agent import GreedyExpansionAgent
from agents.objective_aware_greedy_agent import ObjectiveAwareGreedyAgent
from agents.random_agent import RandomAgent


AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    "random": RandomAgent,
    "greedy_delivery": GreedyDeliveryAgent,
    "greedy_expansion": GreedyExpansionAgent,
    "objective_aware_greedy": ObjectiveAwareGreedyAgent,
}


def create_agent(name: str, seed: int | None = None) -> BaseAgent:
    if name not in AGENT_CLASSES:
        raise ValueError(f"Unknown agent: {name}")
    return AGENT_CLASSES[name](seed=seed)


def list_agent_names() -> list[str]:
    return list(AGENT_CLASSES)
'''

REQUIREMENTS = """streamlit>=1.35
networkx>=3.2
matplotlib>=3.8
Pillow>=10.0
"""

PACKAGE_GITIGNORE = """.DS_Store
.venv/
__pycache__/
*.py[cod]
outputs/
"""

README = """# Railway Agent Replay Interface

This package is a focused macOS-ready presentation build of the single-player
railway simulator. It includes the simulator source, selected interpretable agents,
the recommended `objective_aware_greedy` agent, two route-segment maps, a Streamlit
replay interface, and a static HTML replay generator.

The simulator is an official-compatible single-player abstraction. It focuses on
route-segment construction, route completion, completed-route delivery, Major Line
scoring, Rail Baron objectives, bonds, and final-score calculation. It does not
claim to reproduce every official multiplayer rule.

This presentation runtime is route-segment-only. Construction uses
`build_track_segments`, deliveries require completed routes, and Major Line and
Rail Baron connectivity is evaluated on the completed-route network.

Bonds are not selectable actions. Financing certificates are issued automatically
only when a payment shortfall occurs, and they continue to affect interest and the
final score.

## Quick start on macOS

1. Copy or unzip this directory onto the Mac.
2. In Finder, Control-click `launch_replay_interface.command` and choose **Open**.
3. macOS may ask for permission the first time. The launcher creates a local
   `.venv`, installs the listed Python dependencies, and opens Streamlit.

Python 3.10 or newer is recommended. From Terminal, the equivalent command is:

```bash
chmod +x launch_replay_interface.command generate_static_replay.command
./launch_replay_interface.command
```

The interface defaults to:

- map: `official_like`
- agent: `objective_aware_greedy`
- frame mode: `events`
- seed: `42`
- maximum steps: `60`

The Agent dropdown directly provides the four presentation agents: `random`,
`greedy_delivery`, `greedy_expansion`, and `objective_aware_greedy`.

## Static replay backup

Double-click `generate_static_replay.command`, or run:

```bash
./generate_static_replay.command
```

The command generates PNG frames, `index.html`, `episode_log.txt`,
`episode_summary.json`, and `episode_history.json` under
`outputs/agent_animations/`. Open the generated `index.html` in any browser.

For custom settings:

```bash
.venv/bin/python replay/animate_agent_episode.py \
  --map expanded_official_style \
  --agent objective_aware_greedy \
  --seed 42 \
  --max-steps 60 \
  --frame-mode events
```

## Included source

- `railways/`: simulator rules, state, scoring, loaders, and rendering
- `agents/`: selected presentation agents and their registry
- `replay/`: Streamlit interface and static replay generator
- `data/`: the two presentation maps, cards, and single-player configuration

Development benchmarks, experiment tables, smoke tests, generated research
outputs, exact-solver utilities, and non-presentation agent variants are not part
of this package. They remain available in the full research repository.
"""

LAUNCH_INTERFACE = """#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python -m streamlit run replay/replay_interface.py
"""

GENERATE_STATIC_REPLAY = """#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

.venv/bin/python replay/animate_agent_episode.py \\
  --map official_like \\
  --agent objective_aware_greedy \\
  --seed 42 \\
  --max-steps 60 \\
  --frame-mode events

echo
echo "Replay generated under outputs/agent_animations/."
"""


def _reset_package_directory() -> None:
    package = PACKAGE_ROOT.resolve()
    expected_parent = DIST_ROOT.resolve()
    if package.parent != expected_parent or package.name != "railway_replay_presentation":
        raise RuntimeError(f"Refusing to replace unexpected directory: {package}")
    if package.exists():
        try:
            shutil.rmtree(package)
        except PermissionError:
            if any(package.iterdir()):
                raise
            # Windows may keep an empty working directory locked briefly after
            # the presentation launcher exits. Reusing that verified empty
            # directory is safe and keeps the build deterministic.
    package.mkdir(parents=True, exist_ok=True)


def _copy_runtime_source() -> None:
    shutil.copytree(
        PROJECT_ROOT / "railways",
        PACKAGE_ROOT / "railways",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    agents_dir = PACKAGE_ROOT / "agents"
    agents_dir.mkdir()
    for filename in RUNTIME_AGENT_FILES:
        shutil.copy2(PROJECT_ROOT / "agents" / filename, agents_dir / filename)
    (agents_dir / "__init__.py").write_text(AGENT_INIT, encoding="utf-8")
    (agents_dir / "registry.py").write_text(AGENT_REGISTRY, encoding="utf-8")

    replay_dir = PACKAGE_ROOT / "replay"
    replay_dir.mkdir()
    (replay_dir / "__init__.py").write_text(
        '"""Automated agent replay interface and static generator."""\n',
        encoding="utf-8",
    )

    animation_source = (
        PROJECT_ROOT / "experiments" / "animate_agent_episode.py"
    ).read_text(encoding="utf-8")
    animation_source = animation_source.replace(
        'agent_name: str = "route_segment_greedy"',
        'agent_name: str = "objective_aware_greedy"',
    ).replace(
        'default="route_segment_greedy",',
        'default="objective_aware_greedy",',
    ).replace(
        'PROJECT_ROOT / "experiments" / "outputs" / "agent_animations"',
        'PROJECT_ROOT / "outputs" / "agent_animations"',
    )
    (replay_dir / "animate_agent_episode.py").write_text(
        animation_source,
        encoding="utf-8",
    )

    interface_source = (
        PROJECT_ROOT / "experiments" / "demo_agent_animation_app.py"
    ).read_text(encoding="utf-8")
    interface_source = interface_source.replace(
        "from experiments.animate_agent_episode import (",
        "from replay.animate_agent_episode import (",
    )
    (replay_dir / "replay_interface.py").write_text(
        interface_source,
        encoding="utf-8",
    )

    data_dir = PACKAGE_ROOT / "data"
    data_dir.mkdir()
    for filename in RUNTIME_DATA_FILES:
        shutil.copy2(PROJECT_ROOT / "data" / filename, data_dir / filename)


def _write_package_files() -> None:
    files = {
        "README.md": README,
        "requirements.txt": REQUIREMENTS,
        ".gitignore": PACKAGE_GITIGNORE,
        "launch_replay_interface.command": LAUNCH_INTERFACE,
        "generate_static_replay.command": GENERATE_STATIC_REPLAY,
    }
    for relative_path, content in files.items():
        path = PACKAGE_ROOT / relative_path
        path.write_text(content, encoding="utf-8", newline="\n")
    for name in ("launch_replay_interface.command", "generate_static_replay.command"):
        path = PACKAGE_ROOT / name
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    manifest = [
        str(path.relative_to(PACKAGE_ROOT)).replace("\\", "/")
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file()
    ]
    manifest.append("PACKAGE_CONTENTS.txt")
    (PACKAGE_ROOT / "PACKAGE_CONTENTS.txt").write_text(
        "\n".join(sorted(manifest)) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    executable_names = {
        "launch_replay_interface.command",
        "generate_static_replay.command",
    }
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(DIST_ROOT)
            info = zipfile.ZipInfo.from_file(path, arcname=str(relative).replace("\\", "/"))
            if path.name in executable_names:
                info.external_attr = (stat.S_IFREG | 0o755) << 16
            with path.open("rb") as source:
                archive.writestr(info, source.read(), compress_type=zipfile.ZIP_DEFLATED)


def main() -> None:
    _reset_package_directory()
    _copy_runtime_source()
    _write_package_files()
    _write_zip()
    print(f"Presentation package: {PACKAGE_ROOT}")
    print(f"ZIP archive: {ZIP_PATH}")


if __name__ == "__main__":
    main()
