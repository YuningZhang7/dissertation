from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics
from typing import Any


SUMMARY_COLUMNS = [
    "map",
    "cards_enabled",
    "agent",
    "episodes",
    "mean_final_score",
    "std_final_score",
    "min_final_score",
    "max_final_score",
    "mean_raw_score",
    "mean_major_line_bonus",
    "mean_operation_card_bonus",
    "mean_end_game_card_bonus",
    "mean_financing_penalty",
    "mean_cards_selected",
    "mean_cards_completed",
    "mean_invalid_actions",
    "mean_runtime_seconds",
]


def summarise_phase4_results(
    input_paths: list[str | Path],
    output_csv: str | Path,
    output_md: str | Path,
) -> list[dict[str, Any]]:
    rows = _read_rows(input_paths)
    grouped: dict[tuple[str, bool, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row.get("map", "unknown_map"),
            _as_bool(row.get("cards_enabled", "false")),
            row["agent"],
        )
        grouped.setdefault(key, []).append(row)

    summaries = [
        _summarise_group(map_name, cards_enabled, agent, group)
        for (map_name, cards_enabled, agent), group in grouped.items()
    ]
    summaries.sort(
        key=lambda row: (row["map"], row["cards_enabled"], row["agent"])
    )
    _write_csv(summaries, output_csv)
    _write_markdown(summaries, output_md)
    return summaries


def _read_rows(input_paths: list[str | Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for input_path in input_paths:
        with Path(input_path).open("r", newline="", encoding="utf-8") as file:
            rows.extend(csv.DictReader(file))
    return rows


def _summarise_group(
    map_name: str,
    cards_enabled: bool,
    agent: str,
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    final_scores = _numbers(rows, "final_score")
    return {
        "map": map_name,
        "cards_enabled": cards_enabled,
        "agent": agent,
        "episodes": len(rows),
        "mean_final_score": statistics.fmean(final_scores),
        "std_final_score": (
            statistics.stdev(final_scores) if len(final_scores) > 1 else 0.0
        ),
        "min_final_score": min(final_scores),
        "max_final_score": max(final_scores),
        "mean_raw_score": statistics.fmean(_numbers(rows, "raw_score")),
        "mean_major_line_bonus": statistics.fmean(
            _numbers(rows, "major_line_bonus")
        ),
        "mean_operation_card_bonus": statistics.fmean(
            _numbers(rows, "operation_card_bonus")
        ),
        "mean_end_game_card_bonus": statistics.fmean(
            _numbers(rows, "end_game_card_bonus")
        ),
        "mean_financing_penalty": statistics.fmean(
            _numbers(rows, "financing_penalty")
        ),
        "mean_cards_selected": statistics.fmean(
            _numbers(rows, "cards_selected")
        ),
        "mean_cards_completed": statistics.fmean(
            _numbers(rows, "cards_completed")
        ),
        "mean_invalid_actions": statistics.fmean(
            _numbers(rows, "invalid_actions")
        ),
        "mean_runtime_seconds": statistics.fmean(
            _numbers(rows, "runtime_seconds")
        ),
    }


def _numbers(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _write_csv(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 4 Card Comparison Summary",
        "",
        "| map | cards | agent | episodes | mean final | std | raw | major line | op card | end card | financing penalty | cards selected | cards completed | invalid | runtime (s) |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['map']} | "
            f"{'enabled' if row['cards_enabled'] else 'disabled'} | "
            f"{row['agent']} | "
            f"{row['episodes']} | "
            f"{row['mean_final_score']:.2f} | "
            f"{row['std_final_score']:.2f} | "
            f"{row['mean_raw_score']:.2f} | "
            f"{row['mean_major_line_bonus']:.2f} | "
            f"{row['mean_operation_card_bonus']:.2f} | "
            f"{row['mean_end_game_card_bonus']:.2f} | "
            f"{row['mean_financing_penalty']:.2f} | "
            f"{row['mean_cards_selected']:.2f} | "
            f"{row['mean_cards_completed']:.2f} | "
            f"{row['mean_invalid_actions']:.2f} | "
            f"{row['mean_runtime_seconds']:.4f} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarise Phase 4 card experiments.")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument(
        "--output-csv",
        default="results/summary/phase4_card_comparison_summary.csv",
    )
    parser.add_argument(
        "--output-md",
        default="results/summary/phase4_card_comparison_summary.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = summarise_phase4_results(
        args.inputs,
        args.output_csv,
        args.output_md,
    )
    print(f"Wrote {len(summaries)} summary rows to {args.output_csv}")
    print(f"Wrote markdown summary to {args.output_md}")


if __name__ == "__main__":
    main()
