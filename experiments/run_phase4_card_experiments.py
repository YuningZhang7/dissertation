from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.mcts_agent import MCTSAgent
from agents.registry import create_agent
from experiments.run_experiments import write_results_csv
from experiments.simulation_runner import run_episode
from experiments.summarise_phase4_results import summarise_phase4_results
from railways.environment import DEFAULT_CARDS_PATH, DEFAULT_CONFIG_PATH


DEFAULT_MAPS = [
    PROJECT_ROOT / "data" / "toy_map.json",
    PROJECT_ROOT / "data" / "toy_medium_map.json",
    PROJECT_ROOT / "data" / "semi_realistic_map.json",
]
DEFAULT_AGENTS = [
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "mcts",
    "mcts_majorline",
]
DEFAULT_DISABLED_OUTPUT = (
    PROJECT_ROOT / "results" / "raw" / "phase4_card_disabled_results.csv"
)
DEFAULT_ENABLED_OUTPUT = (
    PROJECT_ROOT / "results" / "raw" / "phase4_card_enabled_results.csv"
)
DEFAULT_SUMMARY_CSV = (
    PROJECT_ROOT / "results" / "summary" / "phase4_card_comparison_summary.csv"
)
DEFAULT_SUMMARY_MD = (
    PROJECT_ROOT / "results" / "summary" / "phase4_card_comparison_summary.md"
)


def run_phase4_card_experiments(
    maps: list[str | Path] | None = None,
    agents: list[str] | None = None,
    episodes: int = 5,
    seed: int = 0,
    max_steps: int = 500,
    mcts_iterations: int = 25,
    mcts_rollout_depth: int = 40,
    disabled_output: str | Path = DEFAULT_DISABLED_OUTPUT,
    enabled_output: str | Path = DEFAULT_ENABLED_OUTPUT,
    summary_csv: str | Path = DEFAULT_SUMMARY_CSV,
    summary_md: str | Path = DEFAULT_SUMMARY_MD,
) -> list[dict[str, Any]]:
    selected_maps = [Path(path) for path in (maps or DEFAULT_MAPS)]
    selected_agents = agents or DEFAULT_AGENTS

    disabled_rows = _run_mode(
        selected_maps,
        selected_agents,
        episodes,
        seed,
        max_steps,
        mcts_iterations,
        mcts_rollout_depth,
        card_path=None,
    )
    enabled_rows = _run_mode(
        selected_maps,
        selected_agents,
        episodes,
        seed,
        max_steps,
        mcts_iterations,
        mcts_rollout_depth,
        card_path=DEFAULT_CARDS_PATH,
    )

    write_results_csv(disabled_rows, disabled_output)
    write_results_csv(enabled_rows, enabled_output)
    return summarise_phase4_results(
        [disabled_output, enabled_output],
        summary_csv,
        summary_md,
    )


def _run_mode(
    maps: list[Path],
    agents: list[str],
    episodes: int,
    seed: int,
    max_steps: int,
    mcts_iterations: int,
    mcts_rollout_depth: int,
    card_path: Path | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for map_path in maps:
        for agent_name in agents:
            for episode_index in range(episodes):
                episode_seed = seed + episode_index
                agent = _create_phase4_agent(
                    agent_name,
                    episode_seed,
                    mcts_iterations,
                    mcts_rollout_depth,
                )
                result = run_episode(
                    agent,
                    seed=episode_seed,
                    max_steps=max_steps,
                    map_path=map_path,
                    config_path=DEFAULT_CONFIG_PATH,
                    card_path=card_path,
                )
                result["agent"] = agent_name
                rows.append(result)
    return rows


def _create_phase4_agent(
    name: str,
    seed: int,
    mcts_iterations: int,
    mcts_rollout_depth: int,
):
    if name == "mcts":
        return MCTSAgent(
            seed=seed,
            iterations=mcts_iterations,
            rollout_depth_limit=mcts_rollout_depth,
        )
    if name == "mcts_majorline":
        return MCTSAgent(
            seed=seed,
            iterations=mcts_iterations,
            rollout_depth_limit=mcts_rollout_depth,
            evaluation_mode="major_line_aware",
        )
    return create_agent(name, seed=seed)


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 4 card comparisons.")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--mcts-iterations", type=int, default=25)
    parser.add_argument("--mcts-rollout-depth", type=int, default=40)
    parser.add_argument(
        "--maps",
        default=",".join(str(path) for path in DEFAULT_MAPS),
    )
    parser.add_argument("--agents", default=",".join(DEFAULT_AGENTS))
    parser.add_argument("--disabled-output", default=str(DEFAULT_DISABLED_OUTPUT))
    parser.add_argument("--enabled-output", default=str(DEFAULT_ENABLED_OUTPUT))
    parser.add_argument("--summary-csv", default=str(DEFAULT_SUMMARY_CSV))
    parser.add_argument("--summary-md", default=str(DEFAULT_SUMMARY_MD))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = run_phase4_card_experiments(
        maps=_parse_list(args.maps),
        agents=_parse_list(args.agents),
        episodes=args.episodes,
        seed=args.seed,
        max_steps=args.max_steps,
        mcts_iterations=args.mcts_iterations,
        mcts_rollout_depth=args.mcts_rollout_depth,
        disabled_output=args.disabled_output,
        enabled_output=args.enabled_output,
        summary_csv=args.summary_csv,
        summary_md=args.summary_md,
    )
    print(f"Wrote {len(summaries)} Phase 4 summary rows.")
    print(f"Card-disabled raw results: {args.disabled_output}")
    print(f"Card-enabled raw results: {args.enabled_output}")
    print(f"Summary CSV: {args.summary_csv}")
    print(f"Summary markdown: {args.summary_md}")


if __name__ == "__main__":
    main()
