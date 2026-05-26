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

## Semi-realistic MCTS Results

Phase 3B reports whether MCTS remains meaningful on a larger and more realistic single-player map.

Command:

```bash
python experiments/run_mcts_experiments.py --map data/semi_realistic_map.json --episodes 10 --iterations-list 50,100 --rollout-depth 60 --rollout-policy random --seed 0 --output results/raw/semi_realistic_mcts_results.csv
```

The semi-realistic MCTS run is intentionally smaller than the medium-map MCTS experiment because the larger action space is expected to increase runtime.

Summary from `results/processed/semi_realistic_mcts_summary.csv`:

| Map | Agent | Episodes | Mean Final Score | Std | Mean Deliveries | Mean Built Edges | Mean Major Line Bonus | Invalid Rate | Terminal Rate | Mean Runtime (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semi_realistic_map | random | 10 | 6.30 | 7.02 | 6.80 | 9.40 | 2.10 | 0.0000 | 1.00 | 0.26 |
| semi_realistic_map | greedy_delivery | 10 | 22.00 | 0.00 | 13.00 | 20.00 | 9.00 | 0.0000 | 1.00 | 0.27 |
| semi_realistic_map | greedy_expansion | 10 | 87.00 | 0.00 | 13.00 | 20.00 | 74.00 | 0.0000 | 1.00 | 2.30 |
| semi_realistic_map | mcts_50 | 10 | 55.00 | 17.94 | 16.70 | 12.10 | 19.60 | 0.0000 | 1.00 | 23.78 |
| semi_realistic_map | mcts_100 | 10 | 64.10 | 26.25 | 15.90 | 12.40 | 33.20 | 0.0000 | 1.00 | 45.07 |

Initial observations:

- MCTS still outperforms `random` and `greedy_delivery` on the semi-realistic map.
- `greedy_expansion` outperforms MCTS in this scenario because it aggressively claims major-line bonuses.
- `mcts_100` improves over `mcts_50`, but runtime roughly doubles.
- MCTS has higher variance on the semi-realistic map, suggesting the larger action space makes planning harder.
- All MCTS runs had zero invalid actions and all episodes terminated normally.

Interpretation:

The semi-realistic map is a useful stress test. It shows that MCTS is not automatically dominant: a well-targeted heuristic can exploit map-specific reward structure more efficiently. This strengthens the dissertation discussion because the model now exposes both MCTS advantages and limitations.

Next implication:

The current MCTS should be treated as a strong but not final search baseline on the semi-realistic map. The most useful follow-up is either a semi-realistic MCTS tuning run with major-line-aware rollout/evaluation, or a Genetic Algorithm that can search over longer-term network construction plans.

## Major-line-aware MCTS

Phase 3C adds an optional MCTS evaluation mode called `major_line_aware`. It keeps the same rule engine and legal-action interface, but changes the rollout evaluation from pure final score to:

```text
final_score
+ major_line_weight * potential_major_line_progress
+ delivery_weight * legal_delivery_count
+ network_weight * built_edge_count
```

The diagnostic experiment on `semi_realistic_map` compared random-rollout MCTS with major-line-aware MCTS:

| Agent | Episodes | Mean Final Score | Std | Mean Major Line Bonus | Mean Runtime (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| greedy_expansion | 10 | 87.00 | 0.00 | 74.00 | 2.27 |
| mcts_50_random | 10 | 48.90 | 23.53 | 16.90 | 23.18 |
| mcts_100_random | 10 | 79.60 | 29.68 | 47.10 | 44.34 |
| mcts_50_majorline | 10 | 92.10 | 12.36 | 70.10 | 23.27 |
| mcts_100_majorline | 10 | 79.80 | 26.19 | 49.60 | 44.87 |

`mcts_50_majorline` closed the gap with `greedy_expansion` and achieved the highest mean final score in this diagnostic run. The result supports the interpretation that MCTS needs domain-aware evaluation for delayed route-completion rewards.
