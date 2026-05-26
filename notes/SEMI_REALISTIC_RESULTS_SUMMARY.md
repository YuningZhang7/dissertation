# Semi-realistic Scenario Results Summary

## Experiment Setup

- Map: `semi_realistic_map`
- Baseline episodes: 50 per agent
- MCTS episodes: 10 per agent
- Seed: 0
- MCTS budgets: 50 and 100 iterations
- Rollout policy: random
- Rollout depth: 60
- Action generation: fast candidate actions
- Rules config: `rules_config`

## Baseline Summary Table

Summary from `results/processed/semi_realistic_baseline_summary.csv`:

| agent | episodes | mean_final_score | std_final_score | mean_deliveries | mean_built_edges | mean_bonds | mean_major_line_bonus | invalid_action_rate | terminal_rate | mean_runtime_seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random | 50 | 3.84 | 6.13 | 5.98 | 8.58 | 4.26 | 1.04 | 0.0000 | 1.00 | 0.25 |
| greedy_delivery | 50 | 22.00 | 0.00 | 13.00 | 20.00 | 0.00 | 9.00 | 0.0000 | 1.00 | 0.27 |
| greedy_expansion | 50 | 87.00 | 0.00 | 13.00 | 20.00 | 0.00 | 74.00 | 0.0000 | 1.00 | 2.27 |

## MCTS Summary Table

Summary from `results/processed/semi_realistic_mcts_summary.csv`:

| agent | episodes | mean_final_score | std_final_score | mean_deliveries | mean_built_edges | mean_bonds | mean_major_line_bonus | invalid_action_rate | terminal_rate | mean_runtime_seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random | 10 | 6.30 | 7.02 | 6.80 | 9.40 | 4.50 | 2.10 | 0.0000 | 1.00 | 0.26 |
| greedy_delivery | 10 | 22.00 | 0.00 | 13.00 | 20.00 | 0.00 | 9.00 | 0.0000 | 1.00 | 0.27 |
| greedy_expansion | 10 | 87.00 | 0.00 | 13.00 | 20.00 | 0.00 | 74.00 | 0.0000 | 1.00 | 2.30 |
| mcts_50 | 10 | 55.00 | 17.94 | 16.70 | 12.10 | 0.20 | 19.60 | 0.0000 | 1.00 | 23.78 |
| mcts_100 | 10 | 64.10 | 26.25 | 15.90 | 12.40 | 0.20 | 33.20 | 0.0000 | 1.00 | 45.07 |

## Initial Observations

- `greedy_expansion` was the strongest baseline, with mean final score 87.00.
- MCTS outperformed `random` and `greedy_delivery` on the semi-realistic map.
- MCTS did not outperform `greedy_expansion`; the expansion heuristic exploited major-line bonuses more directly.
- Runtime increased substantially on the larger scenario: `mcts_100` averaged 45.07 seconds per episode.
- MCTS delivered more goods than the greedy baselines, but it built fewer edges and claimed less major-line bonus than `greedy_expansion`.
- Bond use stayed low for deterministic agents and MCTS; random used more bonds.
- All episodes terminated normally.
- Invalid actions were zero for every agent.

## Comparison with Medium Map

- On `toy_medium_map`, MCTS clearly outperformed both greedy baselines.
- On `semi_realistic_map`, MCTS still improved over `random` and `greedy_delivery`, but `greedy_expansion` became stronger because the larger map contains much larger major-line rewards.
- Runtime increased sharply on the semi-realistic map. For example, `mcts_100` rose from about 22 seconds per episode on the medium-map experiment to about 45 seconds on the semi-realistic map.
- The larger map therefore exposes a useful limitation: random-rollout MCTS can miss long-term structure that a targeted expansion heuristic captures.

## Interpretation

The semi-realistic map increases scenario complexity by adding more cities, edges, regional bottlenecks, grey cities, and major-line objectives. The results suggest that the scenario is suitable for dissertation experiments because it distinguishes strategy styles more clearly than the smaller maps.

MCTS remains useful because it substantially improves on random and short-sighted delivery greed. However, it is not automatically dominant. A simple heuristic designed around expansion and major-line completion can outperform the current MCTS configuration. This is useful experimentally because it motivates further tuning, hybrid rollout policies, or a later Genetic Algorithm rather than presenting MCTS as a solved answer.

## Limitations

- The map is still artificial rather than an official board map.
- Full official track-tile placement rules are not implemented.
- Operation cards and Rail Baron cards are not implemented.
- Multiplayer auction, blocking, and opponent-owned track scoring remain excluded.
- MCTS uses fast candidate action generation, which considers a legal subset rather than all legal actions.

## Next Step

Recommended next steps:

1. Tune MCTS on the semi-realistic map, especially rollout policy and major-line-aware evaluation.
2. Add an exact or branch-and-bound benchmark for very small instances.
3. Implement a Genetic Algorithm for comparison with MCTS and greedy expansion.
4. Improve rule fidelity around income, bonds, urbanize, and objective cards.
