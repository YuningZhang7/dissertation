# Experiment Plan

## Current Goal

Add exact optimality benchmarking on a micro instance while keeping larger-map evaluation heuristic/search-based.

Current active phase: Phase 3D, small-instance exact benchmark.

## Maps / Scenarios

- `toy_map`: small development map.
- `toy_medium_map`: medium artificial map for stronger baseline comparison.
- `semi_realistic_map`: larger artificial map for stronger external validity and more realistic strategy trade-offs.

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

Run experiments on the semi-realistic map:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --seed 0 --map data/semi_realistic_map.json --output results/raw/semi_realistic_baseline_results.csv
```

Run experiments on all configured maps:

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
python experiments/validate_baselines.py --input results/raw/map_comparison_results.csv --episodes 100 --maps toy_map,toy_medium_map,semi_realistic_map
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

## Phase 3A: Semi-realistic Scenario

### Research Questions

1. Do baseline and MCTS results remain meaningful on a larger map?
2. Does MCTS still outperform greedy baselines when the map is larger?
3. How much does runtime increase?
4. Which simplifications still limit external validity?

### Metrics

- final_score
- runtime_seconds
- deliveries
- bonds
- built_edges
- major_line_bonus

### Commands

Run semi-realistic baseline experiments:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --map data/semi_realistic_map.json --output results/raw/semi_realistic_baseline_results.csv
```

Run semi-realistic MCTS experiments:

```bash
python experiments/run_mcts_experiments.py --map data/semi_realistic_map.json --episodes 10 --iterations-list 50,100 --rollout-depth 60 --rollout-policy random --seed 0 --output results/raw/semi_realistic_mcts_results.csv
```

Analyse and plot:

```bash
python experiments/analyse_results.py --input results/raw/semi_realistic_baseline_results.csv --output results/processed/semi_realistic_baseline_summary.csv
python experiments/plot_results.py --input results/raw/semi_realistic_baseline_results.csv --output-dir results/plots/semi_realistic_baseline
python experiments/analyse_results.py --input results/raw/semi_realistic_mcts_results.csv --output results/processed/semi_realistic_mcts_summary.csv
python experiments/plot_results.py --input results/raw/semi_realistic_mcts_results.csv --output-dir results/plots/semi_realistic_mcts
```

## Phase 3B: Semi-realistic Experiments

The goal is to test whether algorithmic findings from `toy_medium_map` still hold on the larger `semi_realistic_map`.

### Research Questions

1. Do baseline agents still behave meaningfully on a larger map?
2. Does MCTS still outperform greedy baselines on the semi-realistic map?
3. How much does runtime increase on a larger scenario?
4. Does the larger map reveal limitations of the current rules or agents?
5. Is the semi-realistic map suitable for future GA or exact benchmark experiments?

### Commands

Run the full semi-realistic pipeline:

```bash
python experiments/run_semi_realistic_pipeline.py --baseline-episodes 50 --mcts-episodes 10 --mcts-iterations-list 50,100 --seed 0
```

Validate baseline and MCTS outputs separately:

```bash
python experiments/validate_baselines.py --input results/raw/semi_realistic_baseline_results.csv --episodes 50 --maps semi_realistic_map
python experiments/validate_mcts_results.py --input results/raw/semi_realistic_mcts_results.csv --episodes 10 --maps semi_realistic_map --agents random,greedy_delivery,greedy_expansion,mcts_50,mcts_100
```

### Preliminary Findings

- `greedy_expansion` is the strongest semi-realistic baseline because it captures major-line bonuses.
- MCTS beats `random` and `greedy_delivery`, but the current random-rollout setting does not beat `greedy_expansion`.
- Runtime grows substantially on the semi-realistic map, especially for `mcts_100`.
- Invalid actions remain zero and all episodes terminate normally.

## Phase 3C: Semi-realistic Diagnosis

### Research Questions

1. Does major-line bonus size determine agent ranking?
2. Does `greedy_expansion` remain strongest when major-line bonuses are reduced?
3. Can major-line-aware MCTS close the gap?
4. What does this imply about search-based agents in structured railway network problems?

### Commands

Run major-line sensitivity:

```bash
python experiments/run_major_line_sensitivity.py --map data/semi_realistic_map.json --episodes 20 --mcts-episodes 5 --mcts-iterations-list 50,100 --multipliers 0,0.5,0.75,1.0 --seed 0
```

Analyse and plot:

```bash
python experiments/analyse_major_line_sensitivity.py --input results/raw/major_line_sensitivity_results.csv
python experiments/plot_major_line_sensitivity.py --input results/raw/major_line_sensitivity_results.csv
```

Run major-line-aware MCTS:

```bash
python experiments/run_mcts_major_line_experiments.py --map data/semi_realistic_map.json --episodes 10 --iterations-list 50,100 --rollout-depth 60 --seed 0
```

Validate:

```bash
python experiments/validate_major_line_experiments.py --input results/raw/mcts_major_line_results.csv --episodes 10
```

Run the combined diagnosis pipeline:

```bash
python experiments/run_semi_realistic_diagnosis_pipeline.py --episodes 20 --mcts-episodes 5 --mcts-iterations-list 50,100 --multipliers 0,0.5,0.75,1.0 --seed 0
```

### Preliminary Findings

- Major-line bonus size strongly changes agent ranking.
- With major-line bonuses removed, MCTS beats both greedy baselines.
- At full major-line bonus, `greedy_expansion` becomes strong because it directly targets major-line completion.
- `mcts_50_majorline` outperformed `greedy_expansion` in the diagnostic run, suggesting domain-aware MCTS is promising.

## Phase 3D: Small-instance Exact Benchmark

### Research Questions

1. Can exact exhaustive search compute a true optimum on a very small instance?
2. How close are greedy agents and MCTS to the exact optimum?
3. Does the exact benchmark strengthen the interpretation of heuristic results on larger maps?
4. How quickly does exact search become impractical as scenario size grows?

### Commands

Run the exact solver:

```bash
python exact/run_exact_benchmark.py
```

Compare agents to exact optimum:

```bash
python exact/compare_agents_to_exact.py
```

Run exact smoke tests:

```bash
python experiments/smoke_test_exact.py
```

### Preliminary Findings

- `micro_map` exact optimum is 10.
- Exact search expanded 2365 states and used 3886 memo hits.
- `greedy_delivery` and `greedy_expansion` both found the optimum on the micro instance.
- MCTS variants were close to optimal but had small stochastic gaps under the tested budgets.
- RandomAgent remained far from optimal.
