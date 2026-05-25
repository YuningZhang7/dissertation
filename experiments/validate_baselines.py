from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

EXPECTED_AGENTS = {"random", "greedy_delivery", "greedy_expansion"}
REQUIRED_COLUMNS = {
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
}
NON_NEGATIVE_COLUMNS = {
    "bonds",
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
}


def validate_baselines(
    input_path: str | Path,
    expected_episodes: int,
    max_invalid_action_rate: float = 0.01,
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
        _validate_agents(rows, expected_episodes, errors)
        _validate_numeric_values(rows, errors)
        _validate_rates(rows, max_invalid_action_rate, errors, warnings)
        _compare_agent_means(rows, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("Baseline validation failed.")
        return 1

    print("Baseline validation passed.")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _validate_agents(
    rows: list[dict[str, str]],
    expected_episodes: int,
    errors: list[str],
) -> None:
    grouped = _group_rows(rows)
    missing_agents = EXPECTED_AGENTS - set(grouped)
    if missing_agents:
        errors.append(f"Missing expected agents: {sorted(missing_agents)}")

    for agent in EXPECTED_AGENTS:
        count = len(grouped.get(agent, []))
        if count != expected_episodes:
            errors.append(
                f"Agent {agent} has {count} episodes, expected {expected_episodes}."
            )


def _validate_numeric_values(rows: list[dict[str, str]], errors: list[str]) -> None:
    for index, row in enumerate(rows, start=1):
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


def _validate_rates(
    rows: list[dict[str, str]],
    max_invalid_action_rate: float,
    errors: list[str],
    warnings: list[str],
) -> None:
    grouped = _group_rows(rows)
    for agent, agent_rows in grouped.items():
        total_invalid = sum(float(row["invalid_actions"]) for row in agent_rows)
        total_actions = sum(float(row["actions_taken"]) for row in agent_rows)
        invalid_rate = total_invalid / total_actions if total_actions else 0.0
        terminal_rate = (
            sum(1 for row in agent_rows if _as_bool(row["terminal"])) / len(agent_rows)
        )
        max_runtime = max(float(row["runtime_seconds"]) for row in agent_rows)
        min_runtime = min(float(row["runtime_seconds"]) for row in agent_rows)

        if invalid_rate > max_invalid_action_rate:
            errors.append(
                f"{agent} invalid action rate {invalid_rate:.4f} exceeds "
                f"{max_invalid_action_rate:.4f}."
            )
        if terminal_rate < 0.95:
            errors.append(f"{agent} terminal rate {terminal_rate:.2f} is below 0.95.")
        elif terminal_rate < 1.0:
            warnings.append(f"{agent} terminal rate is {terminal_rate:.2f}, not 1.00.")
        if min_runtime <= 0:
            errors.append(f"{agent} has non-positive runtime.")
        if max_runtime > 5.0:
            warnings.append(f"{agent} has a high episode runtime: {max_runtime:.2f}s.")


def _compare_agent_means(
    rows: list[dict[str, str]],
    warnings: list[str],
) -> None:
    grouped = _group_rows(rows)
    means = {
        agent: sum(float(row["final_score"]) for row in agent_rows) / len(agent_rows)
        for agent, agent_rows in grouped.items()
        if agent_rows
    }
    random_mean = means.get("random")
    greedy_delivery_mean = means.get("greedy_delivery")
    greedy_expansion_mean = means.get("greedy_expansion")

    if random_mean is None:
        return
    if greedy_delivery_mean is not None and greedy_delivery_mean < random_mean:
        warnings.append(
            "GreedyDeliveryAgent does not outperform RandomAgent on mean final score."
        )
    if greedy_expansion_mean is not None and greedy_expansion_mean < random_mean:
        warnings.append(
            "GreedyExpansionAgent does not outperform RandomAgent on mean final score."
        )


def _group_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["agent"], []).append(row)
    return grouped


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate baseline experiment outputs.")
    parser.add_argument("--input", default="results/raw/experiment_results.csv")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--max-invalid-action-rate", type=float, default=0.01)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exit_code = validate_baselines(
        input_path=args.input,
        expected_episodes=args.episodes,
        max_invalid_action_rate=args.max_invalid_action_rate,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
