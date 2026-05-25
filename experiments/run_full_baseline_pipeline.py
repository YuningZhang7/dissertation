from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = PROJECT_ROOT / "results" / "raw" / "experiment_results.csv"


def run_pipeline(
    episodes: int,
    seed: int,
    output: str | Path = DEFAULT_RESULTS,
    map_arg: str = "all",
) -> None:
    output_path = Path(output)
    validate_command = [
        sys.executable,
        "experiments/validate_baselines.py",
        "--input",
        str(output_path),
        "--episodes",
        str(episodes),
    ]
    if map_arg == "all":
        validate_command.extend(["--maps", "toy_map,toy_medium_map"])
    elif map_arg:
        validate_command.extend(["--maps", Path(map_arg).stem])

    commands = [
        [sys.executable, "experiments/smoke_test_rules.py"],
        [sys.executable, "experiments/smoke_test_agents.py"],
        [sys.executable, "experiments/smoke_test_maps.py"],
        [
            sys.executable,
            "experiments/run_experiments.py",
            "--agent",
            "all",
            "--episodes",
            str(episodes),
            "--seed",
            str(seed),
            "--map",
            map_arg,
            "--output",
            str(output_path),
        ],
        [sys.executable, "experiments/analyse_results.py", "--input", str(output_path)],
        [sys.executable, "experiments/plot_results.py", "--input", str(output_path)],
        validate_command,
    ]

    for command in commands:
        print(f"\nRunning: {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full baseline validation pipeline.")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default=str(DEFAULT_RESULTS))
    parser.add_argument("--map", default="all")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(args.episodes, args.seed, args.output, args.map)


if __name__ == "__main__":
    main()
