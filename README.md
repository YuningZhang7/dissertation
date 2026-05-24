# Railways of the World AI Simulator

## Overview

This project is a local visual simulator for a simplified single-player version of Railways of the World. It is intended as a testbed for future AI and optimisation strategies.

The current version focuses on Phase 2A core rule fidelity: making the single-player rule engine clearer, more testable, and more faithful before adding advanced AI methods.

## Current Development Stage

The project is currently focused on building a rule-complete single-player simulator. AI agents will be added after the rule engine is stable.

## Current Rule Coverage

This version is a single-player rule-development prototype. It is not yet a full official implementation of Railways of the World. The current goal is to preserve the core local rules needed for optimisation experiments, while excluding player-vs-player interaction for now.

See [notes/RULES_COVERAGE.md](notes/RULES_COVERAGE.md).

## Implemented Core Rules

- Turn structure with action and income phases
- Configurable actions per turn
- Connected track-building restriction after the first built edge
- Explicit route-based goods delivery actions
- Upgrade engine
- Bonds
- Bond interest during income
- Score-based income phase
- Basic final scoring
- Empty city markers
- Fixed-turn and empty-city-marker end condition modes
- Simplified urbanize action
- Major-line loading, claiming, and final-score bonus support
- AI-ready environment interface

## Not Yet Implemented

- Full official map
- Full individual track tile placement
- Full operation cards
- Multiplayer auction and interaction
- Opponent-owned track scoring
- Advanced AI methods

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
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

The smoke tests cover connected track building, explicit delivery paths, empty-city-marker end conditions, major-line bonuses, bonds, income, and final scoring.

Run the simple greedy baseline from the command line:

```bash
python experiments/run_greedy.py
```

## Project Direction

The simulator will later be extended with automated strategy methods such as greedy heuristics, Genetic Algorithms, Monte Carlo Tree Search, reinforcement learning, or other optimisation approaches.

The current code separates map data, game state, rules, environment interface, agents, and visualisation:

```text
data JSON
    -> GameState
    -> rules.py / scoring.py
    -> environment.py
    -> agents later
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
|   `-- rules_config.json
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
|   |-- random_agent.py
|   `-- greedy_agent.py
|-- experiments/
|   |-- run_greedy.py
|   `-- smoke_test_rules.py
`-- notes/
    |-- RULES_COVERAGE.md
    `-- meeting_1_summary.md
```
