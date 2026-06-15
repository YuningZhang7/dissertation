# Railways of the World AI Simulator

## Overview

This project is a local visual simulator for a simplified single-player version of Railways of the World. It is intended as a testbed for future AI and optimisation strategies.

The current version is Phase 4: minimal card framework and fuller-rule foundation.

## Current Development Stage

The project currently has a corrected basic-rule simulator, baseline agents, MCTS agents, an exact-search benchmark on micro instances, and a minimal representative card framework for fuller-rule modelling.

## Supervisor Feedback Corrections

The basic-rule action model has been corrected after supervisor feedback:

- The simulator has no fixed player starting city, home city, train position, or moving train token.
- Goods can be delivered from any source city with the required good to any demanding destination city if a valid built route exists.
- Issuing shares/bonds is not exposed as an agent action. Financing is handled internally during payment when automatic financing is enabled.
- The code still uses `bonds` naming in some fields for compatibility, but it currently approximates the share certificate financing mechanism.
- Connected track building remains configurable as a simplifying network-contiguity assumption, not as an official start-point rule.

## Current Rule Coverage

This version is a single-player rule-development prototype. It is not yet a full official implementation of Railways of the World. The current goal is to preserve the core local rules needed for optimisation experiments, while excluding player-vs-player interaction for now.

See [notes/RULES_COVERAGE.md](notes/RULES_COVERAGE.md).

## Model Validity

The simulator is a defined single-player optimisation abstraction, not a claim to fully reproduce the official board game.

See [notes/MODEL_VALIDITY.md](notes/MODEL_VALIDITY.md).

## Scenario Design

The project now includes four self-created scenarios:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`
- `micro_map`

See [notes/SCENARIO_DESIGN.md](notes/SCENARIO_DESIGN.md).

## Implemented Core Rules

- Turn structure with action and income phases
- Configurable actions per turn
- Configurable connected track-building restriction after the first built edge
- Explicit route-based goods delivery actions
- Upgrade engine
- Internal share/bond financing during payments
- Financing interest/dividend during income
- Score-based income phase
- Basic final scoring
- Empty city markers
- Fixed-turn and empty-city-marker end condition modes
- Simplified urbanize action
- Major-line loading, claiming, and final-score bonus support
- Minimal representative operation-card framework:
  - immediate cash cards
  - delivery objective cards
  - network objective cards
  - end-game scoring cards
- AI-ready environment interface

## Not Yet Implemented

- Full official map
- Full individual track tile placement
- Full official operation-card deck
- Full Rail Baron / Tycoon objective-card system
- Multiplayer auction and interaction
- Opponent-owned track scoring
- Genetic Algorithm and Reinforcement Learning agents

## Running the Streamlit Demo

From the repository root:

```bash
python -m streamlit run app.py
```

or:

```bash
python run_app.py
```

The app entry point is always `app.py`. Do not run markdown files such as prompt notes or Codex task instructions.

If the page shows a markdown prompt beginning with `Codex Task`, you are not running the simulator app. Stop Streamlit with `Ctrl+C` and run:

```bash
python -m streamlit run app.py
```

Install dependencies first if needed:

```bash
pip install -r requirements.txt
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## Smoke Tests

Run the rule-engine smoke tests:

```bash
python experiments/smoke_test_rules.py
```

Run the agent and experiment smoke tests:

```bash
python experiments/smoke_test_agents.py
```

Run the MCTS smoke tests:

```bash
python experiments/smoke_test_mcts.py
```

Run the exact benchmark smoke tests:

```bash
python experiments/smoke_test_exact.py
```

Run the minimal card-framework smoke tests:

```bash
python experiments/smoke_test_cards.py
```

Run the Streamlit import smoke test:

```bash
python experiments/smoke_test_app_import.py
```

Run the Phase 4 experiment-pipeline smoke test:

```bash
python experiments/smoke_test_phase4_experiments.py
```

The smoke tests cover connected track building, explicit delivery paths, corrected financing action space, automatic financing during payment, empty-city-marker end conditions, major-line bonuses, income, card loading, representative card effects, and final scoring.

## Phase 4 Card Experiments

Card-disabled baseline using the original card-free simulator:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --map data/toy_map.json --cards none --output results/raw/toy_card_disabled.csv
```

Card-enabled baseline using `data/cards_basic.json`:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --map data/toy_map.json --cards basic --output results/raw/toy_card_enabled.csv
```

Run a quick pipeline verification:

```bash
python experiments/run_phase4_card_experiments.py --profile quick
```

Run the dissertation-scale baseline card comparison:

```bash
python experiments/run_phase4_card_experiments.py --profile standard
```

Run the stronger MCTS comparison when runtime permits:

```bash
python experiments/run_phase4_card_experiments.py --profile mcts100
```

### MCTS Budget Comparison

Run and validate the stronger MCTS budget profile:

```bash
python experiments/run_phase4_card_experiments.py --profile mcts100
python experiments/validate_phase4_card_results.py --profile mcts100
```

Compare the standard and mcts100 summaries:

```bash
python experiments/compare_phase4_mcts_budget.py
```

Run the fast budget-comparison smoke test:

```bash
python experiments/smoke_test_phase4_budget_comparison.py
```

This comparison helps determine whether card-enabled MCTS performance is limited mainly by search budget or by the absence of card-aware evaluation and rollout behaviour. The mcts100 experiment may use fewer episodes than the standard profile when runtime is prohibitive; any override must be recorded in the result note.

Explicit arguments such as `--episodes`, `--mcts-iterations`, `--mcts-rollout-depth`, and `--max-steps` override the selected profile. Output filenames include the profile name so quick and preliminary results do not overwrite standard results.

Validate the standard result files:

```bash
python experiments/validate_phase4_card_results.py --profile standard
```

Each profile writes card-disabled and card-enabled raw CSV files, a full summary, a card-effect comparison table, and a card-usage table under `results/`. `--cards none` in the general experiment runner preserves the card-free model, while `--cards basic` enables `data/cards_basic.json`. The exact `micro_map` benchmark remains card-free by default.

The standard Phase 4 results are used to discuss how the representative cards affect existing agent behaviour, score composition, and search difficulty. No agent is made card-aware during this evidence-collection phase.

Run the simple greedy baseline from the command line:

```bash
python experiments/run_greedy.py
```

## Baseline Agents and Experiments

Implemented baseline agents:

- `RandomAgent`
- `GreedyDeliveryAgent`
- `GreedyExpansionAgent`

Run experiments:

```bash
python experiments/run_experiments.py --agent all --episodes 100
```

Run experiments on specific maps:

```bash
python experiments/run_experiments.py --agent all --episodes 100 --map data/toy_map.json
python experiments/run_experiments.py --agent all --episodes 100 --map data/toy_medium_map.json
python experiments/run_experiments.py --agent all --episodes 50 --map data/semi_realistic_map.json --output results/raw/semi_realistic_baseline_results.csv
```

Run all baseline agents on all configured maps:

```bash
python experiments/run_experiments.py --agent all --episodes 100 --map all --output results/raw/map_comparison_results.csv
```

Run one agent:

```bash
python experiments/run_experiments.py --agent greedy_delivery --episodes 100
```

Analyse results:

```bash
python experiments/analyse_results.py --input results/raw/experiment_results.csv
```

Generate plots:

```bash
python experiments/plot_results.py --input results/raw/experiment_results.csv
```

Results are saved under:

```text
results/raw/
results/processed/
results/plots/
```

## MCTS Agent

The first search-based agent is a Monte Carlo Tree Search agent. It uses the same legal-action environment interface as the baseline agents and plans on copied game states.

Run MCTS experiments:

```bash
python experiments/run_mcts_experiments.py --map data/toy_medium_map.json --episodes 30 --iterations-list 50,100,250 --seed 0
```

Analyse and plot MCTS results:

```bash
python experiments/analyse_results.py --input results/raw/mcts_experiment_results.csv
python experiments/plot_results.py --input results/raw/mcts_experiment_results.csv
```

## MCTS Validation

Run the MCTS smoke tests:

```bash
python experiments/smoke_test_mcts.py
```

Run the MCTS validation pipeline:

```bash
python experiments/run_mcts_pipeline.py --map data/toy_medium_map.json --episodes 30 --iterations-list 50,100,250 --seed 0
```

Validate MCTS results:

```bash
python experiments/validate_mcts_results.py --input results/raw/mcts_experiment_results.csv --episodes 30
```

Compare rollout policies:

```bash
python experiments/run_mcts_experiments.py --map data/toy_medium_map.json --episodes 5 --iterations-list 50,100 --rollout-policy-list random,greedy_delivery --output results/raw/mcts_rollout_comparison_results.csv
```

MCTS result notes are stored in:

```text
notes/MCTS_RESULTS_SUMMARY.md
```

## MCTS Tuning

Run MCTS tuning:

```bash
python experiments/run_mcts_tuning.py --map data/toy_medium_map.json --episodes 10 --iterations-list 50,100 --rollout-depth-list 40,80 --rollout-policy-list random --seed 0
```

Analyse and plot:

```bash
python experiments/analyse_mcts_tuning.py --input results/raw/mcts_tuning_results.csv
python experiments/plot_mcts_tuning.py --input results/raw/mcts_tuning_results.csv
```

Run the full tuning pipeline:

```bash
python experiments/run_mcts_tuning_pipeline.py --map data/toy_medium_map.json --episodes 10 --iterations-list 50,100 --rollout-depth-list 40,80 --rollout-policy-list random --seed 0
```

Fast-vs-full candidate action check:

```bash
python experiments/run_mcts_tuning.py --map data/toy_map.json --episodes 5 --iterations-list 20 --rollout-depth-list 30 --rollout-policy-list random --action-generation-list fast,full --seed 0 --output results/raw/mcts_fast_vs_full_results.csv
```

## Semi-realistic Map

Run baseline experiments:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --map data/semi_realistic_map.json --output results/raw/semi_realistic_baseline_results.csv
```

Analyse and plot baseline results:

```bash
python experiments/analyse_results.py --input results/raw/semi_realistic_baseline_results.csv --output results/processed/semi_realistic_baseline_summary.csv
python experiments/plot_results.py --input results/raw/semi_realistic_baseline_results.csv --output-dir results/plots/semi_realistic_baseline
```

Run MCTS experiments:

```bash
python experiments/run_mcts_experiments.py --map data/semi_realistic_map.json --episodes 10 --iterations-list 50,100 --rollout-depth 60 --rollout-policy random --seed 0 --output results/raw/semi_realistic_mcts_results.csv
```

Analyse and plot MCTS results:

```bash
python experiments/analyse_results.py --input results/raw/semi_realistic_mcts_results.csv --output results/processed/semi_realistic_mcts_summary.csv
python experiments/plot_results.py --input results/raw/semi_realistic_mcts_results.csv --output-dir results/plots/semi_realistic_mcts
```

## Semi-realistic Experiment Pipeline

Run the full semi-realistic reporting workflow:

```bash
python experiments/run_semi_realistic_pipeline.py --baseline-episodes 50 --mcts-episodes 10 --mcts-iterations-list 50,100 --seed 0
```

This runs smoke tests, the project readiness check, baseline experiments, MCTS experiments, analysis, plotting, and validation for `semi_realistic_map`.

Results are summarised in:

```text
notes/SEMI_REALISTIC_RESULTS_SUMMARY.md
```

## Semi-realistic Diagnosis and Major-line-aware MCTS

Run major-line sensitivity experiments:

```bash
python experiments/run_major_line_sensitivity.py --map data/semi_realistic_map.json --episodes 20 --mcts-episodes 5 --mcts-iterations-list 50,100 --multipliers 0,0.5,0.75,1.0 --seed 0
```

Analyse and plot sensitivity results:

```bash
python experiments/analyse_major_line_sensitivity.py --input results/raw/major_line_sensitivity_results.csv
python experiments/plot_major_line_sensitivity.py --input results/raw/major_line_sensitivity_results.csv
```

Run major-line-aware MCTS experiments:

```bash
python experiments/run_mcts_major_line_experiments.py --map data/semi_realistic_map.json --episodes 10 --iterations-list 50,100 --rollout-depth 60 --seed 0
```

Validate major-line-aware MCTS results:

```bash
python experiments/validate_major_line_experiments.py --input results/raw/mcts_major_line_results.csv --episodes 10
```

Run the combined diagnosis pipeline:

```bash
python experiments/run_semi_realistic_diagnosis_pipeline.py --episodes 20 --mcts-episodes 5 --mcts-iterations-list 50,100 --multipliers 0,0.5,0.75,1.0 --seed 0
```

Diagnosis notes are stored in:

```text
notes/SEMI_REALISTIC_DIAGNOSIS.md
```

## Exact Benchmark

Phase 3D adds a small exact-search benchmark on `micro_map`. The exact solver uses the same legal-action and transition interface as the simulator, but searches the full action tree with memoisation.

Run the exact solver:

```bash
python exact/run_exact_benchmark.py
```

Compare agents to the exact optimum:

```bash
python exact/compare_agents_to_exact.py
```

Run exact smoke tests:

```bash
python experiments/smoke_test_exact.py
```

Exact benchmark notes are stored in:

```text
notes/EXACT_BENCHMARK_RESULTS.md
```

## Baseline Experiment Validation

After running experiments, validate the outputs with:

```bash
python experiments/validate_baselines.py --input results/raw/experiment_results.csv --episodes 100
```

For map comparison results:

```bash
python experiments/validate_baselines.py --input results/raw/map_comparison_results.csv --episodes 100 --maps toy_map,toy_medium_map,semi_realistic_map
```

To run tests, experiments, analysis, plotting, and validation in one command:

```bash
python experiments/run_full_baseline_pipeline.py --episodes 100 --seed 0
```

Run the full pipeline across all configured maps:

```bash
python experiments/run_full_baseline_pipeline.py --episodes 100 --seed 0 --map all --output results/raw/map_comparison_results.csv
```

Experiment planning and baseline result notes are stored in:

```text
notes/EXPERIMENT_PLAN.md
notes/BASELINE_RESULTS_SUMMARY.md
```

## Project Direction

The simulator will later be extended with additional automated strategy methods such as Genetic Algorithms, reinforcement learning, or other optimisation approaches.

The current code separates map data, game state, rules, environment interface, agents, and visualisation:

```text
data JSON
    -> GameState
    -> rules.py / scoring.py
    -> environment.py
    -> baseline and MCTS agents
    -> visualization / Streamlit UI
```

## Repository Structure

```text
railways-world-ai/
|-- app.py
|-- README.md
|-- requirements.txt
|-- data/
|   |-- toy_map.json
|   |-- toy_medium_map.json
|   |-- semi_realistic_map.json
|   |-- micro_map.json
|   |-- micro_rules_config.json
|   `-- rules_config.json
|-- exact/
|   |-- __init__.py
|   |-- exact_solver.py
|   |-- run_exact_benchmark.py
|   `-- compare_agents_to_exact.py
|-- railways/
|   |-- __init__.py
|   |-- actions.py
|   |-- environment.py
|   |-- game_state.py
|   |-- map_loader.py
|   |-- models.py
|   |-- rules.py
|   |-- scoring.py
|   `-- visualization.py
|-- agents/
|   |-- __init__.py
|   |-- base_agent.py
|   |-- greedy_delivery_agent.py
|   |-- greedy_expansion_agent.py
|   |-- mcts_agent.py
|   |-- random_agent.py
|   |-- registry.py
|   `-- greedy_agent.py
|-- experiments/
|   |-- analyse_results.py
|   |-- analyse_major_line_sensitivity.py
|   |-- analyse_mcts_tuning.py
|   |-- check_project_readiness.py
|   |-- plot_results.py
|   |-- plot_major_line_sensitivity.py
|   |-- plot_mcts_tuning.py
|   |-- run_major_line_sensitivity.py
|   |-- run_full_baseline_pipeline.py
|   |-- run_mcts_major_line_experiments.py
|   |-- run_mcts_experiments.py
|   |-- run_mcts_pipeline.py
|   |-- run_mcts_tuning.py
|   |-- run_mcts_tuning_pipeline.py
|   |-- run_semi_realistic_diagnosis_pipeline.py
|   |-- run_semi_realistic_pipeline.py
|   |-- run_greedy.py
|   |-- run_experiments.py
|   |-- simulation_runner.py
|   |-- smoke_test_agents.py
|   |-- smoke_test_exact.py
|   |-- smoke_test_maps.py
|   |-- smoke_test_mcts.py
|   |-- smoke_test_rules.py
|   |-- validate_mcts_tuning.py
|   |-- validate_mcts_results.py
|   |-- validate_major_line_experiments.py
|   `-- validate_baselines.py
`-- notes/
    |-- BASELINE_RESULTS_SUMMARY.md
    |-- EXACT_BENCHMARK_RESULTS.md
    |-- EXPERIMENT_PLAN.md
    |-- MCTS_RESULTS_SUMMARY.md
    |-- MODEL_VALIDITY.md
    |-- RULE_FIDELITY_ROADMAP.md
    |-- RULES_COVERAGE.md
    |-- SCENARIO_DESIGN.md
    |-- SEMI_REALISTIC_DIAGNOSIS.md
    |-- SEMI_REALISTIC_RESULTS_SUMMARY.md
    `-- meeting_1_summary.md
```
