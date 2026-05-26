from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from exact.exact_solver import (
    ExactSolver,
    ExactSolverSettings,
    replay_actions,
    result_to_dict,
)
from railways.environment import final_score, is_terminal, reset_game

DEFAULT_MAP = PROJECT_ROOT / "data" / "micro_map.json"
DEFAULT_CONFIG = PROJECT_ROOT / "data" / "micro_rules_config.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "exact_benchmark" / "micro_map_exact_result.json"


def run_exact_benchmark(
    map_path: str | Path = DEFAULT_MAP,
    config_path: str | Path = DEFAULT_CONFIG,
    output: str | Path = DEFAULT_OUTPUT,
    max_expanded_states: int | None = None,
) -> dict:
    initial_state = reset_game(map_path, config_path)
    solver = ExactSolver(
        ExactSolverSettings(
            branch_and_bound=False,
            max_expanded_states=max_expanded_states,
        )
    )
    result = solver.solve(initial_state)

    replay_state, replay_ok, replay_message = replay_actions(
        initial_state,
        result.optimal_actions,
    )
    if not replay_ok:
        raise RuntimeError(replay_message)
    if not is_terminal(replay_state):
        raise RuntimeError("Optimal action replay did not reach a terminal state.")
    if final_score(replay_state) != result.optimal_score:
        raise RuntimeError(
            "Replay final score does not match exact optimum: "
            f"{final_score(replay_state)} != {result.optimal_score}"
        )

    payload = result_to_dict(result, map_path, config_path)
    payload["replay_final_score"] = final_score(replay_state)
    payload["replay_terminal"] = replay_state.is_terminal()
    payload["replay_message"] = replay_message

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run exact search on micro_map.")
    parser.add_argument("--map", default=str(DEFAULT_MAP))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-expanded-states", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_exact_benchmark(
        map_path=args.map,
        config_path=args.config,
        output=args.output,
        max_expanded_states=args.max_expanded_states,
    )
    print("Exact benchmark result")
    print(f"- map: {payload['map']}")
    print(f"- config: {payload['config']}")
    print(f"- optimal_final_score: {payload['optimal_final_score']}")
    print(f"- optimal_action_count: {payload['optimal_action_count']}")
    print(f"- expanded_states: {payload['expanded_states']}")
    print(f"- memo_hits: {payload['memo_hits']}")
    print(f"- runtime_seconds: {payload['runtime_seconds']:.4f}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
