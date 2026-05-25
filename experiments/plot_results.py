from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics

import matplotlib.pyplot as plt

DEFAULT_INPUT = Path("results/raw/experiment_results.csv")
DEFAULT_OUTPUT_DIR = Path("results/plots")


def plot_results(
    input_path: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> None:
    rows = _read_rows(input_path)
    grouped = _group_rows(rows)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    _bar_plot(
        grouped,
        "final_score",
        "Mean Final Score by Agent",
        "Final score",
        output / "final_score_by_agent.png",
    )
    _distribution_plot(
        grouped,
        "final_score",
        "Final Score Distribution by Agent",
        "Final score",
        output / "final_score_distribution.png",
    )
    _bar_plot(grouped, "deliveries", "Mean Deliveries by Agent", "Deliveries", output / "deliveries_by_agent.png")
    _bar_plot(grouped, "bonds", "Mean Bonds by Agent", "Bonds", output / "bonds_by_agent.png")
    _bar_plot(grouped, "built_edges", "Mean Built Edges by Agent", "Built edges", output / "built_edges_by_agent.png")
    _bar_plot(grouped, "runtime_seconds", "Mean Runtime by Agent", "Runtime (seconds)", output / "runtime_by_agent.png")
    _bar_plot(grouped, "invalid_actions", "Mean Invalid Actions by Agent", "Invalid actions", output / "invalid_actions_by_agent.png")
    _terminal_rate_plot(grouped, output / "terminal_rate_by_agent.png")


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _group_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["agent"], []).append(row)
    return dict(sorted(grouped.items()))


def _values(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows if column in row and row[column] != ""]


def _bar_plot(
    grouped: dict[str, list[dict[str, str]]],
    column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    if not _has_column(grouped, column):
        print(f"Skipping {output_path.name}: missing column {column}")
        return

    agents = list(grouped)
    means = [statistics.fmean(_values(grouped[agent], column)) for agent in agents]
    plt.figure(figsize=(8, 5))
    plt.bar(agents, means, color="#4c78a8")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Agent")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _distribution_plot(
    grouped: dict[str, list[dict[str, str]]],
    column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    if not _has_column(grouped, column):
        print(f"Skipping {output_path.name}: missing column {column}")
        return

    agents = list(grouped)
    data = [_values(grouped[agent], column) for agent in agents]
    plt.figure(figsize=(8, 5))
    plt.boxplot(data)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Agent")
    plt.xticks(range(1, len(agents) + 1), agents, rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _terminal_rate_plot(
    grouped: dict[str, list[dict[str, str]]],
    output_path: Path,
) -> None:
    if not _has_column(grouped, "terminal"):
        print(f"Skipping {output_path.name}: missing column terminal")
        return

    agents = list(grouped)
    rates = []
    for agent in agents:
        rows = grouped[agent]
        terminal_count = sum(1 for row in rows if _as_bool(row["terminal"]))
        rates.append(terminal_count / len(rows) if rows else 0.0)

    plt.figure(figsize=(8, 5))
    plt.bar(agents, rates, color="#59a14f")
    plt.title("Terminal Rate by Agent")
    plt.ylabel("Terminal rate")
    plt.xlabel("Agent")
    plt.ylim(0, 1.05)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _has_column(grouped: dict[str, list[dict[str, str]]], column: str) -> bool:
    return all(rows and column in rows[0] for rows in grouped.values())


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot baseline experiment results.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plot_results(args.input, args.output_dir)
    print(f"Wrote plots to {args.output_dir}")


if __name__ == "__main__":
    main()
