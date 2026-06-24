from __future__ import annotations

from pathlib import Path
import shutil
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "railways_meeting_demo_pack"
PACKAGE_DIR = PROJECT_ROOT / PACKAGE_NAME
ZIP_PATH = PROJECT_ROOT / f"{PACKAGE_NAME}.zip"

ROOT_FILES = ["requirements.txt", "run_app.py", "app.py"]
AGENT_FILES = [
    "__init__.py",
    "base_agent.py",
    "random_agent.py",
    "greedy_delivery_agent.py",
    "greedy_expansion_agent.py",
    "registry.py",
]
EXPERIMENT_FILES = [
    "simulation_runner.py",
    "run_experiments.py",
    "run_full_baseline_pipeline.py",
    "run_greedy.py",
    "analyse_results.py",
    "plot_results.py",
    "validate_baselines.py",
    "smoke_test_rules.py",
    "smoke_test_agents.py",
    "smoke_test_maps.py",
    "smoke_test_cards.py",
    "smoke_test_app_import.py",
    "smoke_test_meeting_demo.py",
]
NOTE_FILES = [
    "MEETING_DEMO_SCOPE.md",
    "RULES_COVERAGE.md",
    "MODEL_VALIDITY.md",
    "CARD_FRAMEWORK.md",
    "SCENARIO_DESIGN.md",
    "BASELINE_RESULTS_SUMMARY.md",
]
OPTIONAL_RESULT_FILES = [
    "raw/experiment_results.csv",
    "raw/map_comparison_results.csv",
    "raw/semi_realistic_baseline_results.csv",
    "processed/summary_by_agent.csv",
    "processed/summary_by_map_agent.csv",
    "processed/semi_realistic_baseline_summary.csv",
    "plots/final_score_by_agent.png",
    "plots/final_score_by_map_agent.png",
    "plots/deliveries_by_map_agent.png",
    "plots/runtime_by_map_agent.png",
]
OPTIONAL_RESULT_DIRS: list[str] = []
EXCLUDE_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}

README_TEXT = """# Railways Dissertation Meeting Demo

This is the focused supervisor-meeting version of the single-player railway
optimisation simulator. It demonstrates the rule engine, graph maps, internal
financing, representative operation cards, scoring, and three interpretable
baseline agents.

## Included Agents

- `random`
- `greedy_delivery`
- `greedy_expansion`

MCTS and the separate card-aware greedy agent are intentionally excluded from
this package. Their exploratory source and historical experiments remain in the
full dissertation repository.

## Install

```bash
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Demo

```bash
python run_app.py
```

The Streamlit page normally opens at `http://localhost:8501`.

## Quick Verification

```bash
python experiments/smoke_test_meeting_demo.py
python experiments/smoke_test_rules.py
python experiments/smoke_test_cards.py
python experiments/smoke_test_app_import.py
```

## Small Baseline Comparison

```bash
python experiments/run_experiments.py --agent all --episodes 10 --map all
```

The operation-card system remains part of the environment. The meeting scope
removes only the separate card-aware agent, not card rules or card scoring.
"""

DEMO_GUIDE = """# Meeting Walkthrough

1. Run `python run_app.py` and open the Streamlit page.
2. Show the scenario selector, map graph, player state, legal manual actions,
   operation cards, and action history.
3. Demonstrate that financing occurs inside paid actions and is not a separate
   player action.
4. Run one action with each baseline agent, then run a complete episode.
5. Compare Random, GreedyDelivery, and GreedyExpansion as three interpretable
   policies sharing the same legal-action interface.

The demo deliberately does not expose MCTS or CardAwareGreedy. This keeps the
meeting claim focused on simulator correctness and explainable baselines while
the full repository preserves the exploratory research history.
"""


def main() -> None:
    _prepare_clean_output()
    _copy_root_files()
    _copy_core_code()
    _copy_selected_files("agents", AGENT_FILES)
    _copy_selected_files("experiments", EXPERIMENT_FILES)
    _copy_selected_files("notes", NOTE_FILES)
    _copy_optional_results()
    _write_package_docs()
    _validate_package_shape()
    _write_zip()
    print(f"Created meeting package folder: {PACKAGE_DIR}")
    print(f"Created meeting zip archive: {ZIP_PATH}")


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


def _copy_core_code() -> None:
    _copy_tree(PROJECT_ROOT / "railways", PACKAGE_DIR / "railways")
    _copy_tree(PROJECT_ROOT / "data", PACKAGE_DIR / "data")


def _copy_selected_files(directory: str, files: list[str]) -> None:
    for relative in files:
        _copy_file(
            PROJECT_ROOT / directory / relative,
            PACKAGE_DIR / directory / relative,
        )


def _copy_optional_results() -> None:
    for relative in OPTIONAL_RESULT_FILES:
        source = PROJECT_ROOT / "results" / relative
        if source.exists():
            _copy_file(source, PACKAGE_DIR / "results" / relative)
    for relative in OPTIONAL_RESULT_DIRS:
        source = PROJECT_ROOT / "results" / relative
        if source.exists():
            _copy_tree(source, PACKAGE_DIR / "results" / relative)


def _write_package_docs() -> None:
    (PACKAGE_DIR / "README.md").write_text(README_TEXT, encoding="utf-8")
    (PACKAGE_DIR / "DEMO_GUIDE.md").write_text(DEMO_GUIDE, encoding="utf-8")


def _write_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in PACKAGE_DIR.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(PROJECT_ROOT))


def _validate_package_shape() -> None:
    required = [
        "README.md",
        "DEMO_GUIDE.md",
        "requirements.txt",
        "run_app.py",
        "app.py",
        "railways",
        "data/cards_basic.json",
        "agents/registry.py",
        "experiments/run_experiments.py",
        "experiments/smoke_test_meeting_demo.py",
        "notes/MEETING_DEMO_SCOPE.md",
    ]
    missing = [item for item in required if not (PACKAGE_DIR / item).exists()]
    if missing:
        raise FileNotFoundError(f"Meeting package is missing: {missing}")

    forbidden = [
        "agents/mcts_agent.py",
        "agents/card_aware_greedy_agent.py",
        "agents/card_heuristics.py",
        "experiments/run_mcts_experiments.py",
        "experiments/run_phase4_card_aware_experiments.py",
    ]
    present = [item for item in forbidden if (PACKAGE_DIR / item).exists()]
    if present:
        raise ValueError(f"Exploratory files leaked into meeting package: {present}")

    for relative in ["app.py", "agents/registry.py", "agents/__init__.py"]:
        text = (PACKAGE_DIR / relative).read_text(encoding="utf-8").lower()
        if "mcts" in text or "cardaware" in text or "card_aware" in text:
            raise ValueError(f"Exploratory agent exposure remains in {relative}")


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
    return {
        name
        for name in names
        if name in EXCLUDE_NAMES or name.endswith(".pyc") or name.endswith(".log")
    }


def _assert_inside_project(path: Path) -> None:
    resolved = path.resolve()
    project = PROJECT_ROOT.resolve()
    if resolved != project and project not in resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {resolved}")


if __name__ == "__main__":
    main()
