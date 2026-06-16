from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.generate_dissertation_figures import (
    FIGURE_PATHS,
    generate_dissertation_figures,
)


def test_dissertation_figures_generate_and_are_non_empty() -> None:
    paths = generate_dissertation_figures()
    expected = {path.name for path in FIGURE_PATHS.values()}
    actual = {path.name for path in paths}
    assert expected == actual
    for path in paths:
        assert path.exists(), path
        assert path.stat().st_size > 0, path


def run_all() -> None:
    tests = [test_dissertation_figures_generate_and_are_non_empty]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} dissertation-figure smoke tests passed.")


if __name__ == "__main__":
    run_all()
