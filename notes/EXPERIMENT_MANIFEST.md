# Experiment Manifest

This manifest records the main experiment evidence currently available in the repository. It is intended to support dissertation traceability: what was run, how to reproduce it, where outputs are stored, and which notes interpret the results.

The project remains a single-player optimisation abstraction. It does not claim to implement the full official game.

## Exact Benchmark

Purpose: compute an exact optimum on a deliberately tiny `micro_map` instance and compare heuristic/search agents against that optimum.

Command:

```bash
python exact/run_exact_benchmark.py
python exact/compare_agents_to_exact.py
```

Maps:

- `micro_map`

Agents:

- exact solver
- random
- greedy delivery
- greedy expansion
- MCTS 25
- MCTS 100
- major-line-aware MCTS 25
- major-line-aware MCTS 100

Settings:

- Card mode: disabled by default
- Search: exhaustive exact search with memoisation
- Output optimum: 10
- Optimal action count: 8

Output files:

- `results/exact_benchmark/micro_map_exact_result.json`
- `results/exact_benchmark/micro_map_agent_comparison.csv`
- `results/exact_benchmark/micro_map_agent_comparison.md`

Notes:

- `notes/EXACT_BENCHMARK_RESULTS.md`

## Baseline Agents

Purpose: compare the basic non-search agents on the configured maps under the basic-rule simulator.

Command:

```bash
python experiments/run_experiments.py --agent all --episodes 100 --map all --output results/raw/map_comparison_results.csv
python experiments/analyse_results.py --input results/raw/map_comparison_results.csv --output results/processed/summary_by_map_agent.csv
```

Maps:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Agents:

- random
- greedy delivery
- greedy expansion

Settings:

- Card mode: disabled unless `--cards basic` is explicitly passed
- Seeds: controlled by the experiment script seed argument
- Maximum steps: controlled by `--max-steps`

Output files:

- `results/raw/map_comparison_results.csv`
- `results/processed/summary_by_map_agent.csv`
- related plots under `results/plots/`

Notes:

- `notes/BASELINE_RESULTS_SUMMARY.md`
- `notes/EXPERIMENT_PLAN.md`

## MCTS and Major-Line-Aware MCTS

Purpose: evaluate MCTS performance, MCTS iteration budgets, rollout settings, and major-line-aware evaluation on the medium and semi-realistic scenarios.

Representative commands:

```bash
python experiments/run_mcts_experiments.py --map data/toy_medium_map.json --episodes 30 --iterations-list 50,100,250 --seed 0
python experiments/run_mcts_major_line_experiments.py --map data/semi_realistic_map.json --episodes 10 --iterations-list 50,100 --rollout-depth 60 --seed 0
```

Maps:

- `toy_medium_map`
- `semi_realistic_map`
- additional smoke/tuning maps as documented in the MCTS notes

Agents:

- MCTS
- major-line-aware MCTS

Settings:

- Card mode: disabled for Phase 3 MCTS experiments
- Iterations and rollout depth vary by script arguments
- Major-line-aware mode uses `evaluation_mode="major_line_aware"`

Output files:

- `results/raw/mcts_experiment_results.csv`
- `results/processed/mcts_summary_by_map_agent.csv`
- `results/raw/mcts_major_line_results.csv`
- `results/processed/mcts_major_line_summary.csv`
- plots under `results/plots/mcts*/`

Notes:

- `notes/MCTS_RESULTS_SUMMARY.md`
- `notes/SEMI_REALISTIC_DIAGNOSIS.md`
- `notes/SEMI_REALISTIC_RESULTS_SUMMARY.md`

## Phase 4 Card Framework Experiments

Purpose: verify that the minimal representative operation-card framework can be toggled on/off and that existing agents still run without invalid actions.

Command:

```bash
python experiments/run_phase4_card_experiments.py --profile quick
python experiments/validate_phase4_card_results.py --profile quick
```

Maps:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Agents:

- random
- greedy delivery
- greedy expansion
- MCTS
- major-line-aware MCTS

Settings:

- Quick profile: 2 episodes
- MCTS iterations: 5
- MCTS rollout depth: 20
- Card modes: disabled and enabled with `data/cards_basic.json`

Output files:

- `results/raw/phase4_quick_card_disabled_results.csv`
- `results/raw/phase4_quick_card_enabled_results.csv`
- `results/summary/phase4_quick_card_comparison_summary.csv`
- `results/summary/phase4_quick_card_comparison_summary.md`
- `results/summary/phase4_quick_card_effect_table.csv`
- `results/summary/phase4_quick_card_usage_table.csv`

Notes:

- `notes/CARD_FRAMEWORK.md`
- `notes/PHASE4_EXPERIMENT_PLAN.md`

## Phase 4C Standard Card Experiments

Purpose: compare card-disabled and card-enabled play under the existing non-card-aware agents.

Command:

```bash
python experiments/run_phase4_card_experiments.py --profile standard
python experiments/validate_phase4_card_results.py --profile standard
```

Maps:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Agents:

- random
- greedy delivery
- greedy expansion
- MCTS
- major-line-aware MCTS

Settings:

- Episodes: 30 per map, card mode, and agent
- Seeds: 0 to 29
- MCTS iterations: 25
- MCTS rollout depth: 40
- Max steps: 500
- Card modes: disabled and enabled with `data/cards_basic.json`

Output files:

- `results/raw/phase4_standard_card_disabled_results.csv`
- `results/raw/phase4_standard_card_enabled_results.csv`
- `results/summary/phase4_standard_card_comparison_summary.csv`
- `results/summary/phase4_standard_card_comparison_summary.md`
- `results/summary/phase4_standard_card_effect_table.csv`
- `results/summary/phase4_standard_card_effect_table.md`
- `results/summary/phase4_standard_card_usage_table.csv`
- `results/summary/phase4_standard_card_usage_table.md`

Notes:

- `notes/PHASE4_CARD_RESULTS_SUMMARY.md`
- `notes/PHASE4_CARD_DISCUSSION_POINTS.md`

## Phase 4C MCTS100 Budget Diagnostic

Purpose: test whether increasing MCTS budget alone resolves the card-enabled branching trade-off observed in Phase 4C.

Command:

```bash
python experiments/run_phase4_card_experiments.py --profile mcts100 --episodes 10
python experiments/validate_phase4_card_results.py --profile mcts100
python experiments/compare_phase4_mcts_budget.py
```

Maps:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Agents:

- random
- greedy delivery
- greedy expansion
- MCTS
- major-line-aware MCTS

Settings:

- Episodes: 10 per map, card mode, and agent in the completed local run
- Seeds: 0 to 9
- MCTS iterations: 100
- MCTS rollout depth: 80
- Max steps: 500
- Card modes: disabled and enabled with `data/cards_basic.json`

Output files:

- `results/raw/phase4_mcts100_card_disabled_results.csv`
- `results/raw/phase4_mcts100_card_enabled_results.csv`
- `results/summary/phase4_mcts100_card_comparison_summary.csv`
- `results/summary/phase4_mcts100_card_comparison_summary.md`
- `results/summary/phase4_mcts100_card_effect_table.csv`
- `results/summary/phase4_mcts100_card_usage_table.csv`
- `results/summary/phase4_mcts_budget_comparison.csv`
- `results/summary/phase4_mcts_budget_comparison.md`

Notes:

- `notes/PHASE4_CARD_RESULTS_SUMMARY.md`
- `notes/PHASE4_CARD_DISCUSSION_POINTS.md`

## Phase 4D Card-Aware Agent Experiments

Purpose: test whether lightweight card-aware heuristics improve card-enabled play after Phase 4C.

Command:

```bash
python experiments/run_phase4_card_aware_experiments.py
python experiments/compare_phase4d_to_phase4c.py
```

Maps:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Agents:

- greedy delivery
- greedy expansion
- card-aware greedy
- MCTS
- major-line-aware MCTS
- MCTS with card-aware rollout
- major-line-aware MCTS with card-aware rollout

Settings:

- Episodes: 30 per map and agent
- Seeds: 0 to 29
- MCTS iterations: 25
- MCTS rollout depth: 40
- Max steps: 500
- Card mode: enabled with `data/cards_basic.json`

Output files:

- `results/raw/phase4d_card_aware_results.csv`
- `results/summary/phase4d_card_aware_summary.csv`
- `results/summary/phase4d_card_aware_summary.md`
- `results/summary/phase4d_vs_phase4c_comparison.csv`
- `results/summary/phase4d_vs_phase4c_comparison.md`

Notes:

- `notes/PHASE4D_CARD_AWARE_AGENT_PLAN.md`
- `notes/PHASE4D_CARD_AWARE_RESULTS.md`

## Dissertation Evidence Package

Purpose: validate and package the completed experimental evidence for dissertation writing.

Commands:

```bash
python experiments/validate_all_results.py
python experiments/generate_dissertation_figures.py
python experiments/export_dissertation_tables.py
```

Output files:

- `results/figures/*.png`
- `results/tables/*.md`
- `results/tables/*.tex`

Notes:

- `notes/DISSERTATION_RESULTS_OUTLINE.md`
- `notes/PROJECT_STATUS_FINAL.md`
