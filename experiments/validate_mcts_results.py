from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

DEFAULT_INPUT = Path("results/raw/mcts_experiment_results.csv")
DEFAULT_AGENTS = [
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "mcts_50",
    "mcts_100",
    "mcts_250",
]
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
MCTS_NUMERIC_COLUMNS = {
    "mcts_iterations",
    "mcts_rollout_depth",
    "mcts_exploration_constant",
}


def validate_mcts_results(
    input_path: str | Path,
    expected_episodes: int,
    expected_agents: list[str],
    expected_maps: set[str] | None = None,
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
        maps = expected_maps or {row["map"] for row in rows}
        _validate_map_agents(rows, maps, expected_agents, expected_episodes, errors)
        _validate_numeric_values(rows, errors)
        _validate_group_rates(
            rows,
            max_invalid_action_rate,
            min_terminal_rate,
            errors,
            warnings,
        )
        _compare_mcts_to_greedy(rows, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("MCTS validation failed.")
        return 1

    print("MCTS validation passed.")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _validate_map_agents(
    rows: list[dict[str, str]],
    expected_maps: set[str],
    expected_agents: list[str],
    expected_episodes: int,
    errors: list[str],
) -> None:
    grouped = _group_rows(rows)
    present_maps = {map_name for map_name, _ in grouped}
    missing_maps = expected_maps - present_maps
    if missing_maps:
        errors.append(f"Missing expected maps: {sorted(missing_maps)}")

    for map_name in sorted(expected_maps):
        present_agents = {
            agent for current_map, agent in grouped if current_map == map_name
        }
        missing_agents = set(expected_agents) - present_agents
        if missing_agents:
            errors.append(
                f"Map {map_name} is missing expected agents: {sorted(missing_agents)}"
            )

        for agent in expected_agents:
            count = len(grouped.get((map_name, agent), []))
            if count != expected_episodes:
                errors.append(
                    f"Map {map_name}, agent {agent} has {count} episodes, "
                    f"expected {expected_episodes}."
                )


def _validate_numeric_values(
    rows: list[dict[str, str]],
    errors: list[str],
) -> None:
    for index, row in enumerate(rows, start=1):
        for column in NUMERIC_COLUMNS:
            _validate_float(row[column], column, index, errors)
            if errors and f"Row {index} column {column}" in errors[-1]:
                continue
            value = float(row[column])
            if column in NON_NEGATIVE_COLUMNS and value < 0:
                errors.append(f"Row {index} column {column} is negative: {value}")

        if row["agent"].startswith("mcts_"):
            for column in MCTS_NUMERIC_COLUMNS:
                if row.get(column, "") == "":
                    errors.append(f"Row {index} MCTS column {column} is blank.")
                    continue
                _validate_float(row[column], column, index, errors)

        terminal = row["terminal"].strip().lower()
        if terminal not in {"true", "false", "1", "0", "yes", "no"}:
            errors.append(f"Row {index} terminal value is invalid: {row['terminal']}")


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


def _validate_group_rates(
    rows: list[dict[str, str]],
    max_invalid_action_rate: float,
    min_terminal_rate: float,
    errors: list[str],
    warnings: list[str],
) -> None:
    grouped = _group_rows(rows)
    for (map_name, agent), group_rows in grouped.items():
        total_invalid = sum(float(row["invalid_actions"]) for row in group_rows)
        total_actions = sum(float(row["actions_taken"]) for row in group_rows)
        invalid_rate = total_invalid / total_actions if total_actions else 0.0
        terminal_rate = (
            sum(1 for row in group_rows if _as_bool(row["terminal"])) / len(group_rows)
        )
        mean_runtime = sum(float(row["runtime_seconds"]) for row in group_rows) / len(group_rows)
        min_runtime = min(float(row["runtime_seconds"]) for row in group_rows)

        label = f"{map_name}/{agent}"
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
        if agent.startswith("mcts_") and mean_runtime > 30.0:
            warnings.append(
                f"{label} mean runtime is high ({mean_runtime:.2f}s per episode)."
            )


def _compare_mcts_to_greedy(
    rows: list[dict[str, str]],
    warnings: list[str],
) -> None:
    grouped = _group_rows(rows)
    maps = sorted({map_name for map_name, _ in grouped})

    for map_name in maps:
        means = {
            agent: _mean_final_score(group_rows)
            for (current_map, agent), group_rows in grouped.items()
            if current_map == map_name and group_rows
        }
        greedy_scores = [
            means[agent]
            for agent in ("greedy_delivery", "greedy_expansion")
            if agent in means
        ]
        mcts_scores = [
            score for agent, score in means.items() if agent.startswith("mcts_")
        ]
        if not greedy_scores or not mcts_scores:
            continue
        if max(mcts_scores) < max(greedy_scores):
            warnings.append(
                f"On {map_name}, the best MCTS mean final score "
                f"({max(mcts_scores):.2f}) is below the best greedy baseline "
                f"({max(greedy_scores):.2f})."
            )


def _mean_final_score(rows: list[dict[str, str]]) -> float:
    return sum(float(row["final_score"]) for row in rows) / len(rows)


def _group_rows(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["map"], row["agent"]), []).append(row)
    return grouped


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MCTS experiment outputs.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--agents", default=",".join(DEFAULT_AGENTS))
    parser.add_argument("--maps", default=None)
    parser.add_argument("--max-invalid-action-rate", type=float, default=0.01)
    parser.add_argument("--min-terminal-rate", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    expected_maps = (
        set(_parse_csv_list(args.maps)) if args.maps is not None else None
    )
    exit_code = validate_mcts_results(
        input_path=args.input,
        expected_episodes=args.episodes,
        expected_agents=_parse_csv_list(args.agents),
        expected_maps=expected_maps,
        max_invalid_action_rate=args.max_invalid_action_rate,
        min_terminal_rate=args.min_terminal_rate,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
