from __future__ import annotations

import argparse
import csv
from itertools import product
from pathlib import Path
import sys

DEFAULT_INPUT = Path("results/raw/mcts_tuning_results.csv")
REQUIRED_COLUMNS = {
    "map",
    "config",
    "agent",
    "seed",
    "final_score",
    "raw_score",
    "bonds",
    "money",
    "deliveries",
    "built_edges",
    "major_line_bonus",
    "rail_baron_bonus",
    "operation_card_bonus",
    "empty_markers",
    "turns",
    "actions_taken",
    "invalid_actions",
    "runtime_seconds",
    "terminal",
    "mcts_iterations",
    "mcts_rollout_depth",
    "mcts_exploration_constant",
    "mcts_rollout_policy",
    "mcts_action_generation",
    "mcts_max_candidate_actions",
}
NUMERIC_COLUMNS = {
    "seed",
    "final_score",
    "raw_score",
    "bonds",
    "money",
    "deliveries",
    "built_edges",
    "major_line_bonus",
    "rail_baron_bonus",
    "operation_card_bonus",
    "empty_markers",
    "turns",
    "actions_taken",
    "invalid_actions",
    "runtime_seconds",
    "mcts_iterations",
    "mcts_rollout_depth",
    "mcts_exploration_constant",
    "mcts_max_candidate_actions",
}
NON_NEGATIVE_COLUMNS = NUMERIC_COLUMNS - {"final_score", "raw_score", "money"}


def validate_mcts_tuning(
    input_path: str | Path,
    expected_episodes: int | None = None,
    expected_maps: set[str] | None = None,
    expected_iterations: list[str] | None = None,
    expected_depths: list[str] | None = None,
    expected_policies: list[str] | None = None,
    expected_action_generations: list[str] | None = None,
    expected_candidate_counts: list[str] | None = None,
    max_invalid_action_rate: float = 0.01,
    min_terminal_rate: float = 1.0,
) -> int:
    path = Path(input_path)
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        print(f"ERROR: missing CSV file: {path}")
        return 1

    rows = _read_rows(path)
    if not rows:
        print(f"ERROR: CSV file is empty: {path}")
        return 1

    missing_columns = REQUIRED_COLUMNS - set(rows[0])
    if missing_columns:
        errors.append(f"Missing required columns: {sorted(missing_columns)}")

    if not missing_columns:
        _validate_numeric_values(rows, errors)
        _validate_group_rates(
            rows,
            max_invalid_action_rate,
            min_terminal_rate,
            expected_episodes,
            errors,
            warnings,
        )
        _validate_expected_combinations(
            rows,
            expected_maps,
            expected_iterations,
            expected_depths,
            expected_policies,
            expected_action_generations,
            expected_candidate_counts,
            errors,
        )

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("MCTS tuning validation failed.")
        return 1

    print("MCTS tuning validation passed.")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _validate_numeric_values(
    rows: list[dict[str, str]],
    errors: list[str],
) -> None:
    for index, row in enumerate(rows, start=1):
        for column in REQUIRED_COLUMNS:
            if column.startswith("mcts_") and row.get(column, "") == "":
                errors.append(f"Row {index} has missing MCTS metadata: {column}")

        for column in NUMERIC_COLUMNS:
            try:
                value = float(row[column])
            except ValueError:
                errors.append(f"Row {index} column {column} is not numeric: {row[column]}")
                continue
            if column in NON_NEGATIVE_COLUMNS and value < 0:
                errors.append(f"Row {index} column {column} is negative: {value}")

        terminal = row["terminal"].strip().lower()
        if terminal not in {"true", "false", "1", "0", "yes", "no"}:
            errors.append(f"Row {index} terminal value is invalid: {row['terminal']}")


def _validate_group_rates(
    rows: list[dict[str, str]],
    max_invalid_action_rate: float,
    min_terminal_rate: float,
    expected_episodes: int | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    grouped = _group_rows(rows)
    for group_key, group_rows in grouped.items():
        total_invalid = sum(float(row["invalid_actions"]) for row in group_rows)
        total_actions = sum(float(row["actions_taken"]) for row in group_rows)
        invalid_rate = total_invalid / total_actions if total_actions else 0.0
        terminal_rate = (
            sum(1 for row in group_rows if _as_bool(row["terminal"])) / len(group_rows)
        )
        min_runtime = min(float(row["runtime_seconds"]) for row in group_rows)
        mean_runtime = sum(float(row["runtime_seconds"]) for row in group_rows) / len(group_rows)
        label = "/".join(group_key)

        if expected_episodes is not None and len(group_rows) != expected_episodes:
            errors.append(
                f"{label} has {len(group_rows)} episodes, expected {expected_episodes}."
            )
        if invalid_rate > max_invalid_action_rate:
            errors.append(
                f"{label} invalid action rate {invalid_rate:.4f} exceeds "
                f"{max_invalid_action_rate:.4f}."
            )
        if terminal_rate < min_terminal_rate:
            errors.append(
                f"{label} terminal rate {terminal_rate:.2f} is below "
                f"{min_terminal_rate:.2f}."
            )
        if min_runtime <= 0:
            errors.append(f"{label} has non-positive runtime.")
        if mean_runtime > 60:
            warnings.append(f"{label} mean runtime is high: {mean_runtime:.2f}s.")


def _validate_expected_combinations(
    rows: list[dict[str, str]],
    expected_maps: set[str] | None,
    expected_iterations: list[str] | None,
    expected_depths: list[str] | None,
    expected_policies: list[str] | None,
    expected_action_generations: list[str] | None,
    expected_candidate_counts: list[str] | None,
    errors: list[str],
) -> None:
    observed = set(_group_rows(rows))
    maps = expected_maps or {row["map"] for row in rows}
    iterations = expected_iterations or sorted({row["mcts_iterations"] for row in rows})
    depths = expected_depths or sorted({row["mcts_rollout_depth"] for row in rows})
    policies = expected_policies or sorted({row["mcts_rollout_policy"] for row in rows})
    action_generations = expected_action_generations or sorted(
        {row["mcts_action_generation"] for row in rows}
    )
    candidate_counts = expected_candidate_counts or sorted(
        {row["mcts_max_candidate_actions"] for row in rows}
    )

    expected = set(
        product(
            maps,
            iterations,
            depths,
            policies,
            action_generations,
            candidate_counts,
        )
    )
    missing = expected - observed
    if missing:
        preview = sorted("/".join(combo) for combo in missing)[:10]
        errors.append(f"Missing expected parameter combinations: {preview}")


def _group_rows(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str, str, str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row["map"],
            row["mcts_iterations"],
            row["mcts_rollout_depth"],
            row["mcts_rollout_policy"],
            row["mcts_action_generation"],
            row["mcts_max_candidate_actions"],
        )
        grouped.setdefault(key, []).append(row)
    return grouped


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _parse_csv_list(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MCTS tuning outputs.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument("--maps", default=None)
    parser.add_argument("--iterations-list", default=None)
    parser.add_argument("--rollout-depth-list", default=None)
    parser.add_argument("--rollout-policy-list", default=None)
    parser.add_argument("--action-generation-list", default=None)
    parser.add_argument("--max-candidate-actions-list", default=None)
    parser.add_argument("--max-invalid-action-rate", type=float, default=0.01)
    parser.add_argument("--min-terminal-rate", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exit_code = validate_mcts_tuning(
        input_path=args.input,
        expected_episodes=args.episodes,
        expected_maps=set(_parse_csv_list(args.maps) or []) if args.maps else None,
        expected_iterations=_parse_csv_list(args.iterations_list),
        expected_depths=_parse_csv_list(args.rollout_depth_list),
        expected_policies=_parse_csv_list(args.rollout_policy_list),
        expected_action_generations=_parse_csv_list(args.action_generation_list),
        expected_candidate_counts=_parse_csv_list(args.max_candidate_actions_list),
        max_invalid_action_rate=args.max_invalid_action_rate,
        min_terminal_rate=args.min_terminal_rate,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
