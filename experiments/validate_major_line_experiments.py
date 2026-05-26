from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_experiments import CSV_COLUMNS
from experiments.run_mcts_experiments import MCTS_COLUMNS
from experiments.run_mcts_major_line_experiments import EVALUATION_COLUMNS

DEFAULT_INPUT = Path("results/raw/mcts_major_line_results.csv")
DEFAULT_AGENTS = [
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "mcts_50_random",
    "mcts_100_random",
    "mcts_50_majorline",
    "mcts_100_majorline",
]
REQUIRED_COLUMNS = set(CSV_COLUMNS + MCTS_COLUMNS + EVALUATION_COLUMNS)
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
MCTS_NUMERIC_COLUMNS = {
    "mcts_iterations",
    "mcts_rollout_depth",
    "mcts_exploration_constant",
    "mcts_max_candidate_actions",
    "mcts_major_line_weight",
    "mcts_delivery_weight",
    "mcts_network_weight",
}


def validate_results(
    input_path: str | Path,
    expected_episodes: int,
    expected_agents: list[str],
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
    else:
        _validate_agents(rows, expected_agents, expected_episodes, errors)
        _validate_numeric_values(rows, errors)
        _validate_rates(
            rows,
            max_invalid_action_rate,
            min_terminal_rate,
            errors,
            warnings,
        )
        _compare_majorline_variant(rows, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("Major-line experiment validation failed.")
        return 1

    print("Major-line experiment validation passed.")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _validate_agents(
    rows: list[dict[str, str]],
    expected_agents: list[str],
    expected_episodes: int,
    errors: list[str],
) -> None:
    grouped = _group_by_agent(rows)
    missing_agents = set(expected_agents) - set(grouped)
    if missing_agents:
        errors.append(f"Missing expected agents: {sorted(missing_agents)}")

    for agent in expected_agents:
        count = len(grouped.get(agent, []))
        if count != expected_episodes:
            errors.append(
                f"Agent {agent} has {count} episodes, expected {expected_episodes}."
            )


def _validate_numeric_values(rows: list[dict[str, str]], errors: list[str]) -> None:
    for index, row in enumerate(rows, start=1):
        for column in NUMERIC_COLUMNS:
            _validate_float(row[column], column, index, errors)

        if row["agent"].startswith("mcts_"):
            for column in MCTS_NUMERIC_COLUMNS:
                if row.get(column, "") == "":
                    errors.append(f"Row {index} MCTS column {column} is blank.")
                    continue
                _validate_float(row[column], column, index, errors)
            if row.get("mcts_evaluation_mode", "") not in {
                "final_score",
                "major_line_aware",
            }:
                errors.append(
                    f"Row {index} has invalid MCTS evaluation mode: "
                    f"{row.get('mcts_evaluation_mode', '')}"
                )

        terminal = row["terminal"].strip().lower()
        if terminal not in {"true", "false", "1", "0", "yes", "no"}:
            errors.append(f"Row {index} terminal value is invalid: {row['terminal']}")


def _validate_rates(
    rows: list[dict[str, str]],
    max_invalid_action_rate: float,
    min_terminal_rate: float,
    errors: list[str],
    warnings: list[str],
) -> None:
    grouped = _group_by_agent(rows)
    for agent, group_rows in grouped.items():
        total_invalid = sum(float(row["invalid_actions"]) for row in group_rows)
        total_actions = sum(float(row["actions_taken"]) for row in group_rows)
        invalid_rate = total_invalid / total_actions if total_actions else 0.0
        terminal_rate = (
            sum(1 for row in group_rows if _as_bool(row["terminal"])) / len(group_rows)
        )
        mean_runtime = sum(float(row["runtime_seconds"]) for row in group_rows) / len(group_rows)
        min_runtime = min(float(row["runtime_seconds"]) for row in group_rows)

        if invalid_rate > max_invalid_action_rate:
            errors.append(
                f"{agent} invalid action rate {invalid_rate:.4f} exceeds "
                f"{max_invalid_action_rate:.4f}."
            )
        if terminal_rate < min_terminal_rate:
            errors.append(
                f"{agent} terminal rate {terminal_rate:.2f} is below "
                f"{min_terminal_rate:.2f}."
            )
        if min_runtime <= 0:
            errors.append(f"{agent} has non-positive runtime.")
        if agent.startswith("mcts_") and mean_runtime > 45.0:
            warnings.append(
                f"{agent} mean runtime is high ({mean_runtime:.2f}s per episode)."
            )


def _compare_majorline_variant(
    rows: list[dict[str, str]],
    warnings: list[str],
) -> None:
    grouped = _group_by_agent(rows)
    for budget in _mcts_budgets(grouped):
        random_agent = f"mcts_{budget}_random"
        majorline_agent = f"mcts_{budget}_majorline"
        if random_agent not in grouped or majorline_agent not in grouped:
            continue
        random_score = _mean_score(grouped[random_agent])
        majorline_score = _mean_score(grouped[majorline_agent])
        if majorline_score < random_score:
            warnings.append(
                f"{majorline_agent} mean final score ({majorline_score:.2f}) "
                f"is below {random_agent} ({random_score:.2f})."
            )


def _mcts_budgets(grouped: dict[str, list[dict[str, str]]]) -> list[str]:
    budgets: set[str] = set()
    for agent in grouped:
        parts = agent.split("_")
        if len(parts) >= 3 and parts[0] == "mcts":
            budgets.add(parts[1])
    return sorted(budgets, key=int)


def _mean_score(rows: list[dict[str, str]]) -> float:
    return sum(float(row["final_score"]) for row in rows) / len(rows)


def _group_by_agent(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["agent"], []).append(row)
    return grouped


def _validate_float(
    value: str,
    column: str,
    row_index: int,
    errors: list[str],
) -> None:
    try:
        float(value)
    except ValueError:
        errors.append(f"Row {row_index} column {column} is not numeric: {value}")


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate major-line-aware MCTS experiment outputs."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--agents", default=",".join(DEFAULT_AGENTS))
    parser.add_argument("--max-invalid-action-rate", type=float, default=0.01)
    parser.add_argument("--min-terminal-rate", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exit_code = validate_results(
        input_path=args.input,
        expected_episodes=args.episodes,
        expected_agents=_parse_csv_list(args.agents),
        max_invalid_action_rate=args.max_invalid_action_rate,
        min_terminal_rate=args.min_terminal_rate,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
