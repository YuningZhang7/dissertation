# Phase 4C Preliminary Card Experiment Results

## Experiment Setup

This preliminary run compared card-disabled and card-enabled modes on:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Agents:

- Random
- Greedy Delivery
- Greedy Expansion
- MCTS
- Major-line-aware MCTS

Each map, mode, and agent combination used 2 episodes. MCTS used 5 iterations and rollout depth 20. These settings were intentionally small so the full pipeline could be verified quickly; the results are not final dissertation-scale estimates.

The card-enabled mode used `data/cards_basic.json`. The card-disabled mode used the same simulator with `card_path=None`. All 60 episodes reported zero invalid actions.

## Preliminary Score Changes

| map | agent | cards disabled | cards enabled | change | cards selected | cards completed |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| toy_map | random | -10.0 | 4.0 | +14.0 | 6.5 | 4.0 |
| toy_map | greedy_delivery | -5.5 | 2.0 | +7.5 | 8.0 | 4.0 |
| toy_map | greedy_expansion | -21.0 | -15.0 | +6.0 | 8.0 | 4.0 |
| toy_map | mcts | 14.0 | 31.5 | +17.5 | 7.0 | 4.5 |
| toy_map | mcts_majorline | 9.0 | 28.5 | +19.5 | 6.5 | 4.0 |
| toy_medium_map | random | 11.5 | 17.5 | +6.0 | 5.5 | 3.5 |
| toy_medium_map | greedy_delivery | 32.0 | 32.0 | 0.0 | 0.0 | 0.0 |
| toy_medium_map | greedy_expansion | -43.0 | -43.0 | 0.0 | 0.0 | 0.0 |
| toy_medium_map | mcts | 35.5 | 30.0 | -5.5 | 6.0 | 3.5 |
| toy_medium_map | mcts_majorline | 13.0 | 31.0 | +18.0 | 7.5 | 5.5 |
| semi_realistic_map | random | -25.5 | -9.5 | +16.0 | 5.0 | 2.5 |
| semi_realistic_map | greedy_delivery | 22.0 | 22.0 | 0.0 | 0.0 | 0.0 |
| semi_realistic_map | greedy_expansion | -7.0 | -7.0 | 0.0 | 0.0 | 0.0 |
| semi_realistic_map | mcts | -6.0 | 16.5 | +22.5 | 7.0 | 3.5 |
| semi_realistic_map | mcts_majorline | 15.5 | 24.0 | +8.5 | 6.0 | 2.5 |

## Interpretation

- Card-enabled mode changed both score composition and action choice for Random and MCTS agents.
- On `toy_map`, every tested agent selected cards and mean final scores increased in this small sample.
- On `toy_medium_map` and `semi_realistic_map`, the two greedy agents selected no cards. Their existing priorities continued to choose build, delivery, or upgrade actions while those actions remained available.
- MCTS selected cards across all maps. The card-enabled ordinary MCTS score improved strongly on `semi_realistic_map`, but declined on `toy_medium_map` in this two-episode sample. This is consistent with cards adding useful options while also increasing branching and planning difficulty.
- Major-line-aware MCTS gained in all three card-enabled comparisons in this preliminary run, although the sample is too small for a strong claim.
- End-game cards contributed substantially when agents selected most of the small deck. Financing penalties remained an important counterweight, so higher bonus scores did not always translate directly into equally large final-score gains.

## Limitations

- Two episodes per condition are insufficient for stable statistical conclusions.
- MCTS used only 5 iterations, much lower than the main dissertation experiments.
- The card deck is a small original representative subset, not the official deck.
- Existing greedy agents are not card-aware, so zero card selection reflects their current priority ordering rather than evidence that cards have no value.
- The same basic card definitions are used across maps even when some network-objective city IDs are map-specific abstractions.

## Next Step Recommendation

Run a larger Phase 4C experiment with more episodes and representative MCTS budgets. Report score decomposition and card-selection frequency alongside final score. Only after those results should Phase 4D consider card-aware greedy priorities, card-aware MCTS evaluation, or card-prioritised rollout policies.
