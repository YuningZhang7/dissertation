# Experiment Plan

## Current Goal

Validate baseline agents across multiple artificial maps and compare them with the first search-based agent before implementing Genetic Algorithms or Reinforcement Learning.

## Maps / Scenarios

- `toy_map`: small development map.
- `toy_medium_map`: medium artificial map for stronger baseline comparison.

## Purpose of Medium Map

The small toy map is useful for debugging but may be too simple to distinguish greedy strategies. The medium map is intended to create more meaningful strategic trade-offs before implementing MCTS or other advanced AI methods.

## Agents

- RandomAgent
- GreedyDeliveryAgent
- GreedyExpansionAgent
- MCTSAgent

## Metrics

- final_score
- raw_score
- bonds
- deliveries
- built_edges
- major_line_bonus
- empty_markers
- invalid_actions
- terminal_rate
- runtime_seconds

## Commands

Run tests:

```bash
python experiments/smoke_test_rules.py
python experiments/smoke_test_agents.py
python experiments/smoke_test_maps.py
```

Run experiments on the small map:

```bash
python experiments/run_experiments.py --agent all --episodes 100 --seed 0 --map data/toy_map.json
```

Run experiments on the medium map:

```bash
python experiments/run_experiments.py --agent all --episodes 100 --seed 0 --map data/toy_medium_map.json
```

Run experiments on both maps:

```bash
python experiments/run_experiments.py --agent all --episodes 100 --seed 0 --map all --output results/raw/map_comparison_results.csv
```

Analyse results:

```bash
python experiments/analyse_results.py --input results/raw/map_comparison_results.csv
```

Plot results:

```bash
python experiments/plot_results.py --input results/raw/map_comparison_results.csv
```

Validate baselines:

```bash
python experiments/validate_baselines.py --input results/raw/map_comparison_results.csv --episodes 100 --maps toy_map,toy_medium_map
```

Run the complete validation pipeline:

```bash
python experiments/run_full_baseline_pipeline.py --episodes 100 --seed 0 --map all --output results/raw/map_comparison_results.csv
```

Run MCTS experiments:

```bash
python experiments/run_mcts_experiments.py --map data/toy_medium_map.json --episodes 30 --iterations-list 50,100,250 --seed 0
```

## Interpretation Plan

Compare baseline agents by:

1. Mean final score.
2. Score variance.
3. Number of deliveries.
4. Network size.
5. Bonds used.
6. Major line bonus.
7. Runtime.
8. Invalid action rate.

The medium map should show whether simple greedy strategies are still indistinguishable. These baselines will be used later as comparison points for MCTS, Genetic Algorithm, and optional Reinforcement Learning.

## Phase 2C: MCTS Experiments

The MCTS agent will be compared against RandomAgent, GreedyDeliveryAgent, and GreedyExpansionAgent.

### Research Questions

1. Does MCTS outperform simple greedy baselines?
2. How does MCTS performance change with the number of iterations?
3. What is the trade-off between final score and runtime?
4. Does MCTS benefit more on the medium map than on the small map?

### Planned Budgets

- MCTS-50
- MCTS-100
- MCTS-250

### Metrics

- final_score
- raw_score
- deliveries
- built_edges
- bonds
- major_line_bonus
- runtime_seconds
