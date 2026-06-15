from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_STANDARD_SUMMARY = (
    PROJECT_ROOT
    / "results"
    / "summary"
    / "phase4_standard_card_comparison_summary.csv"
)
DEFAULT_MCTS100_SUMMARY = (
    PROJECT_ROOT
    / "results"
    / "summary"
    / "phase4_mcts100_card_comparison_summary.csv"
)
DEFAULT_OUTPUT_CSV = (
    PROJECT_ROOT / "results" / "summary" / "phase4_mcts_budget_comparison.csv"
)
DEFAULT_OUTPUT_MD = (
    PROJECT_ROOT / "results" / "summary" / "phase4_mcts_budget_comparison.md"
)
FOCUS_AGENTS = {"mcts", "mcts_majorline"}
COMPARISON_COLUMNS = [
    "map",
    "agent",
    "cards_enabled",
    "standard_mean_final_score",
    "mcts100_mean_final_score",
    "budget_delta",
    "standard_runtime",
    "mcts100_runtime",
    "runtime_delta",
    "standard_cards_selected",
    "mcts100_cards_selected",
    "standard_cards_completed",
    "mcts100_cards_completed",
    "standard_operation_card_bonus",
    "mcts100_operation_card_bonus",
    "standard_end_game_card_bonus",
    "mcts100_end_game_card_bonus",
]


def compare_phase4_mcts_budget(
    standard_summary: str | Path = DEFAULT_STANDARD_SUMMARY,
    mcts100_summary: str | Path = DEFAULT_MCTS100_SUMMARY,
    output_csv: str | Path = DEFAULT_OUTPUT_CSV,
    output_md: str | Path = DEFAULT_OUTPUT_MD,
) -> list[dict[str, Any]]:
    standard_rows = _index_rows(_read_rows(standard_summary))
    mcts100_rows = _index_rows(_read_rows(mcts100_summary))
    shared_keys = sorted(set(standard_rows) & set(mcts100_rows))

    rows = [
        _comparison_row(key, standard_rows[key], mcts100_rows[key])
        for key in shared_keys
        if key[2] in FOCUS_AGENTS
    ]
    if not rows:
        raise ValueError("No shared MCTS rows were found in the two summaries.")

    _write_csv(rows, output_csv)
    _write_markdown(rows, output_md)
    return rows


def _index_rows(
    rows: list[dict[str, str]],
) -> dict[tuple[str, bool, str], dict[str, str]]:
    indexed: dict[tuple[str, bool, str], dict[str, str]] = {}
    for row in rows:
        key = (row["map"], _as_bool(row["cards_enabled"]), row["agent"])
        indexed[key] = row
    return indexed


def _comparison_row(
    key: tuple[str, bool, str],
    standard: dict[str, str],
    mcts100: dict[str, str],
) -> dict[str, Any]:
    map_name, cards_enabled, agent = key
    standard_score = float(standard["mean_final_score"])
    mcts100_score = float(mcts100["mean_final_score"])
    standard_runtime = float(standard["mean_runtime_seconds"])
    mcts100_runtime = float(mcts100["mean_runtime_seconds"])
    return {
        "map": map_name,
        "agent": agent,
        "cards_enabled": cards_enabled,
        "standard_mean_final_score": standard_score,
        "mcts100_mean_final_score": mcts100_score,
        "budget_delta": mcts100_score - standard_score,
        "standard_runtime": standard_runtime,
        "mcts100_runtime": mcts100_runtime,
        "runtime_delta": mcts100_runtime - standard_runtime,
        "standard_cards_selected": float(standard["mean_cards_selected"]),
        "mcts100_cards_selected": float(mcts100["mean_cards_selected"]),
        "standard_cards_completed": float(standard["mean_cards_completed"]),
        "mcts100_cards_completed": float(mcts100["mean_cards_completed"]),
        "standard_operation_card_bonus": float(
            standard["mean_operation_card_bonus"]
        ),
        "mcts100_operation_card_bonus": float(
            mcts100["mean_operation_card_bonus"]
        ),
        "standard_end_game_card_bonus": float(
            standard["mean_end_game_card_bonus"]
        ),
        "mcts100_end_game_card_bonus": float(
            mcts100["mean_end_game_card_bonus"]
        ),
    }


def build_card_effect_comparison(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[bool, dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["map"], row["agent"]), {})[
            bool(row["cards_enabled"])
        ] = row

    effects: list[dict[str, Any]] = []
    for (map_name, agent), modes in sorted(grouped.items()):
        if False not in modes or True not in modes:
            continue
        standard_effect = (
            modes[True]["standard_mean_final_score"]
            - modes[False]["standard_mean_final_score"]
        )
        mcts100_effect = (
            modes[True]["mcts100_mean_final_score"]
            - modes[False]["mcts100_mean_final_score"]
        )
        effects.append(
            {
                "map": map_name,
                "agent": agent,
                "standard_card_effect_delta": standard_effect,
                "mcts100_card_effect_delta": mcts100_effect,
                "difference": mcts100_effect - standard_effect,
            }
        )
    return effects


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"Summary contains no rows: {path}")
    return rows


def _write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COMPARISON_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(rows: list[dict[str, Any]], path: str | Path) -> None:
    lines = [
        "# Phase 4 MCTS Budget Comparison",
        "",
        "## Score and Runtime by Card Mode",
        "",
        "| map | agent | cards | standard score | mcts100 score | score change | standard runtime (s) | mcts100 runtime (s) | runtime change (s) | cards selected | cards completed |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['map']} | {row['agent']} | "
            f"{'enabled' if row['cards_enabled'] else 'disabled'} | "
            f"{row['standard_mean_final_score']:.2f} | "
            f"{row['mcts100_mean_final_score']:.2f} | "
            f"{row['budget_delta']:+.2f} | "
            f"{row['standard_runtime']:.2f} | "
            f"{row['mcts100_runtime']:.2f} | "
            f"{row['runtime_delta']:+.2f} | "
            f"{row['standard_cards_selected']:.2f} -> "
            f"{row['mcts100_cards_selected']:.2f} | "
            f"{row['standard_cards_completed']:.2f} -> "
            f"{row['mcts100_cards_completed']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Does the Larger Budget Change the Card Effect?",
            "",
            "Card effect is the card-enabled mean final score minus the card-disabled mean final score within the same profile.",
            "",
            "| map | agent | standard card effect | mcts100 card effect | difference |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in build_card_effect_comparison(rows):
        lines.append(
            "| "
            f"{row['map']} | {row['agent']} | "
            f"{row['standard_card_effect_delta']:+.2f} | "
            f"{row['mcts100_card_effect_delta']:+.2f} | "
            f"{row['difference']:+.2f} |"
        )

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Phase 4 standard and mcts100 MCTS results."
    )
    parser.add_argument("--standard-summary", default=str(DEFAULT_STANDARD_SUMMARY))
    parser.add_argument("--mcts100-summary", default=str(DEFAULT_MCTS100_SUMMARY))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = compare_phase4_mcts_budget(
        standard_summary=args.standard_summary,
        mcts100_summary=args.mcts100_summary,
        output_csv=args.output_csv,
        output_md=args.output_md,
    )
    print(f"Wrote {len(rows)} MCTS budget comparison rows.")
    print(f"Comparison CSV: {args.output_csv}")
    print(f"Comparison markdown: {args.output_md}")


if __name__ == "__main__":
    main()
