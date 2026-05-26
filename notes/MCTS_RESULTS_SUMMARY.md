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

## MCTS Tuning Results

### Purpose

The initial MCTS experiment showed that MCTS improves final score but increases runtime. This tuning experiment investigates the score-runtime trade-off and checks whether the current MCTS setup is robust across maps.

### Parameters Tested

- Main tuning map: `toy_medium_map`
- Main tuning episodes: 10
- Iterations: 50, 100
- Rollout depths: 40, 80
- Rollout policies: random for the main tuning run; a smaller random-vs-greedy rollout check was also run
- Action generation: fast
- Max candidate actions: 24
- Fast-vs-full check: `toy_map`, 5 episodes, 20 iterations, rollout depth 30
- Robustness check: `toy_map` and `toy_medium_map`, 10 episodes, 50 and 100 iterations, rollout depth 40

### Main Tuning Findings

Main result from `results/processed/mcts_tuning_summary.csv`:

| Map | Iterations | Depth | Policy | Action Gen | Candidates | Episodes | Mean Final Score | Std | Mean Deliveries | Runtime (s) | Score / Second |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| toy_medium_map | 50 | 40 | random | fast | 24 | 10 | 50.50 | 6.26 | 15.90 | 11.63 | 4.34 |
| toy_medium_map | 50 | 80 | random | fast | 24 | 10 | 49.90 | 5.32 | 15.60 | 11.58 | 4.31 |
| toy_medium_map | 100 | 40 | random | fast | 24 | 10 | 54.30 | 2.87 | 17.10 | 23.11 | 2.35 |
| toy_medium_map | 100 | 80 | random | fast | 24 | 10 | 53.00 | 4.47 | 17.10 | 22.97 | 2.31 |

### Score-Runtime Trade-off

Increasing the iteration budget from 50 to 100 improved mean final score by about 3 to 4 points on `toy_medium_map`, but approximately doubled runtime. The best raw score in the main tuning run was `100 iterations / depth 40`, with mean final score 54.30. The best score-per-second setting was `50 iterations / depth 40`, with score-per-second 4.34.

Rollout depth 80 did not improve mean score over depth 40 in this experiment. Because runtime was also very similar, depth 40 is the cleaner representative setting for future comparisons.

### Rollout Policy

Small rollout-policy tuning result from `results/processed/mcts_rollout_tuning_summary.csv`:

| Map | Iterations | Depth | Policy | Episodes | Mean Final Score | Runtime (s) | Score / Second |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| toy_medium_map | 50 | 40 | random | 3 | 49.67 | 11.01 | 4.51 |
| toy_medium_map | 50 | 40 | greedy_delivery | 3 | 55.33 | 34.02 | 1.63 |
| toy_medium_map | 100 | 40 | random | 3 | 50.33 | 22.42 | 2.24 |
| toy_medium_map | 100 | 40 | greedy_delivery | 3 | 55.00 | 65.32 | 0.84 |

Greedy rollouts improved score in this small sample, but the runtime cost was large. For dissertation reporting, greedy rollout is promising but should be treated as a higher-cost variant rather than the default.

### Fast vs Full Action Generation

Fast candidate generation uses a legal subset of actions. It still applies only valid rule-engine actions, but it does not enumerate every possible delivery path in MCTS planning. This makes medium-map MCTS practical.

Small-map check from `results/processed/mcts_fast_vs_full_summary.csv`:

| Map | Iterations | Depth | Action Gen | Episodes | Mean Final Score | Runtime (s) | Score / Second |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| toy_map | 20 | 30 | fast | 5 | 17.40 | 0.96 | 18.13 |
| toy_map | 20 | 30 | full | 5 | 18.80 | 1.58 | 11.93 |

Full action generation scored slightly higher on the small map, but fast action generation was substantially quicker and had better score-per-second. Full action generation is feasible for small-map checks, but fast generation is the practical option for medium-map experiments.

### Robustness Across Maps

Robustness check from `results/processed/mcts_map_robustness_summary.csv`:

| Map | Iterations | Depth | Policy | Episodes | Mean Final Score | Runtime (s) | Score / Second |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| toy_map | 50 | 40 | random | 10 | 19.70 | 2.10 | 9.38 |
| toy_map | 100 | 40 | random | 10 | 19.80 | 4.02 | 4.92 |
| toy_medium_map | 50 | 40 | random | 10 | 47.20 | 11.30 | 4.18 |
| toy_medium_map | 100 | 40 | random | 10 | 56.00 | 22.73 | 2.46 |

The larger map benefits more from increased MCTS budget. On the small map, 100 iterations adds little score over 50 iterations, which suggests the small map is close to saturated for this MCTS setup.

### Implication for Dissertation

The recommended representative MCTS setting for later comparisons is:

```text
MCTS-100, rollout depth 40, random rollout, fast action generation, 24 candidate actions
```

This setting gives strong performance on the medium map without the much higher runtime of `mcts_250` or greedy rollouts. For score-runtime plots, `MCTS-50` should also be reported as the efficient lower-budget variant.
