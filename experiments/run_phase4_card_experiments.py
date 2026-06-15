from __future__ import annotations

import argparse
from dataclasses import dataclass
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
DEFAULT_PROFILE = "standard"


@dataclass(frozen=True)
class ExperimentProfile:
    episodes: int
    mcts_iterations: int
    mcts_rollout_depth: int
    max_steps: int


@dataclass(frozen=True)
class Phase4OutputPaths:
    disabled_raw: Path
    enabled_raw: Path
    summary_csv: Path
    summary_md: Path
    effect_csv: Path
    effect_md: Path
    usage_csv: Path
    usage_md: Path


EXPERIMENT_PROFILES = {
    "quick": ExperimentProfile(
        episodes=2,
        mcts_iterations=5,
        mcts_rollout_depth=20,
        max_steps=100,
    ),
    "standard": ExperimentProfile(
        episodes=30,
        mcts_iterations=25,
        mcts_rollout_depth=40,
        max_steps=500,
    ),
    "mcts100": ExperimentProfile(
        episodes=20,
        mcts_iterations=100,
        mcts_rollout_depth=80,
        max_steps=500,
    ),
}


def get_profile_output_paths(profile: str) -> Phase4OutputPaths:
    _get_profile(profile)
    raw_dir = PROJECT_ROOT / "results" / "raw"
    summary_dir = PROJECT_ROOT / "results" / "summary"
    prefix = f"phase4_{profile}"
    return Phase4OutputPaths(
        disabled_raw=raw_dir / f"{prefix}_card_disabled_results.csv",
        enabled_raw=raw_dir / f"{prefix}_card_enabled_results.csv",
        summary_csv=summary_dir / f"{prefix}_card_comparison_summary.csv",
        summary_md=summary_dir / f"{prefix}_card_comparison_summary.md",
        effect_csv=summary_dir / f"{prefix}_card_effect_table.csv",
        effect_md=summary_dir / f"{prefix}_card_effect_table.md",
        usage_csv=summary_dir / f"{prefix}_card_usage_table.csv",
        usage_md=summary_dir / f"{prefix}_card_usage_table.md",
    )


def resolve_profile_settings(
    profile: str,
    episodes: int | None = None,
    max_steps: int | None = None,
    mcts_iterations: int | None = None,
    mcts_rollout_depth: int | None = None,
) -> ExperimentProfile:
    defaults = _get_profile(profile)
    return ExperimentProfile(
        episodes=defaults.episodes if episodes is None else episodes,
        max_steps=defaults.max_steps if max_steps is None else max_steps,
        mcts_iterations=(
            defaults.mcts_iterations
            if mcts_iterations is None
            else mcts_iterations
        ),
        mcts_rollout_depth=(
            defaults.mcts_rollout_depth
            if mcts_rollout_depth is None
            else mcts_rollout_depth
        ),
    )


def run_phase4_card_experiments(
    maps: list[str | Path] | None = None,
    agents: list[str] | None = None,
    profile: str = DEFAULT_PROFILE,
    episodes: int | None = None,
    seed: int = 0,
    max_steps: int | None = None,
    mcts_iterations: int | None = None,
    mcts_rollout_depth: int | None = None,
    disabled_output: str | Path | None = None,
    enabled_output: str | Path | None = None,
    summary_csv: str | Path | None = None,
    summary_md: str | Path | None = None,
    effect_csv: str | Path | None = None,
    effect_md: str | Path | None = None,
    usage_csv: str | Path | None = None,
    usage_md: str | Path | None = None,
) -> list[dict[str, Any]]:
    settings = resolve_profile_settings(
        profile,
        episodes=episodes,
        max_steps=max_steps,
        mcts_iterations=mcts_iterations,
        mcts_rollout_depth=mcts_rollout_depth,
    )
    defaults = get_profile_output_paths(profile)
    outputs = Phase4OutputPaths(
        disabled_raw=Path(disabled_output or defaults.disabled_raw),
        enabled_raw=Path(enabled_output or defaults.enabled_raw),
        summary_csv=Path(summary_csv or defaults.summary_csv),
        summary_md=Path(summary_md or defaults.summary_md),
        effect_csv=Path(effect_csv or defaults.effect_csv),
        effect_md=Path(effect_md or defaults.effect_md),
        usage_csv=Path(usage_csv or defaults.usage_csv),
        usage_md=Path(usage_md or defaults.usage_md),
    )
    selected_maps = [Path(path) for path in (maps or DEFAULT_MAPS)]
    selected_agents = agents or DEFAULT_AGENTS

    disabled_rows = _run_mode(
        selected_maps,
        selected_agents,
        settings,
        seed,
        card_path=None,
        mode_name="card-disabled",
    )
    enabled_rows = _run_mode(
        selected_maps,
        selected_agents,
        settings,
        seed,
        card_path=DEFAULT_CARDS_PATH,
        mode_name="card-enabled",
    )

    write_results_csv(disabled_rows, outputs.disabled_raw)
    write_results_csv(enabled_rows, outputs.enabled_raw)
    return summarise_phase4_results(
        [outputs.disabled_raw, outputs.enabled_raw],
        outputs.summary_csv,
        outputs.summary_md,
        effect_csv=outputs.effect_csv,
        effect_md=outputs.effect_md,
        usage_csv=outputs.usage_csv,
        usage_md=outputs.usage_md,
    )


def _run_mode(
    maps: list[Path],
    agents: list[str],
    settings: ExperimentProfile,
    seed: int,
    card_path: Path | None,
    mode_name: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for map_path in maps:
        for agent_name in agents:
            print(
                f"[{mode_name}] {map_path.stem} / {agent_name}: "
                f"{settings.episodes} episodes"
            )
            for episode_index in range(settings.episodes):
                episode_seed = seed + episode_index
                agent = _create_phase4_agent(
                    agent_name,
                    episode_seed,
                    settings.mcts_iterations,
                    settings.mcts_rollout_depth,
                )
                result = run_episode(
                    agent,
                    seed=episode_seed,
                    max_steps=settings.max_steps,
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


def _get_profile(profile: str) -> ExperimentProfile:
    try:
        return EXPERIMENT_PROFILES[profile]
    except KeyError as error:
        choices = ", ".join(sorted(EXPERIMENT_PROFILES))
        raise ValueError(f"Unknown Phase 4 profile '{profile}'. Choose: {choices}.") from error


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 4 card comparisons.")
    parser.add_argument(
        "--profile",
        choices=sorted(EXPERIMENT_PROFILES),
        default=DEFAULT_PROFILE,
    )
    parser.add_argument("--episodes", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--mcts-iterations", type=int)
    parser.add_argument("--mcts-rollout-depth", type=int)
    parser.add_argument(
        "--maps",
        default=",".join(str(path) for path in DEFAULT_MAPS),
    )
    parser.add_argument("--agents", default=",".join(DEFAULT_AGENTS))
    parser.add_argument("--disabled-output")
    parser.add_argument("--enabled-output")
    parser.add_argument("--summary-csv")
    parser.add_argument("--summary-md")
    parser.add_argument("--effect-csv")
    parser.add_argument("--effect-md")
    parser.add_argument("--usage-csv")
    parser.add_argument("--usage-md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = resolve_profile_settings(
        args.profile,
        episodes=args.episodes,
        max_steps=args.max_steps,
        mcts_iterations=args.mcts_iterations,
        mcts_rollout_depth=args.mcts_rollout_depth,
    )
    defaults = get_profile_output_paths(args.profile)
    output_values = {
        "disabled": args.disabled_output or defaults.disabled_raw,
        "enabled": args.enabled_output or defaults.enabled_raw,
        "summary_csv": args.summary_csv or defaults.summary_csv,
        "summary_md": args.summary_md or defaults.summary_md,
        "effect_csv": args.effect_csv or defaults.effect_csv,
        "effect_md": args.effect_md or defaults.effect_md,
        "usage_csv": args.usage_csv or defaults.usage_csv,
        "usage_md": args.usage_md or defaults.usage_md,
    }
    print(
        f"Phase 4 profile={args.profile}: episodes={settings.episodes}, "
        f"mcts_iterations={settings.mcts_iterations}, "
        f"rollout_depth={settings.mcts_rollout_depth}, "
        f"max_steps={settings.max_steps}"
    )
    summaries = run_phase4_card_experiments(
        maps=_parse_list(args.maps),
        agents=_parse_list(args.agents),
        profile=args.profile,
        episodes=args.episodes,
        seed=args.seed,
        max_steps=args.max_steps,
        mcts_iterations=args.mcts_iterations,
        mcts_rollout_depth=args.mcts_rollout_depth,
        disabled_output=args.disabled_output,
        enabled_output=args.enabled_output,
        summary_csv=args.summary_csv,
        summary_md=args.summary_md,
        effect_csv=args.effect_csv,
        effect_md=args.effect_md,
        usage_csv=args.usage_csv,
        usage_md=args.usage_md,
    )
    print(f"Wrote {len(summaries)} Phase 4 summary rows.")
    for label, output_path in output_values.items():
        print(f"{label}: {output_path}")


if __name__ == "__main__":
    main()
