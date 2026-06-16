from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_MAPS = {"toy_map", "toy_medium_map", "semi_realistic_map"}
PHASE4_AGENTS = {"random", "greedy_delivery", "greedy_expansion", "mcts", "mcts_majorline"}
PHASE4D_AGENTS = {
    "greedy_delivery",
    "greedy_expansion",
    "card_aware_greedy",
    "mcts",
    "mcts_majorline",
    "mcts_card_rollout",
    "mcts_majorline_card_rollout",
}
PHASE4D_COMPARISONS = {
    "card_aware_greedy_vs_greedy_delivery",
    "card_aware_greedy_vs_greedy_expansion",
    "mcts_card_rollout_vs_mcts",
    "mcts_majorline_card_rollout_vs_mcts_majorline",
}


def validate_all_results() -> list[str]:
    messages: list[str] = []
    _validate_exact_benchmark(messages)
    _validate_phase4_profile("standard", PHASE4_AGENTS, messages)
    _validate_phase4_profile("mcts100", PHASE4_AGENTS, messages)
    _validate_phase4d(messages)
    _validate_notes(messages)
    messages.append("All required result artefacts validated.")
    return messages


def _validate_exact_benchmark(messages: list[str]) -> None:
    result_json = PROJECT_ROOT / "results" / "exact_benchmark" / "micro_map_exact_result.json"
    comparison_csv = (
        PROJECT_ROOT / "results" / "exact_benchmark" / "micro_map_agent_comparison.csv"
    )
    comparison_md = (
        PROJECT_ROOT / "results" / "exact_benchmark" / "micro_map_agent_comparison.md"
    )
    _require_file(result_json)
    _require_file(comparison_csv)
    _require_file(comparison_md)

    data = json.loads(result_json.read_text(encoding="utf-8"))
    if data.get("map") != "micro_map":
        raise ValueError("Exact benchmark JSON is not for micro_map.")
    if data.get("optimal_final_score") != data.get("replay_final_score"):
        raise ValueError("Exact benchmark replay score does not match optimum.")

    rows = _read_csv(comparison_csv)
    agents = {row["agent"] for row in rows}
    required = {
        "exact_optimum",
        "random",
        "greedy_delivery",
        "greedy_expansion",
        "mcts_25",
        "mcts_100",
        "mcts_25_majorline",
        "mcts_100_majorline",
    }
    _require_subset(required, agents, "exact benchmark agents")
    messages.append("PASS Exact benchmark results")


def _validate_phase4_profile(
    profile: str,
    expected_agents: set[str],
    messages: list[str],
) -> None:
    prefix = f"phase4_{profile}"
    raw_dir = PROJECT_ROOT / "results" / "raw"
    summary_dir = PROJECT_ROOT / "results" / "summary"
    disabled_raw = raw_dir / f"{prefix}_card_disabled_results.csv"
    enabled_raw = raw_dir / f"{prefix}_card_enabled_results.csv"
    summary_csv = summary_dir / f"{prefix}_card_comparison_summary.csv"
    summary_md = summary_dir / f"{prefix}_card_comparison_summary.md"
    effect_csv = summary_dir / f"{prefix}_card_effect_table.csv"
    effect_md = summary_dir / f"{prefix}_card_effect_table.md"
    usage_csv = summary_dir / f"{prefix}_card_usage_table.csv"
    usage_md = summary_dir / f"{prefix}_card_usage_table.md"

    for path in [
        disabled_raw,
        enabled_raw,
        summary_csv,
        summary_md,
        effect_csv,
        effect_md,
        usage_csv,
        usage_md,
    ]:
        _require_file(path)

    disabled_rows = _read_csv(disabled_raw)
    enabled_rows = _read_csv(enabled_raw)
    summary_rows = _read_csv(summary_csv)
    effect_rows = _read_csv(effect_csv)
    usage_rows = _read_csv(usage_csv)

    _require_columns(
        disabled_rows,
        {"map", "agent", "cards_enabled", "invalid_actions", "final_score"},
        f"{profile} disabled raw",
    )
    _require_columns(
        enabled_rows,
        {"map", "agent", "cards_enabled", "invalid_actions", "final_score"},
        f"{profile} enabled raw",
    )
    _require_columns(
        summary_rows,
        {"map", "cards_enabled", "agent", "mean_final_score", "mean_invalid_actions"},
        f"{profile} summary",
    )

    if any(_as_bool(row["cards_enabled"]) for row in disabled_rows):
        raise ValueError(f"Phase 4 {profile} disabled raw contains enabled rows.")
    if any(not _as_bool(row["cards_enabled"]) for row in enabled_rows):
        raise ValueError(f"Phase 4 {profile} enabled raw contains disabled rows.")

    combined = disabled_rows + enabled_rows
    maps = {row["map"] for row in combined}
    agents = {row["agent"] for row in combined}
    _require_subset(REQUIRED_MAPS, maps, f"Phase 4 {profile} maps")
    _require_subset(expected_agents, agents, f"Phase 4 {profile} agents")

    expected_pairs = {
        (map_name, agent)
        for map_name in REQUIRED_MAPS
        for agent in expected_agents
    }
    for mode_name, rows in (("disabled", disabled_rows), ("enabled", enabled_rows)):
        pairs = {(row["map"], row["agent"]) for row in rows}
        missing = expected_pairs - pairs
        if missing:
            raise ValueError(
                f"Phase 4 {profile} {mode_name} results miss pairs: {sorted(missing)}"
            )

    if len(effect_rows) < len(expected_pairs):
        raise ValueError(f"Phase 4 {profile} effect table is incomplete.")
    if len(usage_rows) < len(expected_pairs):
        raise ValueError(f"Phase 4 {profile} usage table is incomplete.")

    invalid_total = _sum_float(combined, "invalid_actions")
    if invalid_total == 0:
        messages.append(f"PASS Phase 4C {profile} results (invalid actions: 0)")
    else:
        messages.append(
            f"PASS Phase 4C {profile} results with invalid actions reported: {invalid_total:.0f}"
        )


def _validate_phase4d(messages: list[str]) -> None:
    raw_csv = PROJECT_ROOT / "results" / "raw" / "phase4d_card_aware_results.csv"
    summary_csv = PROJECT_ROOT / "results" / "summary" / "phase4d_card_aware_summary.csv"
    summary_md = PROJECT_ROOT / "results" / "summary" / "phase4d_card_aware_summary.md"
    comparison_csv = (
        PROJECT_ROOT / "results" / "summary" / "phase4d_vs_phase4c_comparison.csv"
    )
    comparison_md = (
        PROJECT_ROOT / "results" / "summary" / "phase4d_vs_phase4c_comparison.md"
    )
    for path in [raw_csv, summary_csv, summary_md, comparison_csv, comparison_md]:
        _require_file(path)

    raw_rows = _read_csv(raw_csv)
    summary_rows = _read_csv(summary_csv)
    comparison_rows = _read_csv(comparison_csv)
    _require_columns(
        raw_rows,
        {"map", "agent", "cards_enabled", "invalid_actions", "cards_selected"},
        "Phase 4D raw",
    )
    _require_columns(
        summary_rows,
        {"map", "agent", "mean_final_score", "mean_invalid_actions"},
        "Phase 4D summary",
    )
    _require_columns(
        comparison_rows,
        {"map", "comparison", "baseline_agent", "new_agent", "delta"},
        "Phase 4D comparison",
    )

    if any(not _as_bool(row["cards_enabled"]) for row in raw_rows):
        raise ValueError("Phase 4D raw results must be card-enabled.")
    _require_subset(REQUIRED_MAPS, {row["map"] for row in raw_rows}, "Phase 4D maps")
    _require_subset(PHASE4D_AGENTS, {row["agent"] for row in raw_rows}, "Phase 4D agents")

    expected_pairs = {
        (map_name, agent)
        for map_name in REQUIRED_MAPS
        for agent in PHASE4D_AGENTS
    }
    summary_pairs = {(row["map"], row["agent"]) for row in summary_rows}
    missing_pairs = expected_pairs - summary_pairs
    if missing_pairs:
        raise ValueError(f"Phase 4D summary misses pairs: {sorted(missing_pairs)}")

    _require_subset(
        PHASE4D_COMPARISONS,
        {row["comparison"] for row in comparison_rows},
        "Phase 4D comparisons",
    )
    invalid_total = _sum_float(raw_rows, "invalid_actions")
    if invalid_total == 0:
        messages.append("PASS Phase 4D card-aware results (invalid actions: 0)")
    else:
        messages.append(
            f"PASS Phase 4D card-aware results with invalid actions reported: {invalid_total:.0f}"
        )


def _validate_notes(messages: list[str]) -> None:
    required_notes = [
        "EXACT_BENCHMARK_RESULTS.md",
        "PHASE4_CARD_RESULTS_SUMMARY.md",
        "PHASE4_CARD_DISCUSSION_POINTS.md",
        "PHASE4D_CARD_AWARE_RESULTS.md",
        "PHASE4D_CARD_AWARE_AGENT_PLAN.md",
    ]
    for note_name in required_notes:
        _require_file(PROJECT_ROOT / "notes" / note_name)
    messages.append("PASS required markdown notes exist")


def _read_csv(path: Path) -> list[dict[str, str]]:
    _require_file(path)
    with path.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"CSV has no data rows: {path}")
    return rows


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required artefact: {path}")
    if path.is_file() and path.stat().st_size == 0:
        raise ValueError(f"Required artefact is empty: {path}")


def _require_columns(
    rows: list[dict[str, Any]],
    required: set[str],
    label: str,
) -> None:
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def _require_subset(required: set[str], actual: set[str], label: str) -> None:
    missing = required - actual
    if missing:
        raise ValueError(f"{label} missing: {sorted(missing)}")


def _sum_float(rows: list[dict[str, str]], column: str) -> float:
    return sum(float(row[column]) for row in rows)


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def main() -> None:
    for message in validate_all_results():
        print(message)


if __name__ == "__main__":
    main()
