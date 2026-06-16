from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


FIGURE_DIR = PROJECT_ROOT / "results" / "figures"
SUMMARY_DIR = PROJECT_ROOT / "results" / "summary"
FIGURE_PATHS = {
    "phase4c_card_effect_by_agent": FIGURE_DIR / "phase4c_card_effect_by_agent.png",
    "phase4d_vs_phase4c_delta": FIGURE_DIR / "phase4d_vs_phase4c_delta.png",
    "phase4_mcts_budget_score_runtime": FIGURE_DIR
    / "phase4_mcts_budget_score_runtime.png",
    "phase4_mcts_budget_score_delta": FIGURE_DIR
    / "phase4_mcts_budget_score_delta.png",
    "phase4_mcts_budget_runtime_delta": FIGURE_DIR
    / "phase4_mcts_budget_runtime_delta.png",
    "phase4d_score_decomposition": FIGURE_DIR
    / "phase4d_score_decomposition.png",
    "phase4d_card_usage": FIGURE_DIR / "phase4d_card_usage.png",
}


def generate_dissertation_figures(output_dir: str | Path = FIGURE_DIR) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {name: output / path.name for name, path in FIGURE_PATHS.items()}
    _plot_phase4c_card_effect(paths["phase4c_card_effect_by_agent"])
    _plot_phase4d_delta(paths["phase4d_vs_phase4c_delta"])
    _plot_mcts_budget(paths)
    _plot_phase4d_score_decomposition(paths["phase4d_score_decomposition"])
    _plot_phase4d_card_usage(paths["phase4d_card_usage"])
    return list(paths.values())


def _plot_phase4c_card_effect(output_path: Path) -> None:
    rows = _read_csv(SUMMARY_DIR / "phase4_standard_card_effect_table.csv")
    maps = _ordered_unique(row["map"] for row in rows)
    agents = _ordered_unique(row["agent"] for row in rows)
    width = 0.14
    x_positions = list(range(len(maps)))

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for index, agent in enumerate(agents):
        values = [
            _lookup_float(rows, {"map": map_name, "agent": agent}, "final_score_delta")
            for map_name in maps
        ]
        offsets = [x + (index - (len(agents) - 1) / 2) * width for x in x_positions]
        ax.bar(offsets, values, width=width, label=_label(agent))

    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title("Phase 4C card effect by map and agent")
    ax.set_ylabel("Final score change from enabling cards")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([_label(item) for item in maps])
    ax.legend(ncol=3, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _save(fig, output_path)


def _plot_phase4d_delta(output_path: Path) -> None:
    rows = _read_csv(SUMMARY_DIR / "phase4d_vs_phase4c_comparison.csv")
    comparisons = [
        "card_aware_greedy_vs_greedy_delivery",
        "mcts_card_rollout_vs_mcts",
        "mcts_majorline_card_rollout_vs_mcts_majorline",
    ]
    maps = _ordered_unique(row["map"] for row in rows)
    width = 0.23
    x_positions = list(range(len(maps)))

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    for index, comparison in enumerate(comparisons):
        values = [
            _lookup_float(rows, {"map": map_name, "comparison": comparison}, "delta")
            for map_name in maps
        ]
        offsets = [x + (index - 1) * width for x in x_positions]
        ax.bar(offsets, values, width=width, label=_comparison_label(comparison))

    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title("Phase 4D improvement over Phase 4C card-enabled baselines")
    ax.set_ylabel("Mean final score delta")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([_label(item) for item in maps])
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _save(fig, output_path)


def _plot_mcts_budget(paths: dict[str, Path]) -> None:
    rows = _read_csv(SUMMARY_DIR / "phase4_mcts_budget_comparison.csv")
    labels = [
        f"{_label(row['map'])}\n{_label(row['agent'])}\n{'cards' if _as_bool(row['cards_enabled']) else 'no cards'}"
        for row in rows
    ]
    score_delta = [float(row["budget_delta"]) for row in rows]
    runtime_delta = [float(row["runtime_delta"]) for row in rows]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].bar(range(len(rows)), score_delta, color="#4477AA")
    axes[0].set_ylabel("Score delta")
    axes[0].set_title("MCTS100 budget diagnostic: score and runtime change")
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].bar(range(len(rows)), runtime_delta, color="#CC6677")
    axes[1].set_ylabel("Runtime delta (s)")
    axes[1].set_xticks(range(len(rows)))
    axes[1].set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)
    _save(fig, paths["phase4_mcts_budget_score_runtime"])

    _single_bar_plot(
        labels,
        score_delta,
        "MCTS100 score change over standard MCTS budget",
        "Mean final score delta",
        paths["phase4_mcts_budget_score_delta"],
        "#4477AA",
    )
    _single_bar_plot(
        labels,
        runtime_delta,
        "MCTS100 runtime increase over standard MCTS budget",
        "Runtime delta (s)",
        paths["phase4_mcts_budget_runtime_delta"],
        "#CC6677",
    )


def _plot_phase4d_score_decomposition(output_path: Path) -> None:
    rows = _read_csv(SUMMARY_DIR / "phase4d_card_aware_summary.csv")
    agents = {
        "mcts",
        "mcts_card_rollout",
        "mcts_majorline",
        "mcts_majorline_card_rollout",
    }
    selected = [row for row in rows if row["agent"] in agents]
    selected.sort(key=lambda row: (row["map"], row["agent"]))
    labels = [f"{_label(row['map'])}\n{_label(row['agent'])}" for row in selected]
    components = [
        ("Raw score", "mean_raw_score", "#88CCEE"),
        ("Major-line bonus", "mean_major_line_bonus", "#44AA99"),
        ("Operation-card bonus", "mean_operation_card_bonus", "#DDCC77"),
        ("End-game-card bonus", "mean_end_game_card_bonus", "#CC6677"),
    ]

    fig, ax = plt.subplots(figsize=(13, 6.5))
    x_positions = list(range(len(selected)))
    bottoms = [0.0 for _ in selected]
    for label, column, color in components:
        values = [float(row[column]) for row in selected]
        ax.bar(x_positions, values, bottom=bottoms, label=label, color=color)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    penalties = [-float(row["mean_financing_penalty"]) for row in selected]
    ax.bar(x_positions, penalties, label="Financing penalty", color="#999999")

    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title("Phase 4D score decomposition for MCTS agents")
    ax.set_ylabel("Mean score component")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.legend(ncol=3, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _save(fig, output_path)


def _plot_phase4d_card_usage(output_path: Path) -> None:
    rows = _read_csv(SUMMARY_DIR / "phase4d_card_aware_summary.csv")
    agents = {
        "card_aware_greedy",
        "mcts",
        "mcts_card_rollout",
        "mcts_majorline_card_rollout",
    }
    selected = [row for row in rows if row["agent"] in agents]
    selected.sort(key=lambda row: (row["map"], row["agent"]))
    labels = [f"{_label(row['map'])}\n{_label(row['agent'])}" for row in selected]
    selected_values = [float(row["mean_cards_selected"]) for row in selected]
    completed_values = [float(row["mean_cards_completed"]) for row in selected]
    x_positions = list(range(len(selected)))
    width = 0.36

    fig, ax = plt.subplots(figsize=(13, 5.8))
    ax.bar(
        [x - width / 2 for x in x_positions],
        selected_values,
        width=width,
        label="Cards selected",
        color="#4477AA",
    )
    ax.bar(
        [x + width / 2 for x in x_positions],
        completed_values,
        width=width,
        label="Cards completed",
        color="#228833",
    )
    ax.set_title("Phase 4D card usage")
    ax.set_ylabel("Mean cards per episode")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    _save(fig, output_path)


def _single_bar_plot(
    labels: list[str],
    values: list[float],
    title: str,
    ylabel: str,
    output_path: Path,
    color: str,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.bar(range(len(values)), values, color=color)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _save(fig, output_path)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}")
    with path.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"Input CSV has no rows: {path}")
    return rows


def _lookup_float(
    rows: list[dict[str, str]],
    criteria: dict[str, str],
    column: str,
) -> float:
    for row in rows:
        if all(row[key] == value for key, value in criteria.items()):
            return float(row[column])
    raise KeyError(f"No row for criteria {criteria}")


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _label(value: str) -> str:
    return value.replace("_", " ")


def _comparison_label(value: str) -> str:
    labels = {
        "card_aware_greedy_vs_greedy_delivery": "Card-aware greedy vs greedy delivery",
        "mcts_card_rollout_vs_mcts": "Card-aware rollout vs MCTS",
        "mcts_majorline_card_rollout_vs_mcts_majorline": "Card-aware rollout vs major-line MCTS",
    }
    return labels.get(value, _label(value))


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _save(fig: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    paths = generate_dissertation_figures()
    for path in paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
