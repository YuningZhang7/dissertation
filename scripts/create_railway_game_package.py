from __future__ import annotations

import ast
from pathlib import Path
import shutil
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "railway_game"
PACKAGE_DIR = PROJECT_ROOT / PACKAGE_NAME
ZIP_PATH = PROJECT_ROOT / f"{PACKAGE_NAME}.zip"

INCLUDED_AGENTS = ["random", "greedy_delivery", "greedy_expansion"]
ROOT_FILES = ["run_app.py", "requirements.txt"]
AGENT_FILES = [
    "__init__.py",
    "base_agent.py",
    "random_agent.py",
    "greedy_delivery_agent.py",
    "greedy_expansion_agent.py",
    "registry.py",
]
EXCLUDED_COPY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}

README_RUN = """# Railway Game

This package contains the Streamlit simulator and three simple agents:

- `random`
- `greedy_delivery`
- `greedy_expansion`

## Create a Virtual Environment

macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

## Install Dependencies

```bash
python -m pip install -r requirements.txt
```

On macOS, use `python3` instead of `python` if required.

## Run the App

```bash
python run_app.py
```

Streamlit normally opens `http://localhost:8501`.

## Run the Smoke Test

```bash
python experiments/smoke_test_railway_game.py
```
"""

SMOKE_TEST = '''from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app
from agents.registry import AGENT_CLASSES, create_agent, list_agent_names
from railways.environment import (
    DEFAULT_CARDS_PATH,
    apply_action,
    get_legal_actions,
    reset_game,
)


EXPECTED_AGENTS = ["random", "greedy_delivery", "greedy_expansion"]


def test_app_imports() -> None:
    assert hasattr(app, "main")
    assert hasattr(app, "create_game_state")


def test_registry_exposes_only_included_agents() -> None:
    assert list(AGENT_CLASSES) == EXPECTED_AGENTS
    assert list_agent_names() == EXPECTED_AGENTS


def test_each_agent_chooses_a_legal_action() -> None:
    state = reset_game(card_path=DEFAULT_CARDS_PATH)
    legal_actions = get_legal_actions(state)
    for seed, name in enumerate(EXPECTED_AGENTS):
        action = create_agent(name, seed=seed).choose_action(state)
        assert action in legal_actions, (name, action)


def test_each_agent_runs_a_short_valid_episode() -> None:
    for seed, name in enumerate(EXPECTED_AGENTS):
        state = reset_game(card_path=DEFAULT_CARDS_PATH)
        agent = create_agent(name, seed=seed)
        invalid_actions = 0

        for _ in range(60):
            if state.is_terminal():
                break
            legal_actions = get_legal_actions(state)
            action = agent.choose_action(state)
            if action not in legal_actions:
                invalid_actions += 1
                break
            _, success, _ = apply_action(state, action)
            if not success:
                invalid_actions += 1
                break

        assert invalid_actions == 0, name


def run_all() -> None:
    tests = [
        test_app_imports,
        test_registry_exposes_only_included_agents,
        test_each_agent_chooses_a_legal_action,
        test_each_agent_runs_a_short_valid_episode,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} railway-game smoke tests passed.")


if __name__ == "__main__":
    run_all()
'''


def main() -> None:
    demo_files = _read_existing_demo_files()
    _prepare_output()
    _copy_root_files()
    _copy_core_packages()
    _copy_agent_files()
    _write_demo_files(demo_files)
    _validate_package()
    _create_zip()
    _print_summary()


def _read_existing_demo_files() -> dict[str, str]:
    """Preserve the simplified meeting UI when regenerating the package."""
    paths = {
        "app.py": PACKAGE_DIR / "app.py",
        "README_RUN.md": PACKAGE_DIR / "README_RUN.md",
        "experiments/smoke_test_railway_game.py": (
            PACKAGE_DIR / "experiments" / "smoke_test_railway_game.py"
        ),
    }
    missing = [relative for relative, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Cannot regenerate railway_game because the existing package "
            f"is missing template files: {missing}"
        )
    return {
        relative: path.read_text(encoding="utf-8")
        for relative, path in paths.items()
    }


def _prepare_output() -> None:
    _assert_inside_project(PACKAGE_DIR)
    _assert_inside_project(ZIP_PATH)
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    PACKAGE_DIR.mkdir()


def _copy_root_files() -> None:
    for relative in ROOT_FILES:
        _copy_file(PROJECT_ROOT / relative, PACKAGE_DIR / relative)


def _copy_core_packages() -> None:
    _copy_tree(PROJECT_ROOT / "railways", PACKAGE_DIR / "railways")
    _copy_tree(PROJECT_ROOT / "data", PACKAGE_DIR / "data")


def _copy_agent_files() -> None:
    for filename in AGENT_FILES:
        _copy_file(
            PROJECT_ROOT / "agents" / filename,
            PACKAGE_DIR / "agents" / filename,
        )


def _write_demo_files(demo_files: dict[str, str]) -> None:
    (PACKAGE_DIR / "app.py").write_text(demo_files["app.py"], encoding="utf-8")
    (PACKAGE_DIR / "README_RUN.md").write_text(
        demo_files.get("README_RUN.md", README_RUN),
        encoding="utf-8",
    )
    smoke_path = PACKAGE_DIR / "experiments" / "smoke_test_railway_game.py"
    smoke_path.parent.mkdir(parents=True, exist_ok=True)
    smoke_path.write_text(
        demo_files.get("experiments/smoke_test_railway_game.py", SMOKE_TEST),
        encoding="utf-8",
    )


def _validate_package() -> None:
    required = [
        "README_RUN.md",
        "requirements.txt",
        "run_app.py",
        "app.py",
        "railways",
        "data",
        "agents/registry.py",
        "experiments/smoke_test_railway_game.py",
    ]
    missing = [relative for relative in required if not (PACKAGE_DIR / relative).exists()]
    if missing:
        raise FileNotFoundError(f"Railway game package is missing: {missing}")

    if (PACKAGE_DIR / "README.md").exists():
        raise ValueError("The main repository README must not be copied.")
    for excluded_directory in ["results", "notes"]:
        if (PACKAGE_DIR / excluded_directory).exists():
            raise ValueError(f"Excluded directory was copied: {excluded_directory}")

    forbidden_names = []
    for path in PACKAGE_DIR.rglob("*"):
        lowered = path.name.lower()
        if "mcts" in lowered or "card_aware" in lowered:
            forbidden_names.append(str(path.relative_to(PACKAGE_DIR)))
    if forbidden_names:
        raise ValueError(f"Forbidden files were copied: {forbidden_names}")

    copied_agent_files = sorted(
        path.name for path in (PACKAGE_DIR / "agents").iterdir() if path.is_file()
    )
    if copied_agent_files != sorted(AGENT_FILES):
        raise ValueError(f"Unexpected agent files: {copied_agent_files}")

    _validate_registry()
    for relative in ["app.py", "agents/registry.py", "agents/__init__.py"]:
        contents = (PACKAGE_DIR / relative).read_text(encoding="utf-8").lower()
        if "mcts" in contents or "cardaware" in contents or "card_aware" in contents:
            raise ValueError(f"Excluded agent exposure remains in {relative}")


def _validate_registry() -> None:
    registry_path = PACKAGE_DIR / "agents" / "registry.py"
    tree = ast.parse(registry_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "AGENT_CLASSES" and isinstance(node.value, ast.Dict):
                keys = [
                    key.value
                    for key in node.value.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                ]
                if keys != INCLUDED_AGENTS:
                    raise ValueError(f"Unexpected registry agents: {keys}")
                return
    raise ValueError("Could not validate AGENT_CLASSES in copied registry.")


def _create_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in PACKAGE_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(PROJECT_ROOT))


def _print_summary() -> None:
    print(f"Created folder: {PACKAGE_DIR}")
    print(f"Created zip: {ZIP_PATH}")
    print(f"Included agents: {', '.join(INCLUDED_AGENTS)}")
    print("Run: python run_app.py")
    print("Test: python experiments/smoke_test_railway_game.py")


def _copy_file(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Required source file does not exist: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Required source directory does not exist: {source}")
    shutil.copytree(source, target, ignore=_ignore_copy_names)


def _ignore_copy_names(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in EXCLUDED_COPY_NAMES or name.endswith(".pyc") or name.endswith(".log")
    }


def _assert_inside_project(path: Path) -> None:
    resolved = path.resolve()
    project = PROJECT_ROOT.resolve()
    if resolved != project and project not in resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {resolved}")


if __name__ == "__main__":
    main()
