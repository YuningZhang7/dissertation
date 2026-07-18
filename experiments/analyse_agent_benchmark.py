from __future__ import annotations

import argparse
import json
from pathlib import Path


def analyse_summary(path: str | Path) -> str:
    summary = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = [f"Maps found: {', '.join(sorted(summary))}"]
    agents = sorted({agent for groups in summary.values() for agent in groups})
    lines.append(f"Agents found: {', '.join(agents)}")
    for map_name, groups in summary.items():
        best = max(groups, key=lambda name: groups[name]["mean_final_score"])
        lines.append(f"{map_name}: Best agent is {best}.")
        objective = groups.get("objective_aware_greedy")
        lookahead = groups.get("lookahead_greedy")
        if objective and lookahead:
            delta = lookahead["mean_final_score"] - objective["mean_final_score"]
            lines.append(
                f"  lookahead_greedy vs objective_aware_greedy: {delta:+.2f}"
            )
            if (
                lookahead["mean_runtime_seconds"] > objective["mean_runtime_seconds"]
                and lookahead["mean_final_score"] < objective["mean_final_score"]
            ):
                lines.append(
                    "  Warning: lookahead_greedy is slower and lower-scoring."
                )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse an agent benchmark summary.")
    parser.add_argument("--summary", required=True)
    return parser.parse_args()


def main() -> None:
    print(analyse_summary(parse_args().summary))


if __name__ == "__main__":
    main()
