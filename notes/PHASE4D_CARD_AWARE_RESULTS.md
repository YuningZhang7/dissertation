# Phase 4D Card-Aware Agent Results

## 1. Purpose

Phase 4D tests whether simple card-aware guidance improves performance after the Phase 4C card-enabled baseline. It adds:

- `CardAwareGreedyAgent`
- MCTS with `rollout_policy="card_aware"`

The tree policy, UCB rule, action interface, card framework, financing model, and exact benchmark setup are otherwise unchanged.

## 2. Experiment Setup

- Maps: `toy_map`, `toy_medium_map`, and `semi_realistic_map`
- Card mode: enabled with `data/cards_basic.json`
- Agents: `greedy_delivery`, `greedy_expansion`, `card_aware_greedy`, `mcts`, `mcts_majorline`, `mcts_card_rollout`, `mcts_majorline_card_rollout`
- Episodes: 30 per map and agent
- Total episodes: 630
- MCTS iterations: 25
- MCTS rollout depth: 40
- Maximum steps: 500
- Seeds: 0 to 29 for every condition
- Invalid actions: 0 across all summary rows
- Local wall-clock runtime: approximately 90 minutes

Generated outputs:

- `results/raw/phase4d_card_aware_results.csv`
- `results/summary/phase4d_card_aware_summary.csv`
- `results/summary/phase4d_card_aware_summary.md`
- `results/summary/phase4d_vs_phase4c_comparison.csv`
- `results/summary/phase4d_vs_phase4c_comparison.md`

## 3. Main Phase 4D Results

| map | agent | mean final | raw | major line | operation cards | end cards | financing penalty | cards selected | cards completed | runtime (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| toy_map | greedy_delivery | 2.00 | 9.00 | 3.00 | 6.00 | 8.00 | 24.00 | 8.00 | 4.00 | 0.0052 |
| toy_map | greedy_expansion | -15.00 | 9.00 | 3.00 | 6.00 | 8.00 | 41.00 | 8.00 | 4.00 | 0.0431 |
| toy_map | card_aware_greedy | 14.70 | 14.70 | 3.00 | 12.00 | 5.00 | 20.00 | 7.00 | 6.00 | 0.0181 |
| toy_map | mcts | 34.63 | 14.07 | 3.00 | 11.00 | 8.00 | 1.43 | 7.90 | 5.63 | 1.9305 |
| toy_map | mcts_card_rollout | 40.67 | 21.17 | 3.00 | 12.00 | 8.00 | 3.50 | 7.97 | 5.97 | 3.4052 |
| toy_map | mcts_majorline | 34.47 | 13.97 | 3.00 | 10.90 | 8.00 | 1.40 | 7.70 | 5.50 | 1.9707 |
| toy_map | mcts_majorline_card_rollout | 40.57 | 21.13 | 3.00 | 12.00 | 8.00 | 3.57 | 7.97 | 5.97 | 3.4849 |
| toy_medium_map | greedy_delivery | 32.00 | 13.00 | 19.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0745 |
| toy_medium_map | greedy_expansion | -43.00 | 2.00 | 19.00 | 0.00 | 0.00 | 64.00 | 0.00 | 0.00 | 1.1942 |
| toy_medium_map | card_aware_greedy | 23.00 | 2.00 | 19.00 | 12.00 | 5.00 | 15.00 | 7.00 | 6.00 | 0.2142 |
| toy_medium_map | mcts | 48.13 | 17.20 | 15.73 | 8.50 | 8.00 | 1.30 | 6.63 | 4.50 | 6.8093 |
| toy_medium_map | mcts_card_rollout | 60.53 | 28.87 | 16.57 | 9.77 | 8.00 | 2.67 | 6.30 | 4.17 | 15.6329 |
| toy_medium_map | mcts_majorline | 48.03 | 18.37 | 14.00 | 9.37 | 8.00 | 1.70 | 6.70 | 4.60 | 7.3555 |
| toy_medium_map | mcts_majorline_card_rollout | 61.53 | 29.63 | 15.93 | 9.97 | 8.00 | 2.00 | 6.43 | 4.37 | 15.9524 |
| semi_realistic_map | greedy_delivery | 22.00 | 13.00 | 9.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.2655 |
| semi_realistic_map | greedy_expansion | -7.00 | 0.00 | 74.00 | 0.00 | 0.00 | 81.00 | 0.00 | 0.00 | 7.4389 |
| semi_realistic_map | card_aware_greedy | 55.00 | 2.00 | 74.00 | 6.00 | 5.00 | 32.00 | 5.00 | 4.00 | 0.7682 |
| semi_realistic_map | mcts | 30.50 | 17.60 | 9.60 | 2.60 | 7.97 | 7.27 | 5.73 | 2.53 | 14.2114 |
| semi_realistic_map | mcts_card_rollout | 93.80 | 26.20 | 57.10 | 4.30 | 8.00 | 1.80 | 5.40 | 3.07 | 41.5070 |
| semi_realistic_map | mcts_majorline | 33.77 | 17.73 | 14.67 | 2.10 | 7.90 | 8.63 | 5.00 | 2.13 | 15.5830 |
| semi_realistic_map | mcts_majorline_card_rollout | 72.20 | 22.63 | 37.60 | 4.80 | 8.00 | 0.83 | 5.50 | 3.27 | 42.1746 |

## 4. Phase 4D vs Phase 4C

The comparison below uses the Phase 4C standard card-enabled baselines.

| map | comparison | baseline score | new score | delta | baseline cards selected | new cards selected | baseline cards completed | new cards completed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| toy_map | card-aware greedy vs greedy delivery | 2.00 | 14.70 | +12.70 | 8.00 | 7.00 | 4.00 | 6.00 |
| toy_map | card-aware greedy vs greedy expansion | -15.00 | 14.70 | +29.70 | 8.00 | 7.00 | 4.00 | 6.00 |
| toy_map | card-aware MCTS rollout vs MCTS | 33.33 | 40.67 | +7.33 | 7.93 | 7.97 | 5.63 | 5.97 |
| toy_map | card-aware major-line rollout vs major-line MCTS | 33.77 | 40.57 | +6.80 | 7.80 | 7.97 | 5.53 | 5.97 |
| toy_medium_map | card-aware greedy vs greedy delivery | 32.00 | 23.00 | -9.00 | 0.00 | 7.00 | 0.00 | 6.00 |
| toy_medium_map | card-aware greedy vs greedy expansion | -43.00 | 23.00 | +66.00 | 0.00 | 7.00 | 0.00 | 6.00 |
| toy_medium_map | card-aware MCTS rollout vs MCTS | 47.47 | 60.53 | +13.07 | 6.63 | 6.30 | 4.53 | 4.17 |
| toy_medium_map | card-aware major-line rollout vs major-line MCTS | 48.20 | 61.53 | +13.33 | 6.33 | 6.43 | 4.33 | 4.37 |
| semi_realistic_map | card-aware greedy vs greedy delivery | 22.00 | 55.00 | +33.00 | 0.00 | 5.00 | 0.00 | 4.00 |
| semi_realistic_map | card-aware greedy vs greedy expansion | -7.00 | 55.00 | +62.00 | 0.00 | 5.00 | 0.00 | 4.00 |
| semi_realistic_map | card-aware MCTS rollout vs MCTS | 31.30 | 93.80 | +62.50 | 5.63 | 5.40 | 2.40 | 3.07 |
| semi_realistic_map | card-aware major-line rollout vs major-line MCTS | 40.13 | 72.20 | +32.07 | 5.07 | 5.50 | 2.27 | 3.27 |

## 5. Interpretation

Card-aware greedy is useful but map-dependent. It improves strongly over greedy expansion on all maps and over greedy delivery on `toy_map` and `semi_realistic_map`. On `toy_medium_map`, however, it scores 23.00 compared with greedy delivery's 32.00. The card-aware greedy heuristic selected and completed cards, but it sacrificed too much direct delivery score on that map.

Card-aware MCTS rollout improves all three tested scenarios. The improvement is especially large on `semi_realistic_map`, where ordinary Phase 4C MCTS had struggled to turn card selection into stronger overall plans. The card-aware rollout appears to guide search toward plans that preserve more major-line value while still completing card objectives.

The runtime cost is substantial. On `semi_realistic_map`, ordinary MCTS averaged 14.21 seconds per episode in this run, while card-aware rollout averaged 41.51 seconds. Major-line-aware MCTS rose from 15.58 seconds to 42.17 seconds with the card-aware rollout. This is a clear score-runtime trade-off rather than a free improvement.

## 6. Dissertation Use

These results support the Phase 4 argument that adding cards changes the simulator from a direct delivery-and-network optimisation task into a richer sequential optimisation problem with delayed objectives. Simple greedy priorities can miss or overvalue these objectives, while MCTS benefits from rollout guidance that recognises card completion opportunities.

The results should still be framed as evidence under the implemented abstraction, not as claims about solving the full official board game. The deck is small and original, the maps are artificial, and the card-aware rollout is a heuristic baseline rather than a fully tuned card-aware search algorithm.
