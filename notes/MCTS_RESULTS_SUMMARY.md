# MCTS Results Summary

## Experiment Setup

- Map: `toy_medium_map`
- Episodes: 30 for the main MCTS budget comparison
- Seed: 0
- MCTS budgets: 50, 100, 250 iterations
- Rollout policy: random
- Rollout depth: 80
- Exploration constant: 1.414
- Action generation: fast candidate actions, using legal rule-engine actions with shortest delivery candidates for MCTS planning speed

## Summary Table

Main result from `results/processed/mcts_summary_by_map_agent.csv`:

| Map | Agent | Episodes | Mean Final Score | Std | Mean Deliveries | Mean Built Edges | Mean Major Line Bonus | Invalid Rate | Terminal Rate | Mean Runtime (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| toy_medium_map | random | 30 | 11.37 | 8.27 | 7.80 | 12.00 | 4.87 | 0.0000 | 1.00 | 0.08 |
| toy_medium_map | greedy_delivery | 30 | 32.00 | 0.00 | 13.00 | 20.00 | 19.00 | 0.0000 | 1.00 | 0.07 |
| toy_medium_map | greedy_expansion | 30 | 30.00 | 0.00 | 11.00 | 22.00 | 19.00 | 0.0000 | 1.00 | 0.54 |
| toy_medium_map | mcts_50 | 30 | 51.67 | 4.49 | 16.33 | 12.97 | 18.10 | 0.0000 | 1.00 | 11.34 |
| toy_medium_map | mcts_100 | 30 | 53.43 | 3.86 | 16.87 | 12.83 | 18.73 | 0.0000 | 1.00 | 22.35 |
| toy_medium_map | mcts_250 | 30 | 56.77 | 3.94 | 17.50 | 12.50 | 18.83 | 0.0000 | 1.00 | 53.74 |

Small rollout-policy comparison from `results/processed/mcts_rollout_comparison_summary.csv`:

| Map | Agent | Episodes | Mean Final Score | Mean Deliveries | Invalid Rate | Terminal Rate | Mean Runtime (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| toy_medium_map | mcts_50_random | 5 | 47.80 | 14.80 | 0.0000 | 1.00 | 11.24 |
| toy_medium_map | mcts_50_greedy | 5 | 54.80 | 16.80 | 0.0000 | 1.00 | 33.22 |
| toy_medium_map | mcts_100_random | 5 | 51.80 | 16.60 | 0.0000 | 1.00 | 22.66 |
| toy_medium_map | mcts_100_greedy | 5 | 57.60 | 17.20 | 0.0000 | 1.00 | 65.10 |

## Initial Observations

- `mcts_250` achieved the highest mean final score in the main experiment: 56.77.
- All MCTS budgets clearly outperformed `random`, `greedy_delivery`, and `greedy_expansion` on mean final score.
- Increasing iterations improved mean final score from 51.67 at 50 iterations to 56.77 at 250 iterations.
- Runtime increased substantially with search budget: about 11.34 seconds per episode for `mcts_50`, 22.35 seconds for `mcts_100`, and 53.74 seconds for `mcts_250`.
- MCTS delivered more goods than the baselines: 17.50 average deliveries for `mcts_250` versus 13.00 for `greedy_delivery`.
- No invalid actions were recorded.
- All episodes terminated normally.
- The small rollout-policy comparison suggests greedy rollouts can improve MCTS score, but roughly triple runtime at the tested budgets.

## Interpretation

MCTS is promising for this simplified Railways environment. On the medium map, the search agent finds stronger plans than the short-sighted greedy baselines, especially by improving delivery count and final score. The cost is runtime: `mcts_250` is much slower than every baseline, so future experiments should report both score and runtime.

The medium map is complex enough for MCTS to show an advantage. The results also suggest that rollout policy matters: greedy rollouts appear useful, but the runtime cost is high. A practical next tuning step would be to test lower rollout depths, mixed rollout policies, or heuristic terminal evaluation.

## Next Step

Recommended next step:

- tune MCTS rollout depth and rollout policy for a better score/runtime trade-off;
- then compare against a Genetic Algorithm if the dissertation schedule allows.
