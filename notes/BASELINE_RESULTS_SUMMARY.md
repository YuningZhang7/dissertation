# Baseline Results Summary

## Experiment Setup

- Maps: `data/toy_map.json`, `data/toy_medium_map.json`
- Rules config: `data/rules_config.json`
- Agents: `random`, `greedy_delivery`, `greedy_expansion`
- Episodes: 100 per map-agent pair
- Seed: 0
- Date: 2026-05-25

## Summary Table

| map | agent | episodes | mean_final_score | std_final_score | min_final_score | max_final_score | mean_raw_score | mean_bonds | mean_deliveries | mean_built_edges | mean_major_line_bonus | mean_empty_markers | mean_invalid_actions | invalid_action_rate | terminal_rate | mean_actions_taken | mean_runtime_seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| toy_map | greedy_delivery | 100 | 10.00 | 0.00 | 10.00 | 10.00 | 9.00 | 2.00 | 7.00 | 12.00 | 3.00 | 7.00 | 0.00 | 0.0000 | 1.00 | 33.00 | 0.0052 |
| toy_map | greedy_expansion | 100 | 10.00 | 0.00 | 10.00 | 10.00 | 9.00 | 2.00 | 7.00 | 12.00 | 3.00 | 7.00 | 0.00 | 0.0000 | 1.00 | 33.00 | 0.0266 |
| toy_map | random | 100 | 4.13 | 4.31 | -8.00 | 15.00 | 6.24 | 4.63 | 4.79 | 8.70 | 2.52 | 4.51 | 0.00 | 0.0000 | 1.00 | 28.47 | 0.0093 |
| toy_medium_map | greedy_delivery | 100 | 32.00 | 0.00 | 32.00 | 32.00 | 13.00 | 0.00 | 13.00 | 20.00 | 19.00 | 6.00 | 0.00 | 0.0000 | 1.00 | 33.00 | 0.0767 |
| toy_medium_map | greedy_expansion | 100 | 30.00 | 0.00 | 30.00 | 30.00 | 11.00 | 0.00 | 11.00 | 22.00 | 19.00 | 7.00 | 0.00 | 0.0000 | 1.00 | 33.00 | 0.5867 |
| toy_medium_map | random | 100 | 10.78 | 8.17 | -3.00 | 33.00 | 9.90 | 3.22 | 7.69 | 11.92 | 4.10 | 3.88 | 0.00 | 0.0000 | 1.00 | 30.01 | 0.0886 |

## Initial Observations

- On `toy_map`, `greedy_delivery` and `greedy_expansion` still produce identical score-level outcomes, confirming that the small map is mainly useful for debugging.
- On `toy_medium_map`, the greedy agents no longer behave identically: `greedy_delivery` achieves a higher mean final score, while `greedy_expansion` builds a larger network.
- `toy_medium_map` creates clearer strategy differences through longer routes, bottleneck edges, and larger major-line bonuses.
- `random` remains much more variable on both maps.
- All map-agent combinations had zero invalid actions.
- All episodes terminated normally.
- `greedy_expansion` is substantially slower on the medium map because it simulates build candidates.

## Generated Outputs

- `results/raw/map_comparison_results.csv`
- `results/processed/summary_by_map_agent.csv`
- `results/plots/final_score_by_agent.png`
- `results/plots/final_score_distribution.png`
- `results/plots/deliveries_by_agent.png`
- `results/plots/bonds_by_agent.png`
- `results/plots/built_edges_by_agent.png`
- `results/plots/runtime_by_agent.png`
- `results/plots/invalid_actions_by_agent.png`
- `results/plots/terminal_rate_by_agent.png`
- `results/plots/final_score_by_map_agent.png`
- `results/plots/deliveries_by_map_agent.png`
- `results/plots/bonds_by_map_agent.png`
- `results/plots/built_edges_by_map_agent.png`
- `results/plots/runtime_by_map_agent.png`

## Next Step

The medium map makes baseline comparison more meaningful. The next sensible step is to keep the advanced AI postponed briefly and either calibrate the medium scenario further or begin a search-based agent, most likely Monte Carlo Tree Search.

## Phase 3A Semi-realistic Baseline Extension

Phase 3A adds `semi_realistic_map`, a larger artificial scenario intended to improve external validity before moving to GA or RL.

Baseline command:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --map data/semi_realistic_map.json --output results/raw/semi_realistic_baseline_results.csv
```

Summary from `results/processed/semi_realistic_baseline_summary.csv`:

| map | agent | episodes | mean_final_score | std_final_score | mean_deliveries | mean_built_edges | mean_major_line_bonus | invalid_action_rate | terminal_rate | mean_runtime_seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| semi_realistic_map | random | 50 | 3.84 | 6.13 | 5.98 | 8.58 | 1.04 | 0.0000 | 1.00 | 0.25 |
| semi_realistic_map | greedy_delivery | 50 | 22.00 | 0.00 | 13.00 | 20.00 | 9.00 | 0.0000 | 1.00 | 0.27 |
| semi_realistic_map | greedy_expansion | 50 | 87.00 | 0.00 | 13.00 | 20.00 | 74.00 | 0.0000 | 1.00 | 2.27 |

Initial observations:

- The semi-realistic map strongly distinguishes `greedy_delivery` and `greedy_expansion`.
- `greedy_expansion` achieves much higher final score because it claims substantially more major-line bonus points.
- `random` remains weak and variable.
- All baseline runs had zero invalid actions and all episodes terminated normally.
- `greedy_expansion` is slower than the other baselines, but still practical for batch experiments.
