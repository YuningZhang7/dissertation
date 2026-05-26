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
- score_per_second

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

Run the MCTS validation pipeline:

```bash
python experiments/run_mcts_pipeline.py --map data/toy_medium_map.json --episodes 30 --iterations-list 50,100,250 --seed 0
```

Compare random and greedy rollout policies:

```bash
python experiments/run_mcts_experiments.py --map data/toy_medium_map.json --episodes 5 --iterations-list 50,100 --rollout-policy-list random,greedy_delivery --output results/raw/mcts_rollout_comparison_results.csv
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

### Rollout Policies

- random
- greedy_delivery

### Metrics

- final_score
- raw_score
- deliveries
- built_edges
- bonds
- major_line_bonus
- runtime_seconds

## Phase 2C.6: MCTS Tuning

### Research Questions

1. How does MCTS score change with iteration budget?
2. How does rollout depth affect performance?
3. Does greedy rollout improve score enough to justify runtime?
4. How much speed is gained by fast candidate action generation?
5. Which MCTS configuration gives the best score-runtime trade-off?

### Primary Metrics

- mean_final_score
- mean_runtime_seconds
- score_per_second
- deliveries
- major_line_bonus
- invalid_action_rate
- terminal_rate

### Commands

Run the main tuning experiment:

```bash
python experiments/run_mcts_tuning.py --map data/toy_medium_map.json --episodes 10 --iterations-list 50,100 --rollout-depth-list 40,80 --rollout-policy-list random --action-generation-list fast --max-candidate-actions-list 24 --seed 0
```

Analyse and plot tuning results:

```bash
python experiments/analyse_mcts_tuning.py --input results/raw/mcts_tuning_results.csv
python experiments/plot_mcts_tuning.py --input results/raw/mcts_tuning_results.csv
```

Validate tuning results:

```bash
python experiments/validate_mcts_tuning.py --input results/raw/mcts_tuning_results.csv --episodes 10 --maps toy_medium_map --iterations-list 50,100 --rollout-depth-list 40,80 --rollout-policy-list random --action-generation-list fast --max-candidate-actions-list 24
```

Run fast-vs-full action generation check:

```bash
python experiments/run_mcts_tuning.py --map data/toy_map.json --episodes 5 --iterations-list 20 --rollout-depth-list 30 --rollout-policy-list random --action-generation-list fast,full --seed 0 --output results/raw/mcts_fast_vs_full_results.csv
```

Run map robustness check:

```bash
python experiments/run_mcts_tuning.py --map all --episodes 10 --iterations-list 50,100 --rollout-depth-list 40 --rollout-policy-list random --action-generation-list fast --max-candidate-actions-list 24 --seed 0 --output results/raw/mcts_map_robustness_results.csv
```
