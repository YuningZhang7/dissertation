from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    PROJECT_ROOT / "notes" / "MODEL_VALIDITY.md",
    PROJECT_ROOT / "notes" / "RULE_FIDELITY_ROADMAP.md",
    PROJECT_ROOT / "notes" / "SCENARIO_DESIGN.md",
    PROJECT_ROOT / "data" / "semi_realistic_map.json",
]


def main() -> None:
    print("Project readiness checklist")
    missing = []
    for path in REQUIRED_FILES:
        if path.exists():
            print(f"OK {path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"MISSING {path.relative_to(PROJECT_ROOT)}")
            missing.append(path)

    if missing:
        raise SystemExit(1)

    print("Readiness checklist passed.")


if __name__ == "__main__":
    main()
