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
    grouped_by_agent = _group_rows(rows, ["agent"])
    grouped_by_map_agent = _group_rows(rows, ["map", "agent"])
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    _bar_plot(
        grouped_by_agent,
        "final_score",
        "Mean Final Score by Agent",
        "Final score",
        output / "final_score_by_agent.png",
    )
    _distribution_plot(
        grouped_by_agent,
        "final_score",
        "Final Score Distribution by Agent",
        "Final score",
        output / "final_score_distribution.png",
    )
    _bar_plot(grouped_by_agent, "deliveries", "Mean Deliveries by Agent", "Deliveries", output / "deliveries_by_agent.png")
    _bar_plot(grouped_by_agent, "bonds", "Mean Bonds by Agent", "Bonds", output / "bonds_by_agent.png")
    _bar_plot(grouped_by_agent, "built_edges", "Mean Built Edges by Agent", "Built edges", output / "built_edges_by_agent.png")
    _bar_plot(grouped_by_agent, "runtime_seconds", "Mean Runtime by Agent", "Runtime (seconds)", output / "runtime_by_agent.png")
    _bar_plot(grouped_by_agent, "invalid_actions", "Mean Invalid Actions by Agent", "Invalid actions", output / "invalid_actions_by_agent.png")
    _terminal_rate_plot(grouped_by_agent, output / "terminal_rate_by_agent.png")

    _map_agent_bar_plot(grouped_by_map_agent, "final_score", "Mean Final Score by Map and Agent", "Final score", output / "final_score_by_map_agent.png")
    _map_agent_bar_plot(grouped_by_map_agent, "deliveries", "Mean Deliveries by Map and Agent", "Deliveries", output / "deliveries_by_map_agent.png")
    _map_agent_bar_plot(grouped_by_map_agent, "bonds", "Mean Bonds by Map and Agent", "Bonds", output / "bonds_by_map_agent.png")
    _map_agent_bar_plot(grouped_by_map_agent, "built_edges", "Mean Built Edges by Map and Agent", "Built edges", output / "built_edges_by_map_agent.png")
    _map_agent_bar_plot(grouped_by_map_agent, "runtime_seconds", "Mean Runtime by Map and Agent", "Runtime (seconds)", output / "runtime_by_map_agent.png")
    _score_runtime_tradeoff_plot(
        grouped_by_map_agent,
        output / "score_runtime_tradeoff.png",
    )


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _group_rows(
    rows: list[dict[str, str]],
    keys: list[str],
) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        group_key = tuple(row.get(key, "unknown") for key in keys)
        grouped.setdefault(group_key, []).append(row)
    return dict(sorted(grouped.items()))


def _values(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows if column in row and row[column] != ""]


def _bar_plot(
    grouped: dict[tuple[str, ...], list[dict[str, str]]],
    column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    if not _has_column(grouped, column):
        print(f"Skipping {output_path.name}: missing column {column}")
        return

    labels = [_label(group_key) for group_key in grouped]
    means = [statistics.fmean(_values(rows, column)) for rows in grouped.values()]
    plt.figure(figsize=_figure_size_for_labels(labels))
    plt.bar(labels, means, color="#4c78a8")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Agent")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _distribution_plot(
    grouped: dict[tuple[str, ...], list[dict[str, str]]],
    column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    if not _has_column(grouped, column):
        print(f"Skipping {output_path.name}: missing column {column}")
        return

    labels = [_label(group_key) for group_key in grouped]
    data = [_values(rows, column) for rows in grouped.values()]
    plt.figure(figsize=_figure_size_for_labels(labels))
    plt.boxplot(data)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Agent")
    plt.xticks(range(1, len(labels) + 1), labels, rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _map_agent_bar_plot(
    grouped: dict[tuple[str, ...], list[dict[str, str]]],
    column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    if not _has_column(grouped, column):
        print(f"Skipping {output_path.name}: missing column {column}")
        return

    maps = sorted({group_key[0] for group_key in grouped})
    agents = sorted({group_key[1] for group_key in grouped})
    x_positions = range(len(maps))
    width = 0.8 / max(1, len(agents))

    plt.figure(figsize=(max(10, len(agents) * 1.5 + len(maps) * 1.2), 5.5))
    for agent_index, agent in enumerate(agents):
        offsets = [x + (agent_index - (len(agents) - 1) / 2) * width for x in x_positions]
        means = []
        for map_name in maps:
            rows = grouped.get((map_name, agent), [])
            means.append(statistics.fmean(_values(rows, column)) if rows else 0.0)
        plt.bar(offsets, means, width=width, label=agent)

    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Map")
    plt.xticks(list(x_positions), maps, rotation=15, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _terminal_rate_plot(
    grouped: dict[tuple[str, ...], list[dict[str, str]]],
    output_path: Path,
) -> None:
    if not _has_column(grouped, "terminal"):
        print(f"Skipping {output_path.name}: missing column terminal")
        return

    labels = [_label(group_key) for group_key in grouped]
    rates = []
    for rows in grouped.values():
        terminal_count = sum(1 for row in rows if _as_bool(row["terminal"]))
        rates.append(terminal_count / len(rows) if rows else 0.0)

    plt.figure(figsize=_figure_size_for_labels(labels))
    plt.bar(labels, rates, color="#59a14f")
    plt.title("Terminal Rate by Agent")
    plt.ylabel("Terminal rate")
    plt.xlabel("Agent")
    plt.ylim(0, 1.05)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _has_column(
    grouped: dict[tuple[str, ...], list[dict[str, str]]],
    column: str,
) -> bool:
    return all(rows and column in rows[0] for rows in grouped.values())


def _score_runtime_tradeoff_plot(
    grouped: dict[tuple[str, ...], list[dict[str, str]]],
    output_path: Path,
) -> None:
    if not _has_column(grouped, "final_score") or not _has_column(
        grouped,
        "runtime_seconds",
    ):
        print(f"Skipping {output_path.name}: missing score or runtime columns")
        return

    points = []
    for group_key, rows in grouped.items():
        label = _label(group_key)
        mean_score = statistics.fmean(_values(rows, "final_score"))
        mean_runtime = statistics.fmean(_values(rows, "runtime_seconds"))
        points.append((mean_runtime, mean_score, label))

    if not points:
        return

    plt.figure(figsize=(max(9, len(points) * 0.7), 5.5))
    for mean_runtime, mean_score, label in points:
        plt.scatter(mean_runtime, mean_score, color="#4c78a8")
        plt.annotate(
            label,
            (mean_runtime, mean_score),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
        )

    plt.title("Final Score vs Runtime Trade-off")
    plt.xlabel("Mean runtime (seconds)")
    plt.ylabel("Mean final score")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _figure_size_for_labels(labels: list[str]) -> tuple[float, float]:
    return (max(8.0, len(labels) * 1.05), 5.0)


def _label(group_key: tuple[str, ...]) -> str:
    return " / ".join(group_key)


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
