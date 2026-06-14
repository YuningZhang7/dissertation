# Exact Benchmark Results

## Purpose

For small instances, exhaustive search with memoisation can compute the true optimum under the implemented rule abstraction. This provides an optimality benchmark for evaluating the solution quality of greedy agents and MCTS.

For larger maps, the legal action space grows too quickly, so exact search is computationally impractical and heuristic or search-based methods are required.

## Micro-map Design

The `micro_map` scenario is a deliberately small artificial map for exact benchmarking.

- Cities: 5
- Edges: 6
- Major lines: 1
- Goods: 4 initial goods
- Horizon: 4 turns
- Actions per turn: 2
- Voluntary share/bond action: disabled
- Automatic financing during payment: enabled
- End condition: fixed turns

The map is small enough for exhaustive search, but it still contains a strategic trade-off:

- build short routes for immediate deliveries;
- build toward a longer connection from `A` to `D`;
- claim the `A-D` major-line bonus;
- decide whether to spend actions on deliveries or network completion.

## Exact Solver

The exact solver uses the existing simulator interface:

- `get_legal_actions(state)`
- `copy_state(state)`
- `apply_action(state, action)`
- `final_score(state)`
- `is_terminal(state)`

It does not implement a separate game engine. The optimum is therefore computed under the same rule abstraction used by the baseline and MCTS agents.

After supervisor feedback, this benchmark uses the corrected basic-rule action space: issuing shares/bonds is not a legal agent action and does not appear in the exact search tree. Financing is handled internally during payment when automatic financing is enabled.

The solver performs recursive depth-first search over legal actions with memoisation. The canonical state key includes turn, phase, actions remaining, player money, score, bonds, locomotive level, built edges, remaining goods, city empty markers, claimed major lines, and other rule-relevant mutable state.

Branch-and-bound is disabled in this phase. This avoids unsafe pruning and keeps the benchmark exact.

## Exact Result

Command:

```bash
python exact/run_exact_benchmark.py
```

Result:

| metric | value |
| --- | ---: |
| optimal final score | 10 |
| optimal action count | 8 |
| expanded states | 7526 |
| memo hits | 10390 |
| pruned states | 0 |
| runtime seconds | 10.93 |

One optimal action sequence:

1. Build track `A-B`
2. Build track `A-E`
3. Deliver blue from `A` to `B`
4. Deliver red from `B` to `A`
5. Build track `B-C`
6. Build track `C-D`
7. Deliver green from `C` to `D`
8. Deliver yellow from `D` to `C`

This sequence also connects `A` to `D`, claiming the `A-D` major-line bonus.

The optimal sequence contains no `issue_bond` action. Any financing needed by alternative branches is handled internally by the payment rules.

## Agent Comparison

Command:

```bash
python exact/compare_agents_to_exact.py
```

Comparison against the exact optimum:

| agent | episodes | mean score | std | min | max | optimum | absolute gap | relative gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| exact_optimum | 1 | 10.00 | 0.00 | 10.00 | 10.00 | 10.00 | 0.00 | 0.00% |
| random | 30 | 3.00 | 2.51 | -1.00 | 7.00 | 10.00 | 7.00 | 70.00% |
| greedy_delivery | 1 | 10.00 | 0.00 | 10.00 | 10.00 | 10.00 | 0.00 | 0.00% |
| greedy_expansion | 1 | 5.00 | 0.00 | 5.00 | 5.00 | 10.00 | 5.00 | 50.00% |
| mcts_25 | 20 | 8.80 | 1.01 | 7.00 | 10.00 | 10.00 | 1.20 | 12.00% |
| mcts_100 | 20 | 9.25 | 0.79 | 8.00 | 10.00 | 10.00 | 0.75 | 7.50% |
| mcts_25_majorline | 20 | 8.70 | 1.08 | 7.00 | 10.00 | 10.00 | 1.30 | 13.00% |
| mcts_100_majorline | 20 | 9.50 | 0.76 | 8.00 | 10.00 | 10.00 | 0.50 | 5.00% |

## Interpretation

On this micro instance, `greedy_delivery` finds an optimal solution, while `greedy_expansion` underperforms because its expansion-first bias spends effort on network structure before taking enough immediate deliveries. This is useful: the micro benchmark is small enough to expose the exact opportunity cost of heuristic priorities.

MCTS performs close to optimal but does not always find the optimum under the tested budgets. The small gap is useful evidence: stochastic search quality can be quantified against a true optimum on small instances.

Major-line-aware MCTS is competitive but does not consistently dominate original MCTS on `micro_map`. This is acceptable and not a contradiction of the semi-realistic findings. The micro instance is an exact optimality benchmark with only one small major-line objective, so it is not the main scenario for demonstrating the value of major-line-aware search. The semi-realistic map remains the relevant setting for that claim, because it contains a larger delayed major-line reward structure.

RandomAgent performs poorly and has high variance, as expected.

## Dissertation Contribution

This exact benchmark strengthens the experimental story:

- exact search provides ground truth on a small instance;
- greedy and MCTS agents can be measured by optimality gap;
- medium and semi-realistic maps remain necessary because small instances can be too easy for simple heuristics;
- larger scenarios still require heuristic or search-based methods because exhaustive search scales poorly.

This supports the dissertation claim:

> Exact search on small instances shows how far each heuristic/search agent is from the true optimum. This strengthens the experimental evaluation by combining optimality benchmarking on small maps with scalable heuristic evaluation on medium and semi-realistic maps.

## Output Files

Generated locally under ignored `results/` paths:

- `results/exact_benchmark/micro_map_exact_result.json`
- `results/exact_benchmark/micro_map_agent_comparison.csv`
- `results/exact_benchmark/micro_map_agent_comparison.md`
