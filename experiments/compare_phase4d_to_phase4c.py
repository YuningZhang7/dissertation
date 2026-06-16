from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_PHASE4C_SUMMARY = (
    PROJECT_ROOT / "results" / "summary" / "phase4_standard_card_comparison_summary.csv"
)
DEFAULT_PHASE4D_SUMMARY = (
    PROJECT_ROOT / "results" / "summary" / "phase4d_card_aware_summary.csv"
)
DEFAULT_OUTPUT_CSV = (
    PROJECT_ROOT / "results" / "summary" / "phase4d_vs_phase4c_comparison.csv"
)
DEFAULT_OUTPUT_MD = (
    PROJECT_ROOT / "results" / "summary" / "phase4d_vs_phase4c_comparison.md"
)
COMPARISON_COLUMNS = [
    "map",
    "comparison",
    "baseline_agent",
    "new_agent",
    "baseline_mean_final_score",
    "new_mean_final_score",
    "delta",
    "baseline_cards_selected",
    "new_cards_selected",
    "baseline_cards_completed",
    "new_cards_completed",
    "baseline_runtime",
    "new_runtime",
]
COMPARISONS = [
    ("card_aware_greedy_vs_greedy_delivery", "greedy_delivery", "card_aware_greedy"),
    ("card_aware_greedy_vs_greedy_expansion", "greedy_expansion", "card_aware_greedy"),
    ("mcts_card_rollout_vs_mcts", "mcts", "mcts_card_rollout"),
    (
        "mcts_majorline_card_rollout_vs_mcts_majorline",
        "mcts_majorline",
        "mcts_majorline_card_rollout",
    ),
]


def compare_phase4d_to_phase4c(
    phase4c_summary: str | Path = DEFAULT_PHASE4C_SUMMARY,
    phase4d_summary: str | Path = DEFAULT_PHASE4D_SUMMARY,
    output_csv: str | Path = DEFAULT_OUTPUT_CSV,
    output_md: str | Path = DEFAULT_OUTPUT_MD,
) -> list[dict[str, Any]]:
    phase4c_rows = _index_phase4c_card_enabled(_read_rows(phase4c_summary))
    phase4d_rows = _index_by_map_agent(_read_rows(phase4d_summary))
    maps = sorted({key[0] for key in phase4c_rows} | {key[0] for key in phase4d_rows})

    comparison_rows: list[dict[str, Any]] = []
    for map_name in maps:
        for comparison_name, baseline_agent, new_agent in COMPARISONS:
            baseline = phase4c_rows.get((map_name, baseline_agent))
            new = phase4d_rows.get((map_name, new_agent))
            if baseline is None or new is None:
                continue
            baseline_score = float(baseline["mean_final_score"])
            new_score = float(new["mean_final_score"])
            comparison_rows.append(
                {
                    "map": map_name,
                    "comparison": comparison_name,
                    "baseline_agent": baseline_agent,
                    "new_agent": new_agent,
                    "baseline_mean_final_score": baseline_score,
                    "new_mean_final_score": new_score,
                    "delta": new_score - baseline_score,
                    "baseline_cards_selected": float(baseline["mean_cards_selected"]),
                    "new_cards_selected": float(new["mean_cards_selected"]),
                    "baseline_cards_completed": float(baseline["mean_cards_completed"]),
                    "new_cards_completed": float(new["mean_cards_completed"]),
                    "baseline_runtime": float(baseline["mean_runtime_seconds"]),
                    "new_runtime": float(new["mean_runtime_seconds"]),
                }
            )

    _write_csv(comparison_rows, output_csv, COMPARISON_COLUMNS)
    _write_markdown(comparison_rows, output_md)
    return comparison_rows


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _index_phase4c_card_enabled(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, str]]:
    indexed: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if not _as_bool(row.get("cards_enabled", "false")):
            continue
        indexed[(row["map"], row["agent"])] = row
    return indexed


def _index_by_map_agent(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["map"], row["agent"]): row for row in rows}


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


def _write_markdown(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    lines = [
        "# Phase 4D vs Phase 4C Comparison",
        "",
        "| map | comparison | baseline | new | baseline score | new score | delta | baseline cards selected | new cards selected | baseline cards completed | new cards completed | baseline runtime | new runtime |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['map']} | "
            f"{row['comparison']} | "
            f"{row['baseline_agent']} | "
            f"{row['new_agent']} | "
            f"{row['baseline_mean_final_score']:.2f} | "
            f"{row['new_mean_final_score']:.2f} | "
            f"{row['delta']:+.2f} | "
            f"{row['baseline_cards_selected']:.2f} | "
            f"{row['new_cards_selected']:.2f} | "
            f"{row['baseline_cards_completed']:.2f} | "
            f"{row['new_cards_completed']:.2f} | "
            f"{row['baseline_runtime']:.4f} | "
            f"{row['new_runtime']:.4f} |"
        )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Phase 4D card-aware results with Phase 4C baselines."
    )
    parser.add_argument("--phase4c-summary", default=str(DEFAULT_PHASE4C_SUMMARY))
    parser.add_argument("--phase4d-summary", default=str(DEFAULT_PHASE4D_SUMMARY))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = compare_phase4d_to_phase4c(
        phase4c_summary=args.phase4c_summary,
        phase4d_summary=args.phase4d_summary,
        output_csv=args.output_csv,
        output_md=args.output_md,
    )
    print(f"Wrote {len(rows)} Phase 4D comparison rows.")
    print(f"csv: {args.output_csv}")
    print(f"markdown: {args.output_md}")


if __name__ == "__main__":
    main()
