from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics
from typing import Any

DEFAULT_INPUT = Path("results/raw/major_line_sensitivity_results.csv")
DEFAULT_OUTPUT = Path("results/processed/major_line_sensitivity_summary.csv")
SUMMARY_COLUMNS = [
    "major_line_multiplier",
    "agent",
    "episodes",
    "mean_final_score",
    "std_final_score",
    "mean_raw_score",
    "mean_deliveries",
    "mean_built_edges",
    "mean_major_line_bonus",
    "mean_bonds",
    "mean_runtime_seconds",
    "invalid_action_rate",
    "terminal_rate",
]


def analyse_sensitivity(
    input_path: str | Path,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> list[dict[str, Any]]:
    rows = _read_rows(input_path)
    grouped: dict[tuple[float, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(
            (float(row["major_line_multiplier"]), row["agent"]),
            [],
        ).append(row)

    summaries = [
        _summarise_group(multiplier, agent, group)
        for (multiplier, agent), group in grouped.items()
    ]
    summaries.sort(key=lambda row: (row["major_line_multiplier"], row["agent"]))
    _write_summary(summaries, output_path)
    return summaries


def print_summary(summaries: list[dict[str, Any]]) -> None:
    print("Major-line sensitivity summary")
    for row in summaries:
        print(
            f"- multiplier={row['major_line_multiplier']:g}/{row['agent']}: "
            f"episodes={row['episodes']}, "
            f"mean_final_score={row['mean_final_score']:.2f}, "
            f"major_line_bonus={row['mean_major_line_bonus']:.2f}, "
            f"terminal_rate={row['terminal_rate']:.2f}"
        )


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _summarise_group(
    multiplier: float,
    agent: str,
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    final_scores = _numbers(rows, "final_score")
    total_invalid_actions = sum(_numbers(rows, "invalid_actions"))
    total_actions_taken = sum(_numbers(rows, "actions_taken"))
    terminal_count = sum(1 for row in rows if _as_bool(row["terminal"]))

    return {
        "major_line_multiplier": multiplier,
        "agent": agent,
        "episodes": len(rows),
        "mean_final_score": statistics.fmean(final_scores),
        "std_final_score": statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0,
        "mean_raw_score": statistics.fmean(_numbers(rows, "raw_score")),
        "mean_deliveries": statistics.fmean(_numbers(rows, "deliveries")),
        "mean_built_edges": statistics.fmean(_numbers(rows, "built_edges")),
        "mean_major_line_bonus": statistics.fmean(_numbers(rows, "major_line_bonus")),
        "mean_bonds": statistics.fmean(_numbers(rows, "bonds")),
        "mean_runtime_seconds": statistics.fmean(_numbers(rows, "runtime_seconds")),
        "invalid_action_rate": (
            total_invalid_actions / total_actions_taken if total_actions_taken else 0.0
        ),
        "terminal_rate": terminal_count / len(rows) if rows else 0.0,
    }


def _numbers(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _write_summary(summaries: list[dict[str, Any]], output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(summaries)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyse major-line sensitivity experiment results."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = analyse_sensitivity(args.input, args.output)
    print_summary(summaries)
    print(f"Wrote summary to {args.output}")


if __name__ == "__main__":
    main()
