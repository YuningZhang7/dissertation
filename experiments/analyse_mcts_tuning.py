from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics
from typing import Any

DEFAULT_INPUT = Path("results/raw/mcts_tuning_results.csv")
DEFAULT_OUTPUT = Path("results/processed/mcts_tuning_summary.csv")
GROUP_COLUMNS = [
    "map",
    "mcts_iterations",
    "mcts_rollout_depth",
    "mcts_rollout_policy",
    "mcts_action_generation",
    "mcts_max_candidate_actions",
]
SUMMARY_COLUMNS = [
    *GROUP_COLUMNS,
    "episodes",
    "mean_final_score",
    "std_final_score",
    "mean_deliveries",
    "mean_built_edges",
    "mean_major_line_bonus",
    "mean_runtime_seconds",
    "invalid_action_rate",
    "terminal_rate",
    "score_per_second",
]


def analyse_mcts_tuning(
    input_path: str | Path,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> list[dict[str, Any]]:
    rows = _read_rows(input_path)
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row[column] for column in GROUP_COLUMNS), []).append(row)

    summaries = [
        _summarise_group(group_key, group_rows)
        for group_key, group_rows in grouped.items()
    ]
    summaries.sort(
        key=lambda row: (
            row["map"],
            int(row["mcts_iterations"]),
            int(row["mcts_rollout_depth"]),
            row["mcts_rollout_policy"],
            row["mcts_action_generation"],
            int(row["mcts_max_candidate_actions"]),
        )
    )
    _write_summary(summaries, output_path)
    return summaries


def print_summary(summaries: list[dict[str, Any]]) -> None:
    print("MCTS tuning summary")
    for row in summaries:
        print(
            f"- {row['map']} i{row['mcts_iterations']} "
            f"d{row['mcts_rollout_depth']} "
            f"{row['mcts_rollout_policy']} "
            f"{row['mcts_action_generation']} "
            f"c{row['mcts_max_candidate_actions']}: "
            f"episodes={row['episodes']}, "
            f"mean_final_score={row['mean_final_score']:.2f}, "
            f"runtime={row['mean_runtime_seconds']:.2f}s, "
            f"score_per_second={row['score_per_second']:.3f}"
        )


def _summarise_group(
    group_key: tuple[str, ...],
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    final_scores = _numbers(rows, "final_score")
    runtimes = _numbers(rows, "runtime_seconds")
    total_invalid = sum(_numbers(rows, "invalid_actions"))
    total_actions = sum(_numbers(rows, "actions_taken"))
    terminal_count = sum(1 for row in rows if _as_bool(row["terminal"]))
    mean_runtime = statistics.fmean(runtimes)
    mean_score = statistics.fmean(final_scores)

    return {
        **dict(zip(GROUP_COLUMNS, group_key)),
        "episodes": len(rows),
        "mean_final_score": mean_score,
        "std_final_score": statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0,
        "mean_deliveries": statistics.fmean(_numbers(rows, "deliveries")),
        "mean_built_edges": statistics.fmean(_numbers(rows, "built_edges")),
        "mean_major_line_bonus": statistics.fmean(_numbers(rows, "major_line_bonus")),
        "mean_runtime_seconds": mean_runtime,
        "invalid_action_rate": total_invalid / total_actions if total_actions else 0.0,
        "terminal_rate": terminal_count / len(rows) if rows else 0.0,
        "score_per_second": mean_score / mean_runtime if mean_runtime else 0.0,
    }


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _numbers(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _write_summary(
    summaries: list[dict[str, Any]],
    output_path: str | Path,
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(summaries)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse MCTS tuning results.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = analyse_mcts_tuning(args.input, args.output)
    print_summary(summaries)
    print(f"Wrote summary to {args.output}")


if __name__ == "__main__":
    main()
