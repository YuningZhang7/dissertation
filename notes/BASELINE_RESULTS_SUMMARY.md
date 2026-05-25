# Baseline Results Summary

## Experiment Setup

- Map: `data/toy_map.json`
- Rules config: `data/rules_config.json`
- Agents: `random`, `greedy_delivery`, `greedy_expansion`
- Episodes: 100 per agent
- Seed: 0
- Date: 2026-05-25

## Summary Table

| agent | episodes | mean_final_score | std_final_score | min_final_score | max_final_score | mean_raw_score | mean_bonds | mean_deliveries | mean_built_edges | mean_major_line_bonus | mean_empty_markers | mean_invalid_actions | invalid_action_rate | terminal_rate | mean_actions_taken | mean_runtime_seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| greedy_delivery | 100 | 10.00 | 0.00 | 10.00 | 10.00 | 9.00 | 2.00 | 7.00 | 12.00 | 3.00 | 7.00 | 0.00 | 0.0000 | 1.00 | 33.00 | 0.0054 |
| greedy_expansion | 100 | 10.00 | 0.00 | 10.00 | 10.00 | 9.00 | 2.00 | 7.00 | 12.00 | 3.00 | 7.00 | 0.00 | 0.0000 | 1.00 | 33.00 | 0.0261 |
| random | 100 | 4.45 | 4.05 | -3.00 | 15.00 | 6.52 | 4.44 | 4.98 | 8.81 | 2.37 | 4.65 | 0.00 | 0.0000 | 1.00 | 28.56 | 0.0096 |

## Initial Observations

- `greedy_delivery` and `greedy_expansion` achieved the highest average final score on the current toy map.
- The two greedy agents produced identical score-level outcomes in this run, which suggests the current toy map is small enough that their heuristics converge to similar play.
- `random` had much higher variance, including a negative minimum final score and a maximum score above the greedy baselines.
- Both greedy agents delivered more goods on average than `random`.
- `random` used more bonds on average.
- All agents had zero invalid actions.
- All episodes terminated normally.
- `greedy_expansion` was slower than `greedy_delivery`, as expected, because it simulates build candidates before choosing.

## Generated Outputs

- `results/raw/experiment_results.csv`
- `results/processed/summary_by_agent.csv`
- `results/plots/final_score_by_agent.png`
- `results/plots/final_score_distribution.png`
- `results/plots/deliveries_by_agent.png`
- `results/plots/bonds_by_agent.png`
- `results/plots/built_edges_by_agent.png`
- `results/plots/runtime_by_agent.png`
- `results/plots/invalid_actions_by_agent.png`
- `results/plots/terminal_rate_by_agent.png`

## Next Step

The baseline platform looks structurally stable. If baseline results remain stable after a larger map or richer rules, the next stage will be to implement a search-based agent, most likely Monte Carlo Tree Search.
