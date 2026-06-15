from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_phase4_card_experiments import (
    DEFAULT_AGENTS,
    DEFAULT_MAPS,
    DEFAULT_PROFILE,
    EXPERIMENT_PROFILES,
    Phase4OutputPaths,
    get_profile_output_paths,
)


RAW_REQUIRED_COLUMNS = {
    "map",
    "agent",
    "cards_enabled",
    "final_score",
    "invalid_actions",
    "cards_selected",
    "cards_completed",
    "operation_card_bonus",
    "end_game_card_bonus",
}
SUMMARY_REQUIRED_COLUMNS = {
    "map",
    "cards_enabled",
    "agent",
    "episodes",
    "mean_final_score",
    "mean_invalid_actions",
    "mean_cards_selected",
    "mean_cards_completed",
}


def validate_phase4_card_results(
    profile: str = DEFAULT_PROFILE,
    paths: Phase4OutputPaths | None = None,
    required_maps: set[str] | None = None,
    required_agents: set[str] | None = None,
) -> list[str]:
    selected_paths = paths or get_profile_output_paths(profile)
    expected_maps = required_maps or {path.stem for path in DEFAULT_MAPS}
    expected_agents = required_agents or set(DEFAULT_AGENTS)

    for path in _all_paths(selected_paths):
        if not path.exists():
            raise FileNotFoundError(f"Missing Phase 4 result file: {path}")

    disabled_rows = _read_csv(selected_paths.disabled_raw)
    enabled_rows = _read_csv(selected_paths.enabled_raw)
    summary_rows = _read_csv(selected_paths.summary_csv)
    effect_rows = _read_csv(selected_paths.effect_csv)
    usage_rows = _read_csv(selected_paths.usage_csv)

    _require_rows(disabled_rows, "card-disabled raw CSV")
    _require_rows(enabled_rows, "card-enabled raw CSV")
    _require_columns(disabled_rows, RAW_REQUIRED_COLUMNS, "card-disabled raw CSV")
    _require_columns(enabled_rows, RAW_REQUIRED_COLUMNS, "card-enabled raw CSV")
    _require_columns(summary_rows, SUMMARY_REQUIRED_COLUMNS, "summary CSV")

    if any(_as_bool(row["cards_enabled"]) for row in disabled_rows):
        raise ValueError("Card-disabled raw CSV contains cards_enabled=True rows.")
    if any(not _as_bool(row["cards_enabled"]) for row in enabled_rows):
        raise ValueError("Card-enabled raw CSV contains cards_enabled=False rows.")

    combined_rows = disabled_rows + enabled_rows
    actual_maps = {row["map"] for row in combined_rows}
    actual_agents = {row["agent"] for row in combined_rows}
    missing_maps = expected_maps - actual_maps
    missing_agents = expected_agents - actual_agents
    if missing_maps:
        raise ValueError(f"Missing required maps: {sorted(missing_maps)}")
    if missing_agents:
        raise ValueError(f"Missing required agents: {sorted(missing_agents)}")

    expected_pairs = {
        (map_name, agent)
        for map_name in expected_maps
        for agent in expected_agents
    }
    disabled_pairs = {(row["map"], row["agent"]) for row in disabled_rows}
    enabled_pairs = {(row["map"], row["agent"]) for row in enabled_rows}
    if expected_pairs - disabled_pairs:
        raise ValueError("Card-disabled results do not cover every map/agent pair.")
    if expected_pairs - enabled_pairs:
        raise ValueError("Card-enabled results do not cover every map/agent pair.")

    summary_modes = {_as_bool(row["cards_enabled"]) for row in summary_rows}
    if summary_modes != {False, True}:
        raise ValueError("Summary CSV must include both card modes.")
    if len(effect_rows) != len(expected_pairs):
        raise ValueError("Card effect table does not cover every map/agent pair.")
    if len(usage_rows) != len(expected_pairs):
        raise ValueError("Card usage table does not cover every map/agent pair.")

    messages = [
        f"Validated Phase 4 profile '{profile}'.",
        f"Card-disabled rows: {len(disabled_rows)}",
        f"Card-enabled rows: {len(enabled_rows)}",
        f"Summary groups: {len(summary_rows)}",
    ]
    invalid_total = sum(float(row["invalid_actions"]) for row in combined_rows)
    if invalid_total == 0:
        messages.append("Invalid actions: 0")
    else:
        messages.append(
            f"WARNING: invalid actions total {invalid_total:.0f}; inspect raw results."
        )
    return messages


def _all_paths(paths: Phase4OutputPaths) -> list[Path]:
    return [
        paths.disabled_raw,
        paths.enabled_raw,
        paths.summary_csv,
        paths.summary_md,
        paths.effect_csv,
        paths.effect_md,
        paths.usage_csv,
        paths.usage_md,
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _require_rows(rows: list[dict[str, str]], label: str) -> None:
    if not rows:
        raise ValueError(f"{label} contains no data rows.")


def _require_columns(
    rows: list[dict[str, str]], required: set[str], label: str
) -> None:
    _require_rows(rows, label)
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"{label} is missing columns: {sorted(missing)}")


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _custom_paths(args: argparse.Namespace) -> Phase4OutputPaths:
    defaults = get_profile_output_paths(args.profile)
    return Phase4OutputPaths(
        disabled_raw=Path(args.disabled_output or defaults.disabled_raw),
        enabled_raw=Path(args.enabled_output or defaults.enabled_raw),
        summary_csv=Path(args.summary_csv or defaults.summary_csv),
        summary_md=Path(args.summary_md or defaults.summary_md),
        effect_csv=Path(args.effect_csv or defaults.effect_csv),
        effect_md=Path(args.effect_md or defaults.effect_md),
        usage_csv=Path(args.usage_csv or defaults.usage_csv),
        usage_md=Path(args.usage_md or defaults.usage_md),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Phase 4 card results.")
    parser.add_argument(
        "--profile",
        choices=sorted(EXPERIMENT_PROFILES),
        default=DEFAULT_PROFILE,
    )
    parser.add_argument("--disabled-output")
    parser.add_argument("--enabled-output")
    parser.add_argument("--summary-csv")
    parser.add_argument("--summary-md")
    parser.add_argument("--effect-csv")
    parser.add_argument("--effect-md")
    parser.add_argument("--usage-csv")
    parser.add_argument("--usage-md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    messages = validate_phase4_card_results(
        profile=args.profile,
        paths=_custom_paths(args),
    )
    for message in messages:
        print(message)


if __name__ == "__main__":
    main()
