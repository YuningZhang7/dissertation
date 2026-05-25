from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics
from typing import Any

DEFAULT_INPUT = Path("results/raw/experiment_results.csv")
DEFAULT_OUTPUT = Path("results/processed/summary_by_agent.csv")
SUMMARY_COLUMNS = [
    "agent",
    "episodes",
    "mean_final_score",
    "std_final_score",
    "min_final_score",
    "max_final_score",
    "mean_raw_score",
    "mean_bonds",
    "mean_deliveries",
    "mean_built_edges",
    "mean_major_line_bonus",
    "mean_runtime_seconds",
]


def analyse_results(input_path: str | Path, output_path: str | Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    rows = _read_rows(input_path)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["agent"], []).append(row)

    summaries = [_summarise_agent(agent, group) for agent, group in grouped.items()]
    summaries.sort(key=lambda row: row["agent"])
    _write_summary(summaries, output_path)
    return summaries


def print_summary(summaries: list[dict[str, Any]]) -> None:
    print("Summary by agent")
    for row in summaries:
        print(
            f"- {row['agent']}: episodes={row['episodes']}, "
            f"mean_final_score={row['mean_final_score']:.2f}, "
            f"std={row['std_final_score']:.2f}, "
            f"deliveries={row['mean_deliveries']:.2f}, "
            f"runtime={row['mean_runtime_seconds']:.4f}s"
        )


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _summarise_agent(agent: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    final_scores = _numbers(rows, "final_score")
    return {
        "agent": agent,
        "episodes": len(rows),
        "mean_final_score": statistics.fmean(final_scores),
        "std_final_score": statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0,
        "min_final_score": min(final_scores),
        "max_final_score": max(final_scores),
        "mean_raw_score": statistics.fmean(_numbers(rows, "raw_score")),
        "mean_bonds": statistics.fmean(_numbers(rows, "bonds")),
        "mean_deliveries": statistics.fmean(_numbers(rows, "deliveries")),
        "mean_built_edges": statistics.fmean(_numbers(rows, "built_edges")),
        "mean_major_line_bonus": statistics.fmean(_numbers(rows, "major_line_bonus")),
        "mean_runtime_seconds": statistics.fmean(_numbers(rows, "runtime_seconds")),
    }


def _numbers(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows]


def _write_summary(summaries: list[dict[str, Any]], output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(summaries)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse baseline experiment results.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = analyse_results(args.input, args.output)
    print_summary(summaries)
    print(f"Wrote summary to {args.output}")


if __name__ == "__main__":
    main()
