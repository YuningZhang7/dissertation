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
- Voluntary bonds: disabled
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
| expanded states | 2365 |
| memo hits | 3886 |
| pruned states | 0 |
| runtime seconds | 2.36 |

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

## Agent Comparison

Command:

```bash
python exact/compare_agents_to_exact.py
```

Comparison against the exact optimum:

| agent | episodes | mean score | std | min | max | optimum | absolute gap | relative gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| exact_optimum | 1 | 10.00 | 0.00 | 10.00 | 10.00 | 10.00 | 0.00 | 0.00% |
| random | 30 | 2.77 | 2.69 | 0.00 | 8.00 | 10.00 | 7.23 | 72.33% |
| greedy_delivery | 1 | 10.00 | 0.00 | 10.00 | 10.00 | 10.00 | 0.00 | 0.00% |
| greedy_expansion | 1 | 10.00 | 0.00 | 10.00 | 10.00 | 10.00 | 0.00 | 0.00% |
| mcts_25 | 20 | 9.45 | 0.76 | 8.00 | 10.00 | 10.00 | 0.55 | 5.50% |
| mcts_100 | 20 | 9.40 | 0.60 | 8.00 | 10.00 | 10.00 | 0.60 | 6.00% |
| mcts_25_majorline | 20 | 9.10 | 0.64 | 8.00 | 10.00 | 10.00 | 0.90 | 9.00% |
| mcts_100_majorline | 20 | 9.00 | 0.00 | 9.00 | 9.00 | 10.00 | 1.00 | 10.00% |

## Interpretation

On this micro instance, both greedy agents find an optimal solution. This is expected: the instance is small and the main useful routes are easy for the heuristics to identify.

MCTS performs close to optimal but does not always find the optimum under the tested budgets. The small gap is useful evidence: stochastic search quality can be quantified against a true optimum on small instances.

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
