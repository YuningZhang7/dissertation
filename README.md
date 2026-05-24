# Railways of the World AI Simulator

## Overview

This project is a local visual simulator for a simplified single-player version of Railways of the World. It is intended as a testbed for future AI and optimisation strategies.

The first prototype uses a small toy map, Streamlit controls, and modular Python rule logic. It is deliberately simple so later dissertation work can add search, reinforcement learning, heuristics, or optimisation models without rewriting the visual environment.

## Current Features

- Toy railway map
- Track construction
- Goods delivery
- Locomotive upgrades
- Bonds
- Turn progression
- Local visual interface
- Basic random and greedy baseline agents
- Action history in the app

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## Project Direction

The simulator will later be extended with automated strategy agents such as greedy heuristics, Genetic Algorithms, Monte Carlo Tree Search, reinforcement learning, or other optimisation methods.

The current code separates map data, game state, rules, agents, and visualisation:

```text
data JSON
    -> GameState
    -> rules.py
    -> agents
    -> visualization / Streamlit UI
```

## Repository Structure

```text
railways-world-ai/
├── app.py
├── README.md
├── requirements.txt
├── data/
│   ├── toy_map.json
│   └── rules_config.json
├── railways/
│   ├── __init__.py
│   ├── models.py
│   ├── game_state.py
│   ├── map_loader.py
│   ├── rules.py
│   ├── scoring.py
│   └── visualization.py
├── agents/
│   ├── __init__.py
│   ├── random_agent.py
│   └── greedy_agent.py
├── experiments/
│   └── run_greedy.py
└── notes/
    └── meeting_1_summary.md
```

## Experiment Script

Run the greedy baseline without the Streamlit UI:

```bash
python experiments/run_greedy.py
```
