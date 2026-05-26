from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics

import matplotlib.pyplot as plt

DEFAULT_INPUT = Path("results/raw/mcts_tuning_results.csv")
DEFAULT_OUTPUT_DIR = Path("results/plots/mcts_tuning")


def plot_mcts_tuning(
    input_path: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> None:
    rows = _read_rows(input_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summaries = _summarise(rows)

    _line_plot(
        summaries,
        x_column="mcts_iterations",
        y_column="mean_final_score",
        title="MCTS Iterations vs Final Score",
        ylabel="Mean final score",
        output_path=output / "mcts_iterations_vs_score.png",
    )
    _line_plot(
        summaries,
        x_column="mcts_iterations",
        y_column="mean_runtime_seconds",
        title="MCTS Iterations vs Runtime",
        ylabel="Mean runtime (seconds)",
        output_path=output / "mcts_iterations_vs_runtime.png",
    )
    _line_plot(
        summaries,
        x_column="mcts_rollout_depth",
        y_column="mean_final_score",
        title="MCTS Rollout Depth vs Final Score",
        ylabel="Mean final score",
        output_path=output / "mcts_rollout_depth_vs_score.png",
    )
    _score_runtime_tradeoff(
        summaries,
        output / "mcts_policy_score_runtime_tradeoff.png",
    )
    _candidate_count_plot(
        summaries,
        output / "mcts_candidate_count_score_runtime.png",
    )
    _bar_plot(
        summaries,
        "score_per_second",
        "MCTS Score per Second",
        "Score per second",
        output / "mcts_score_per_second.png",
    )


def _read_rows(input_path: str | Path) -> list[dict[str, str]]:
    with Path(input_path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _summarise(rows: list[dict[str, str]]) -> list[dict[str, float | str]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row["map"],
            row["mcts_iterations"],
            row["mcts_rollout_depth"],
            row["mcts_rollout_policy"],
            row["mcts_action_generation"],
            row["mcts_max_candidate_actions"],
        )
        grouped.setdefault(key, []).append(row)

    summaries: list[dict[str, float | str]] = []
    for key, group_rows in grouped.items():
        mean_score = statistics.fmean(float(row["final_score"]) for row in group_rows)
        mean_runtime = statistics.fmean(
            float(row["runtime_seconds"]) for row in group_rows
        )
        summaries.append(
            {
                "map": key[0],
                "mcts_iterations": float(key[1]),
                "mcts_rollout_depth": float(key[2]),
                "mcts_rollout_policy": key[3],
                "mcts_action_generation": key[4],
                "mcts_max_candidate_actions": float(key[5]),
                "mean_final_score": mean_score,
                "mean_runtime_seconds": mean_runtime,
                "score_per_second": mean_score / mean_runtime if mean_runtime else 0.0,
                "label": _label_from_key(key),
            }
        )
    return sorted(summaries, key=lambda row: str(row["label"]))


def _line_plot(
    summaries: list[dict[str, float | str]],
    x_column: str,
    y_column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    grouped: dict[str, list[dict[str, float | str]]] = {}
    for row in summaries:
        label = _series_label(row, exclude=x_column)
        grouped.setdefault(label, []).append(row)

    plt.figure(figsize=(max(9, len(grouped) * 0.8), 5.5))
    for label, rows in grouped.items():
        sorted_rows = sorted(rows, key=lambda row: float(row[x_column]))
        x_values = [float(row[x_column]) for row in sorted_rows]
        y_values = [float(row[y_column]) for row in sorted_rows]
        plt.plot(x_values, y_values, marker="o", label=label)

    plt.title(title)
    plt.xlabel(x_column.replace("mcts_", "").replace("_", " "))
    plt.ylabel(ylabel)
    if len(grouped) <= 12:
        plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _score_runtime_tradeoff(
    summaries: list[dict[str, float | str]],
    output_path: Path,
) -> None:
    plt.figure(figsize=(max(9, len(summaries) * 0.45), 5.5))
    for row in summaries:
        x_value = float(row["mean_runtime_seconds"])
        y_value = float(row["mean_final_score"])
        plt.scatter(x_value, y_value, color="#4c78a8")
        plt.annotate(
            str(row["label"]),
            (x_value, y_value),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=7,
        )

    plt.title("MCTS Policy Score-Runtime Trade-off")
    plt.xlabel("Mean runtime (seconds)")
    plt.ylabel("Mean final score")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _candidate_count_plot(
    summaries: list[dict[str, float | str]],
    output_path: Path,
) -> None:
    plt.figure(figsize=(9, 5.5))
    for row in summaries:
        x_value = float(row["mcts_max_candidate_actions"])
        y_value = float(row["mean_final_score"])
        runtime = float(row["mean_runtime_seconds"])
        plt.scatter(x_value, y_value, s=max(30.0, runtime * 8), alpha=0.7)
        plt.annotate(
            str(row["label"]),
            (x_value, y_value),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=7,
        )

    plt.title("Candidate Count vs Score and Runtime")
    plt.xlabel("Max candidate actions")
    plt.ylabel("Mean final score")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _bar_plot(
    summaries: list[dict[str, float | str]],
    column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    sorted_rows = sorted(summaries, key=lambda row: float(row[column]), reverse=True)
    labels = [str(row["label"]) for row in sorted_rows]
    values = [float(row[column]) for row in sorted_rows]

    plt.figure(figsize=(max(10, len(labels) * 0.9), 5.5))
    plt.bar(labels, values, color="#59a14f")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _series_label(
    row: dict[str, float | str],
    exclude: str,
) -> str:
    parts = []
    if exclude != "mcts_iterations":
        parts.append(f"i{int(float(row['mcts_iterations']))}")
    if exclude != "mcts_rollout_depth":
        parts.append(f"d{int(float(row['mcts_rollout_depth']))}")
    parts.extend(
        [
            str(row["mcts_rollout_policy"]).replace("greedy_delivery", "greedy"),
            str(row["mcts_action_generation"]),
            f"c{int(float(row['mcts_max_candidate_actions']))}",
        ]
    )
    return "_".join(parts)


def _label_from_key(key: tuple[str, ...]) -> str:
    policy = key[3].replace("greedy_delivery", "greedy")
    return f"i{key[1]}_d{key[2]}_{policy}_{key[4]}_c{key[5]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot MCTS tuning results.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plot_mcts_tuning(args.input, args.output_dir)
    print(f"Wrote MCTS tuning plots to {args.output_dir}")


if __name__ == "__main__":
    main()
