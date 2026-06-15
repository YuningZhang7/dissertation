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
EFFECT_COLUMNS = [
    "map",
    "agent",
    "cards_disabled_mean_final_score",
    "cards_enabled_mean_final_score",
    "final_score_delta",
]
USAGE_COLUMNS = [
    "map",
    "agent",
    "mean_cards_selected",
    "mean_cards_completed",
    "mean_operation_card_bonus",
    "mean_end_game_card_bonus",
]


def summarise_phase4_results(
    input_paths: list[str | Path],
    output_csv: str | Path,
    output_md: str | Path,
    effect_csv: str | Path | None = None,
    effect_md: str | Path | None = None,
    usage_csv: str | Path | None = None,
    usage_md: str | Path | None = None,
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
    _write_csv(summaries, output_csv, SUMMARY_COLUMNS)
    _write_summary_markdown(summaries, output_md)

    effect_rows = build_card_effect_rows(summaries)
    usage_rows = build_card_usage_rows(summaries)
    if effect_csv is not None:
        _write_csv(effect_rows, effect_csv, EFFECT_COLUMNS)
    if effect_md is not None:
        _write_effect_markdown(effect_rows, effect_md)
    if usage_csv is not None:
        _write_csv(usage_rows, usage_csv, USAGE_COLUMNS)
    if usage_md is not None:
        _write_usage_markdown(usage_rows, usage_md)
    return summaries


def build_card_effect_rows(
    summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paired: dict[tuple[str, str], dict[bool, dict[str, Any]]] = {}
    for row in summaries:
        paired.setdefault((row["map"], row["agent"]), {})[
            bool(row["cards_enabled"])
        ] = row

    effect_rows: list[dict[str, Any]] = []
    for (map_name, agent), modes in paired.items():
        if False not in modes or True not in modes:
            continue
        disabled_score = float(modes[False]["mean_final_score"])
        enabled_score = float(modes[True]["mean_final_score"])
        effect_rows.append(
            {
                "map": map_name,
                "agent": agent,
                "cards_disabled_mean_final_score": disabled_score,
                "cards_enabled_mean_final_score": enabled_score,
                "final_score_delta": enabled_score - disabled_score,
            }
        )
    effect_rows.sort(key=lambda row: (row["map"], row["agent"]))
    return effect_rows


def build_card_usage_rows(
    summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    usage_rows = [
        {
            "map": row["map"],
            "agent": row["agent"],
            "mean_cards_selected": row["mean_cards_selected"],
            "mean_cards_completed": row["mean_cards_completed"],
            "mean_operation_card_bonus": row["mean_operation_card_bonus"],
            "mean_end_game_card_bonus": row["mean_end_game_card_bonus"],
        }
        for row in summaries
        if row["cards_enabled"]
    ]
    usage_rows.sort(key=lambda row: (row["map"], row["agent"]))
    return usage_rows


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


def _write_csv(
    rows: list[dict[str, Any]],
    output_path: str | Path,
    columns: list[str],
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary_markdown(
    rows: list[dict[str, Any]], output_path: str | Path
) -> None:
    lines = [
        "# Phase 4 Card Comparison Summary",
        "",
        "| map | cards | agent | episodes | mean final | std | min | max | raw | major line | op card | end card | financing penalty | cards selected | cards completed | invalid | runtime (s) |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
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
            f"{row['min_final_score']:.2f} | "
            f"{row['max_final_score']:.2f} | "
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
    _write_markdown_lines(lines, output_path)


def _write_effect_markdown(
    rows: list[dict[str, Any]], output_path: str | Path
) -> None:
    lines = [
        "# Phase 4 Card Effect Table",
        "",
        "| map | agent | cards disabled mean | cards enabled mean | change |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['map']} | {row['agent']} | "
            f"{row['cards_disabled_mean_final_score']:.2f} | "
            f"{row['cards_enabled_mean_final_score']:.2f} | "
            f"{row['final_score_delta']:+.2f} |"
        )
    _write_markdown_lines(lines, output_path)


def _write_usage_markdown(
    rows: list[dict[str, Any]], output_path: str | Path
) -> None:
    lines = [
        "# Phase 4 Card Usage Table",
        "",
        "| map | agent | cards selected | cards completed | operation-card bonus | end-game-card bonus |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['map']} | {row['agent']} | "
            f"{row['mean_cards_selected']:.2f} | "
            f"{row['mean_cards_completed']:.2f} | "
            f"{row['mean_operation_card_bonus']:.2f} | "
            f"{row['mean_end_game_card_bonus']:.2f} |"
        )
    _write_markdown_lines(lines, output_path)


def _write_markdown_lines(lines: list[str], output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--effect-csv")
    parser.add_argument("--effect-md")
    parser.add_argument("--usage-csv")
    parser.add_argument("--usage-md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = summarise_phase4_results(
        args.inputs,
        args.output_csv,
        args.output_md,
        effect_csv=args.effect_csv,
        effect_md=args.effect_md,
        usage_csv=args.usage_csv,
        usage_md=args.usage_md,
    )
    print(f"Wrote {len(summaries)} summary rows to {args.output_csv}")
    print(f"Wrote markdown summary to {args.output_md}")


if __name__ == "__main__":
    main()
