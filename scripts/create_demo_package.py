from __future__ import annotations

from pathlib import Path
import shutil
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "railways_dissertation_demo_pack"
PACKAGE_DIR = PROJECT_ROOT / PACKAGE_NAME
ZIP_PATH = PROJECT_ROOT / f"{PACKAGE_NAME}.zip"

ROOT_FILES = [
    "README.md",
    "requirements.txt",
    "run_app.py",
    "app.py",
]
ROOT_DIRS = [
    "railways",
    "agents",
    "exact",
    "data",
    "experiments",
    "notes",
]
RESULT_DIRS = [
    "exact_benchmark",
    "figures",
    "raw",
    "summary",
    "tables",
]
EXCLUDE_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}


DEMO_GUIDE = """# Full Dissertation Demo Guide

This package is the full research archive and includes exploratory MCTS and
card-aware work. For the focused supervisor meeting package, run
`python scripts/create_meeting_demo_package.py` from the source repository.

## What This Project Is

This is a dissertation-ready experimental prototype for a single-player railway
optimisation abstraction inspired by Railways of the World.

It is not a full official implementation of the commercial board game. The
project focuses on a controlled rule-based simulator and AI/OR experiments:
graph-based maps, legal action generation, goods delivery, engine range
constraints, financing penalties, major-line objectives, and representative
operation cards.

## Install on Mac

From inside this demo package:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Streamlit Demo

Preferred command:

```bash
python run_app.py
```

Streamlit command:

```bash
streamlit run run_app.py
```

If that fails, run the app entry point directly:

```bash
streamlit run app.py
```

## Run Evidence Checks

```bash
python experiments/validate_all_results.py
python experiments/generate_dissertation_figures.py
python experiments/export_dissertation_tables.py
```

## Good Files to Open During the Supervisor Walkthrough

Core simulator:

- railways/models.py
- railways/game_state.py
- railways/rules.py
- railways/environment.py

Main baseline agents:

- agents/random_agent.py
- agents/greedy_delivery_agent.py
- agents/greedy_expansion_agent.py

Exploratory agents retained in this full archive:

- agents/card_aware_greedy_agent.py
- agents/mcts_agent.py

Data and configuration:

- data/rules_config.json
- data/cards_basic.json

Dissertation evidence:

- notes/PROJECT_STATUS_FINAL.md
- notes/DISSERTATION_RESULTS_OUTLINE.md
- notes/EXPERIMENT_MANIFEST.md
- results/figures/
- results/tables/

## Short Supervisor Explanation

The simulator represents the game as a graph-based sequential optimisation
problem. The meeting narrative focuses on the random, greedy-delivery, and
greedy-expansion baselines. MCTS and card-aware variants are preserved here as
exploratory research history. The project is designed for controlled AI/OR
experiments rather than full commercial board game reproduction.
"""


def main() -> None:
    _prepare_clean_output()
    _copy_root_files()
    _copy_code_and_notes()
    _copy_results()
    _write_demo_guide()
    _write_zip()
    _validate_package_shape()
    print(f"Created package folder: {PACKAGE_DIR}")
    print(f"Created zip archive: {ZIP_PATH}")


def _prepare_clean_output() -> None:
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


def _copy_code_and_notes() -> None:
    for relative in ROOT_DIRS:
        _copy_tree(PROJECT_ROOT / relative, PACKAGE_DIR / relative)


def _copy_results() -> None:
    results_target = PACKAGE_DIR / "results"
    results_target.mkdir()
    for relative in RESULT_DIRS:
        source = PROJECT_ROOT / "results" / relative
        if source.exists():
            _copy_tree(source, results_target / relative)


def _write_demo_guide() -> None:
    (PACKAGE_DIR / "DEMO_GUIDE.md").write_text(DEMO_GUIDE, encoding="utf-8")


def _write_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in PACKAGE_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(PROJECT_ROOT))


def _validate_package_shape() -> None:
    required_paths = [
        "README.md",
        "requirements.txt",
        "run_app.py",
        "app.py",
        "DEMO_GUIDE.md",
        "railways",
        "agents",
        "exact",
        "data",
        "experiments",
        "results",
        "results/figures",
        "results/tables",
        "notes",
    ]
    missing = [path for path in required_paths if not (PACKAGE_DIR / path).exists()]
    if missing:
        raise FileNotFoundError(f"Demo package is missing: {missing}")


def _copy_file(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Required file does not exist: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Required directory does not exist: {source}")
    shutil.copytree(source, target, ignore=_ignore_names)


def _ignore_names(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in EXCLUDE_NAMES or name.endswith(".pyc") or name.endswith(".log"):
            ignored.add(name)
    return ignored


def _assert_inside_project(path: Path) -> None:
    resolved = path.resolve()
    project = PROJECT_ROOT.resolve()
    if resolved != project and project not in resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {resolved}")


if __name__ == "__main__":
    main()
