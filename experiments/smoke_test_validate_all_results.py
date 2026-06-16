from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.validate_all_results import validate_all_results


def test_validate_all_results_reports_required_sections() -> None:
    messages = validate_all_results()
    joined = "\n".join(messages)
    assert "PASS Exact benchmark results" in joined
    assert "PASS Phase 4C standard results" in joined
    assert "PASS Phase 4C mcts100 results" in joined
    assert "PASS Phase 4D card-aware results" in joined
    assert "All required result artefacts validated." in joined


def run_all() -> None:
    tests = [test_validate_all_results_reports_required_sections]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} validate-all smoke tests passed.")


if __name__ == "__main__":
    run_all()
