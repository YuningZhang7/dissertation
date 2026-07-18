# Railways of the World AI Simulator

## Overview

This project is a local visual simulator for a simplified single-player version
of Railways of the World. It is intended as a dissertation testbed for
interpretable AI and optimisation strategies.

The current mainline version focuses on the route-segment simulator, replay
demo, benchmark tooling, automatic financing, colored urbanization, and the
dissertation-facing public agents.

## Meeting/Demo Scope

The main meeting/demo build exposes five public agents.

Core agents:

- `random`
- `greedy_delivery`
- `greedy_expansion`
- `objective_aware_greedy`
- `lookahead_greedy`

`lookahead_greedy` is the final balanced lookahead agent for the demo path. It
is tuned for readable replays: it prioritizes route completion and delivery
before using urbanization near the built network or objective cities.
The original aggressive `urbanization_aware_lookahead_greedy` implementation is
kept as internal helper code, but is no longer exposed as a public demo agent.

See [notes/MEETING_DEMO_SCOPE.md](notes/MEETING_DEMO_SCOPE.md).

## Supervisor Feedback Corrections

The basic-rule action model has been corrected after supervisor feedback:

- The simulator has no fixed player starting city, home city, train position, or moving train token.
- Goods can be delivered from any source city with the required good to any demanding destination city if a valid built route exists.
- Issuing shares/bonds is not exposed as an agent action. Financing is handled internally during payment when automatic financing is enabled.
- The code still uses `bonds` naming in some fields for compatibility, but it currently approximates the share certificate financing mechanism.
- Connected track building remains configurable as a simplifying network-contiguity assumption, not as an official start-point rule.

## Current Rule Coverage

This version is a single-player rule-development prototype. It is not yet a
full official implementation of Railways of the World. The current goal is to
preserve the core local rules needed for optimisation experiments, while
excluding player-vs-player interaction for now.

See [notes/RULES_COVERAGE.md](notes/RULES_COVERAGE.md) and
[notes/MODEL_VALIDITY.md](notes/MODEL_VALIDITY.md).

## Scenario Design

The project includes self-created scenarios for smoke tests, demo runs, and
benchmark comparisons:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`
- `micro_map`
- `official_like_route_segment_map`
- `expanded_official_style_route_segment_map`

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
- Colored urbanize actions for each gray city and allowed good color
- Major-line loading, claiming, and final-score bonus support
- Rail Baron objective loading, claiming, and final-score bonus support
- Minimal representative operation-card framework
- AI-ready environment interface

## Not Yet Implemented

- Full official map
- Full individual track tile placement
- Full official operation-card deck
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

The app entry point is always `app.py`. Do not run markdown files such as
prompt notes or Codex task instructions.

Install dependencies first if needed:

```bash
pip install -r requirements.txt
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## Replay Demo

The current replay/presentation path is route-segment focused:

```bash
python experiments/demo_agent_animation_app.py
```

Replay generation and animation support live in:

```text
experiments/animate_agent_episode.py
```

## Smoke Tests

Run the core rule-engine smoke tests:

```bash
python experiments/smoke_test_rules.py
```

Run the current agent and benchmark smoke tests:

```bash
python experiments/smoke_test_agents.py
python experiments/smoke_test_agent_benchmark.py
python experiments/smoke_test_app_import.py
python experiments/smoke_test_agent_animation_app.py
python experiments/smoke_test_agent_animation.py
python experiments/smoke_test_lookahead_greedy_agent.py
python experiments/smoke_test_meeting_demo.py
python experiments/smoke_test_official_like_baselines.py
python experiments/smoke_test_expanded_official_style_baselines.py
```

Optional focused smoke tests remain for maps and the representative card
framework:

```bash
python experiments/smoke_test_maps.py
python experiments/smoke_test_cards.py
```

The smoke tests cover connected track building, explicit delivery paths,
corrected financing action space, automatic financing during payment,
empty-city-marker end conditions, major-line bonuses, Rail Baron bonuses,
income, colored urbanization, action hashing, replay compatibility, and final
scoring.

## Benchmarking

Run a small current-agent benchmark:

```bash
python experiments/run_agent_benchmark.py --maps official_like --episodes 5 --max-steps 50
```

Run selected agents explicitly:

```bash
python experiments/run_agent_benchmark.py --maps official_like --agents objective_aware_greedy lookahead_greedy --episodes 5 --max-steps 50
```

Generate a replay-friendly lookahead episode:

```bash
python experiments/animate_agent_episode.py --map official_like --agent lookahead_greedy --seed 42 --max-steps 60 --frame-mode events
```

Benchmark outputs are written under:

```text
experiments/results/agent_benchmark/
```

The benchmark records score, bonds, deliveries, completed routes, major-line
and Rail Baron bonuses, fallback actions, runtime, and urbanization diagnostics
such as `urbanize_actions` and `urbanized_city_count`.

## Baseline Experiments

The older baseline runner remains available for the lightweight toy-map
experiments:

```bash
python experiments/run_experiments.py --agent all --episodes 100
python experiments/run_greedy.py
```

After running baseline experiments, validate their output with:

```bash
python experiments/validate_baselines.py --input results/raw/experiment_results.csv --episodes 100
```

For current dissertation comparisons, prefer `experiments/run_agent_benchmark.py`.

## Historical Results

Historical notes and generated outputs from earlier exploratory phases are
retained for provenance. They are not part of the current core-agent
meeting/demo runtime.

Main evidence locations include:

```text
notes/
results/
experiments/results/
experiments/outputs/
```

## Project Direction

The simulator may later be extended with additional automated strategy methods
such as Genetic Algorithms, reinforcement learning, or other optimisation
approaches.

The current code separates map data, game state, rules, environment interface,
agents, and visualisation:

```text
data JSON
    -> GameState
    -> rules.py / scoring.py
    -> environment.py
    -> current public agents
    -> visualization / Streamlit UI
```

## Repository Structure

```text
railways-world-ai/
|-- app.py
|-- README.md
|-- requirements.txt
|-- data/
|-- railways/
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
|   |-- objective_aware_greedy_agent.py
|   |-- lookahead_greedy_agent.py
|   |-- random_agent.py
|   |-- registry.py
|   `-- urbanization_aware_lookahead_greedy_agent.py
|-- experiments/
|   |-- animate_agent_episode.py
|   |-- demo_agent_animation_app.py
|   |-- run_agent_benchmark.py
|   |-- run_experiments.py
|   |-- simulation_runner.py
|   |-- smoke_test_agents.py
|   |-- smoke_test_agent_benchmark.py
|   |-- smoke_test_agent_animation.py
|   |-- smoke_test_agent_animation_app.py
|   |-- smoke_test_app_import.py
|   |-- smoke_test_meeting_demo.py
|   |-- smoke_test_lookahead_greedy_agent.py
|   |-- smoke_test_urbanization_aware_lookahead_greedy_agent.py
|   `-- validate_baselines.py
`-- notes/
```
