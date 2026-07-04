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
        route = groups.get("route_segment_greedy")
        objective = groups.get("objective_aware_greedy")
        adaptive = groups.get("adaptive_objective_greedy")
        if route and objective:
            delta = objective["mean_final_score"] - route["mean_final_score"]
            lines.append(
                f"  objective_aware_greedy vs route_segment_greedy: {delta:+.2f}"
            )
        if objective and adaptive:
            delta = adaptive["mean_final_score"] - objective["mean_final_score"]
            lines.append(
                f"  adaptive_objective_greedy vs objective_aware_greedy: {delta:+.2f}"
            )
            if (
                adaptive["mean_runtime_seconds"] > objective["mean_runtime_seconds"]
                and adaptive["mean_final_score"] < objective["mean_final_score"]
            ):
                lines.append(
                    "  Warning: adaptive_objective_greedy is slower and lower-scoring."
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
