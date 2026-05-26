from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics

import matplotlib.pyplot as plt

DEFAULT_INPUT = Path("results/raw/major_line_sensitivity_results.csv")
DEFAULT_OUTPUT_DIR = Path("results/plots/major_line_sensitivity")


def plot_sensitivity(input_path: str | Path, output_dir: str | Path) -> None:
    rows = _read_rows(input_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    _line_plot(
        rows,
        metric="final_score",
        ylabel="Mean final score",
        title="Final score vs major-line multiplier",
        output_path=output / "score_vs_major_line_multiplier.png",
    )
    _line_plot(
        rows,
        metric="major_line_bonus",
        ylabel="Mean major-line bonus",
        title="Major-line bonus vs multiplier",
        output_path=output / "major_line_bonus_vs_multiplier.png",
    )
    _line_plot(
        rows,
        metric="deliveries",
        ylabel="Mean deliveries",
        title="Deliveries vs major-line multiplier",
        output_path=output / "deliveries_vs_multiplier.png",
    )
    _line_plot(
        rows,
        metric="runtime_seconds",
        ylabel="Mean runtime (seconds)",
        title="Runtime vs major-line multiplier",
        output_path=output / "runtime_vs_multiplier.png",
    )


def _line_plot(
    rows: list[dict[str, str]],
    metric: str,
    ylabel: str,
    title: str,
    output_path: Path,
) -> None:
    grouped: dict[str, dict[float, list[float]]] = {}
    for row in rows:
        grouped.setdefault(row["agent"], {}).setdefault(
            float(row["major_line_multiplier"]),
            [],
        ).append(float(row[metric]))

    plt.figure(figsize=(10, 6))
    for agent in sorted(grouped):
        points = sorted(
            (multiplier, statistics.fmean(values))
            for multiplier, values in grouped[agent].items()
        )
        if not points:
            continue
        x_values = [point[0] for point in points]
        y_values = [point[1] for point in points]
        plt.plot(x_values, y_values, marker="o", linewidth=2, label=agent)

    plt.xlabel("Major-line bonus multiplier")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(axis="y", alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot major-line sensitivity experiment results."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plot_sensitivity(args.input, args.output_dir)
    print(f"Wrote plots to {args.output_dir}")


if __name__ == "__main__":
    main()
