# Phase 4C Card Experiment Results

## 1. Purpose

Phase 4C compares card-disabled and card-enabled versions of the same single-player simulator using the existing Random, Greedy Delivery, Greedy Expansion, MCTS, and major-line-aware MCTS agents. The experiment asks how the minimal representative card framework changes score, score composition, card-selection behaviour, and runtime under the implemented abstraction.

## 2. Preliminary Pipeline Run

An earlier run used 2 episodes per condition, 5 MCTS iterations, rollout depth 20, and at most 100 steps. It confirmed that the pipeline, metrics, and card-enabled agents worked, but it was not used for dissertation-scale conclusions. Its broad patterns motivated the larger standard run: Random and MCTS selected cards, while the greedy agents ignored cards on the medium and semi-realistic scenarios.

## 3. Standard Experiment Setup

- Maps: `toy_map`, `toy_medium_map`, and `semi_realistic_map`
- Agents: Random, Greedy Delivery, Greedy Expansion, MCTS, and major-line-aware MCTS
- Card modes: disabled and enabled with `data/cards_basic.json`
- Episodes: 30 per map, mode, and agent
- Total episodes: 900
- MCTS iterations: 25
- MCTS rollout depth: 40
- Maximum steps: 500
- Seeds: 0 to 29 for every condition
- Invalid actions: 0 across all episodes
- Local wall-clock runtime: approximately 56 minutes

Generated outputs:

- `results/raw/phase4_standard_card_disabled_results.csv`
- `results/raw/phase4_standard_card_enabled_results.csv`
- `results/summary/phase4_standard_card_comparison_summary.csv`
- `results/summary/phase4_standard_card_comparison_summary.md`
- `results/summary/phase4_standard_card_effect_table.csv`
- `results/summary/phase4_standard_card_effect_table.md`
- `results/summary/phase4_standard_card_usage_table.csv`
- `results/summary/phase4_standard_card_usage_table.md`

## 4. Main Results

| map | agent | cards disabled mean | cards enabled mean | change | cards selected | cards completed |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| toy_map | random | -1.07 | 18.30 | +19.37 | 7.03 | 4.73 |
| toy_map | greedy_delivery | -4.50 | 2.00 | +6.50 | 8.00 | 4.00 |
| toy_map | greedy_expansion | -20.80 | -15.00 | +5.80 | 8.00 | 4.00 |
| toy_map | mcts | 12.43 | 33.33 | +20.90 | 7.93 | 5.63 |
| toy_map | mcts_majorline | 11.70 | 33.77 | +22.07 | 7.80 | 5.53 |
| toy_medium_map | random | 1.43 | 15.80 | +14.37 | 5.57 | 3.30 |
| toy_medium_map | greedy_delivery | 32.00 | 32.00 | +0.00 | 0.00 | 0.00 |
| toy_medium_map | greedy_expansion | -43.00 | -43.00 | +0.00 | 0.00 | 0.00 |
| toy_medium_map | mcts | 41.73 | 47.47 | +5.73 | 6.63 | 4.53 |
| toy_medium_map | mcts_majorline | 42.70 | 48.20 | +5.50 | 6.33 | 4.33 |
| semi_realistic_map | random | -39.67 | -25.47 | +14.20 | 4.87 | 1.93 |
| semi_realistic_map | greedy_delivery | 22.00 | 22.00 | +0.00 | 0.00 | 0.00 |
| semi_realistic_map | greedy_expansion | -7.00 | -7.00 | +0.00 | 0.00 | 0.00 |
| semi_realistic_map | mcts | 32.73 | 31.30 | -1.43 | 5.63 | 2.40 |
| semi_realistic_map | mcts_majorline | 39.80 | 40.13 | +0.33 | 5.07 | 2.27 |

In this experiment, cards improved mean final score for every agent on `toy_map`. Random also improved on both larger maps. The greedy agents selected no cards on `toy_medium_map` or `semi_realistic_map`, so their results were unchanged there. Both MCTS variants improved on `toy_medium_map`; on `semi_realistic_map`, ordinary MCTS declined slightly and major-line-aware MCTS was approximately unchanged.

## 5. Score Decomposition

The MCTS results show why card bonuses should not be interpreted in isolation.

| map | agent | raw score disabled -> enabled | major line disabled -> enabled | operation + end-game cards | financing penalty disabled -> enabled | final change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| toy_map | mcts | 13.00 -> 12.80 | 3.00 -> 3.00 | 18.90 | 3.57 -> 1.37 | +20.90 |
| toy_map | mcts_majorline | 12.07 -> 13.63 | 3.00 -> 3.00 | 18.80 | 3.37 -> 1.67 | +22.07 |
| toy_medium_map | mcts | 27.03 -> 17.37 | 17.87 -> 15.00 | 16.77 | 3.17 -> 1.67 | +5.73 |
| toy_medium_map | mcts_majorline | 27.90 -> 17.70 | 17.87 -> 15.33 | 16.63 | 3.07 -> 1.47 | +5.50 |
| semi_realistic_map | mcts | 24.80 -> 19.87 | 17.50 -> 8.03 | 10.47 | 9.57 -> 7.07 | -1.43 |
| semi_realistic_map | mcts_majorline | 23.47 -> 19.00 | 25.87 -> 18.10 | 9.80 | 9.53 -> 6.77 | +0.33 |

On `toy_map`, card bonuses were largely additive: delivery and major-line performance stayed similar while financing penalties also fell. On `toy_medium_map`, card-enabled MCTS sacrificed raw delivery and some major-line score, but the card bonuses and lower financing penalty more than compensated. On `semi_realistic_map`, the card bonuses did not fully compensate for reduced delivery and major-line performance for ordinary MCTS. This suggests that card actions can redirect search away from strong basic-rule plans when the map presents more competing network objectives.

Card-enabled MCTS runtime increased from 1.33 to 1.90 seconds per episode on `toy_map` and from 1.34 to 1.95 seconds for major-line-aware MCTS. The relative runtime increase was smaller on the larger maps, but the additional card branches still changed which plans were explored.

## 6. Interpretation

- Cards introduced delayed rewards and optional objectives rather than simply adding a fixed score bonus.
- Random selected cards on every map and improved by 14.20 to 19.37 mean points. This reflects broad access to card bonuses, but Random remained weak on `semi_realistic_map`.
- The greedy agents used all eight cards on `toy_map` after their higher-priority actions became exhausted, but selected none on the two larger maps. Their fixed priorities do not estimate delayed card value.
- MCTS used cards across all maps and completed more card objectives than Random in most conditions. This suggests search can coordinate card selection with later actions under the implemented abstraction.
- MCTS did not benefit uniformly. The slight decline on `semi_realistic_map` suggests that increased branching and delayed rewards can offset the available bonus when the search budget is limited.
- Major-line-aware MCTS retained a small positive change on `semi_realistic_map`, but the difference is too small to support a strong superiority claim.

These results provide preliminary evidence that fuller rules make the optimisation problem more complex: the agent must balance immediate delivery, network expansion, financing, major lines, and optional card objectives within the same action budget.

## 7. Limitations

- The deck is a small original representative subset, not the full official card deck.
- The three maps are artificial research scenarios rather than the official map.
- Thirty episodes reduce noise but do not eliminate sampling uncertainty, especially for MCTS.
- Existing greedy agents and MCTS evaluation are not card-aware.
- MCTS used 25 iterations; different budgets may change the balance between card value and branching cost.
- The experiment concerns the implemented single-player abstraction, not the full official multiplayer game.
- Runtime values are machine-dependent.

## 8. Next Step

Phase 4D should test targeted card-aware improvements rather than adding unrelated algorithms. The clearest candidates are a card-aware greedy baseline, card-aware MCTS evaluation features, or a card-prioritised rollout policy. A stronger MCTS-only `mcts100` profile can first test whether additional search budget resolves the slight `semi_realistic_map` decline before changing the agent design.
