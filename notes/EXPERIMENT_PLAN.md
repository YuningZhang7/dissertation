# Experiment Plan

## Current Goal

Validate baseline agents before implementing advanced AI methods.

## Agents

- RandomAgent
- GreedyDeliveryAgent
- GreedyExpansionAgent

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
```

Run experiments:

```bash
python experiments/run_experiments.py --agent all --episodes 100 --seed 0
```

Analyse results:

```bash
python experiments/analyse_results.py --input results/raw/experiment_results.csv
```

Plot results:

```bash
python experiments/plot_results.py --input results/raw/experiment_results.csv
```

Validate baselines:

```bash
python experiments/validate_baselines.py --input results/raw/experiment_results.csv --episodes 100
```

Run the complete validation pipeline:

```bash
python experiments/run_full_baseline_pipeline.py --episodes 100 --seed 0
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

These baselines will be used later as comparison points for MCTS, Genetic Algorithm, and optional Reinforcement Learning.
