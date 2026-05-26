# Semi-realistic Results Diagnosis

## Motivation

The Phase 3B semi-realistic experiment showed that `greedy_expansion` outperformed the original random-rollout MCTS variants. The most likely reason was major-line reward structure: `greedy_expansion` directly evaluates whether a build action improves future network opportunities and major-line completion, while MCTS with random rollouts often misses delayed major-line rewards.

## Key Question

Is `greedy_expansion` strong because it is generally better, or because the current semi-realistic scoring heavily rewards major-line completion?

## Major-line Sensitivity

Major-line sensitivity experiments were run on `semi_realistic_map` with multipliers `0.0`, `0.5`, `0.75`, and `1.0`.

Baseline agents used 20 episodes per multiplier. MCTS used 5 episodes per multiplier with budgets 50 and 100, rollout depth 60, random rollout, and fast action generation.

| multiplier | random | greedy_delivery | greedy_expansion | mcts_50 | mcts_100 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 3.60 | 13.00 | 12.00 | 33.60 | 39.80 |
| 0.50 | 4.20 | 17.00 | 49.00 | 41.20 | 46.80 |
| 0.75 | 4.40 | 20.00 | 69.00 | 58.00 | 63.40 |
| 1.00 | 4.40 | 22.00 | 87.00 | 54.40 | 77.80 |

Mean major-line bonus:

| multiplier | greedy_delivery | greedy_expansion | mcts_50 | mcts_100 |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 0.50 | 4.00 | 36.00 | 3.20 | 8.80 |
| 0.75 | 7.00 | 56.00 | 35.20 | 29.60 |
| 1.00 | 9.00 | 74.00 | 23.80 | 47.00 |

The sensitivity experiment confirms that major-line reward size strongly affects agent ranking. When major-line bonuses are removed, MCTS clearly beats both greedy agents. As the multiplier increases, `greedy_expansion` rises sharply because it directly targets network expansion and major-line completion.

## MCTS Diagnosis

Random-rollout MCTS may miss long-term structure for several reasons:

- major-line rewards are delayed until a full source-target connection is built;
- random rollouts often fail to complete long routes within the rollout depth;
- fast candidate action generation uses a legal subset of actions for speed, which can limit long-range exploration;
- `greedy_expansion` directly ranks build actions by future delivery opportunities and major-line bonus gain.

This does not mean MCTS is unsuitable. It means the current MCTS needs domain-aware evaluation or rollout guidance to compete with a strong structural heuristic.

## Major-line-aware MCTS

The MCTS evaluation function now supports `major_line_aware` mode:

```text
reward =
    final_score
    + major_line_weight * potential_major_line_progress
    + delivery_weight * legal_delivery_count
    + network_weight * built_edge_count
```

The potential major-line progress term estimates partial progress toward unclaimed major lines by checking how many edges on a shortest available source-target path have already been built.

Major-line-aware MCTS experiment on `semi_realistic_map`, 10 episodes per agent:

| agent | mean_final_score | std_final_score | mean_deliveries | mean_built_edges | mean_major_line_bonus | mean_runtime_seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| random | 9.60 | 14.57 | 6.90 | 9.40 | 4.70 | 0.26 |
| greedy_delivery | 22.00 | 0.00 | 13.00 | 20.00 | 9.00 | 0.26 |
| greedy_expansion | 87.00 | 0.00 | 13.00 | 20.00 | 74.00 | 2.27 |
| mcts_50_random | 48.90 | 23.53 | 16.70 | 11.60 | 16.90 | 23.18 |
| mcts_100_random | 79.60 | 29.68 | 15.90 | 12.10 | 47.10 | 44.34 |
| mcts_50_majorline | 92.10 | 12.36 | 12.60 | 14.10 | 70.10 | 23.27 |
| mcts_100_majorline | 79.80 | 26.19 | 15.10 | 12.80 | 49.60 | 44.87 |

The best result in this diagnostic run was `mcts_50_majorline`, with mean final score 92.10. It outperformed `greedy_expansion` while using a similar runtime to `mcts_50_random`. This suggests that domain-aware evaluation can close the gap created by delayed major-line rewards.

The `mcts_100_majorline` result did not improve over `mcts_100_random` in this sample. This may be due to stochastic variation, interaction between the heuristic and exploration, or the need to tune major-line, delivery, and network weights.

## Implications

- The semi-realistic map is useful because it reveals algorithmic weaknesses that were hidden on smaller maps.
- Major-line rewards are a dominant strategic feature of the current semi-realistic scenario.
- MCTS benefits from domain-aware evaluation; pure random rollout is not enough for delayed route-completion objectives.
- The results support a dissertation discussion about hybrid methods, heuristic rollouts, or GA search over long-term network construction.

## Next Step

Possible next steps:

1. Use `mcts_50_majorline` as the main improved MCTS variant in later experiments.
2. Tune `major_line_weight`, `delivery_weight`, and `network_weight`.
3. Add an exact benchmark on small instances.
4. Implement a Genetic Algorithm for comparison with major-line-aware MCTS.
5. Improve major-line and objective-card rules.
