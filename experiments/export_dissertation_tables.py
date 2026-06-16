from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


TABLE_DIR = PROJECT_ROOT / "results" / "tables"
SUMMARY_DIR = PROJECT_ROOT / "results" / "summary"
EXACT_DIR = PROJECT_ROOT / "results" / "exact_benchmark"


def export_dissertation_tables(output_dir: str | Path = TABLE_DIR) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    generated.extend(_export_exact_benchmark(output))
    generated.extend(_export_phase4c_card_effect(output))
    generated.extend(_export_phase4c_mcts_budget(output))
    generated.extend(_export_phase4d_agent_comparison(output))
    return generated


def _export_exact_benchmark(output: Path) -> list[Path]:
    rows = _read_csv(EXACT_DIR / "micro_map_agent_comparison.csv")
    selected_agents = [
        "exact_optimum",
        "random",
        "greedy_delivery",
        "greedy_expansion",
        "mcts_25",
        "mcts_100",
        "mcts_25_majorline",
        "mcts_100_majorline",
    ]
    table_rows = []
    for agent in selected_agents:
        row = _find(rows, {"agent": agent})
        table_rows.append(
            {
                "Agent": _label(agent),
                "Episodes": row["episodes"],
                "Mean score": _fmt(row["mean_score"]),
                "Exact gap": _fmt(row["absolute_gap"]),
                "Relative gap (%)": _fmt(row["relative_gap_percent"]),
            }
        )
    return _write_table_pair(output, "table_exact_benchmark", table_rows)


def _export_phase4c_card_effect(output: Path) -> list[Path]:
    rows = _read_csv(SUMMARY_DIR / "phase4_standard_card_effect_table.csv")
    table_rows = [
        {
            "Map": _label(row["map"]),
            "Agent": _label(row["agent"]),
            "Cards off": _fmt(row["cards_disabled_mean_final_score"]),
            "Cards on": _fmt(row["cards_enabled_mean_final_score"]),
            "Delta": _signed(row["final_score_delta"]),
        }
        for row in rows
    ]
    return _write_table_pair(output, "table_phase4c_card_effect", table_rows)


def _export_phase4c_mcts_budget(output: Path) -> list[Path]:
    rows = _read_csv(SUMMARY_DIR / "phase4_mcts_budget_comparison.csv")
    table_rows = [
        {
            "Map": _label(row["map"]),
            "Agent": _label(row["agent"]),
            "Cards": "on" if _as_bool(row["cards_enabled"]) else "off",
            "Score delta": _signed(row["budget_delta"]),
            "Runtime delta (s)": _fmt(row["runtime_delta"]),
        }
        for row in rows
    ]
    return _write_table_pair(output, "table_phase4c_mcts_budget", table_rows)


def _export_phase4d_agent_comparison(output: Path) -> list[Path]:
    rows = _read_csv(SUMMARY_DIR / "phase4d_vs_phase4c_comparison.csv")
    keep = {
        "card_aware_greedy_vs_greedy_delivery",
        "mcts_card_rollout_vs_mcts",
        "mcts_majorline_card_rollout_vs_mcts_majorline",
    }
    table_rows = [
        {
            "Map": _label(row["map"]),
            "Comparison": _comparison_label(row["comparison"]),
            "Baseline": _fmt(row["baseline_mean_final_score"]),
            "Phase 4D": _fmt(row["new_mean_final_score"]),
            "Delta": _signed(row["delta"]),
            "Cards completed": f"{_fmt(row['baseline_cards_completed'])} -> {_fmt(row['new_cards_completed'])}",
        }
        for row in rows
        if row["comparison"] in keep
    ]
    return _write_table_pair(output, "table_phase4d_agent_comparison", table_rows)


def _write_table_pair(
    output: Path,
    stem: str,
    rows: list[dict[str, Any]],
) -> list[Path]:
    if not rows:
        raise ValueError(f"Cannot write empty table: {stem}")
    md_path = output / f"{stem}.md"
    tex_path = output / f"{stem}.tex"
    md_path.write_text(_to_markdown(rows), encoding="utf-8")
    tex_path.write_text(_to_latex(rows), encoding="utf-8")
    return [md_path, tex_path]


def _to_markdown(rows: list[dict[str, Any]]) -> str:
    columns = list(rows[0])
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(lines) + "\n"


def _to_latex(rows: list[dict[str, Any]]) -> str:
    columns = list(rows[0])
    column_spec = "l" * len(columns)
    lines = [
        f"\\begin{{tabular}}{{{column_spec}}}",
        "\\hline",
        " & ".join(_tex_escape(column) for column in columns) + " \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(
            " & ".join(_tex_escape(str(row[column])) for column in columns) + " \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}", ""])
    return "\n".join(lines)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing table input: {path}")
    with path.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"Table input has no rows: {path}")
    return rows


def _find(rows: list[dict[str, str]], criteria: dict[str, str]) -> dict[str, str]:
    for row in rows:
        if all(row[key] == value for key, value in criteria.items()):
            return row
    raise KeyError(f"No row matching {criteria}")


def _label(value: str) -> str:
    return value.replace("_", " ")


def _comparison_label(value: str) -> str:
    labels = {
        "card_aware_greedy_vs_greedy_delivery": "Card-aware greedy vs greedy delivery",
        "mcts_card_rollout_vs_mcts": "Card-aware rollout vs MCTS",
        "mcts_majorline_card_rollout_vs_mcts_majorline": "Card-aware rollout vs major-line MCTS",
    }
    return labels.get(value, _label(value))


def _fmt(value: str | float) -> str:
    return f"{float(value):.2f}"


def _signed(value: str | float) -> str:
    return f"{float(value):+.2f}"


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def main() -> None:
    for path in export_dissertation_tables():
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
