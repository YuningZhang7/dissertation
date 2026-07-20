# Railways of the World AI Simulator

## Overview

This project is a local visual simulator for a simplified single-player railway network problem inspired by *Railways of the World*. It is intended as a dissertation testbed for interpretable AI and optimisation strategies, not as a full commercial game implementation.

The current mainline focuses on:

- a route-segment simulator;
- five interpretable public agents;
- automatic financing;
- coloured urbanisation;
- Major Line and Rail Baron connection objectives;
- replay visualisation;
- reproducible multi-seed benchmark tooling.

## Current Public Agents

The public registry exposes exactly five agents:

- `random`
- `greedy_delivery`
- `greedy_expansion`
- `objective_aware_greedy`
- `lookahead_greedy`

`objective_aware_greedy` is the strongest one-step heuristic baseline. It prioritises current deliveries and otherwise scores route construction and locomotive upgrades using delivery potential, route completion, objectives, construction cost, and financing.

`lookahead_greedy` is the final enhanced agent. It uses depth-two bounded
lookahead with a `0.55` future-value discount and conservative urbanisation gates.
At both the root and rollout levels, delivery, build, upgrade, and urbanisation
actions use their respective full heuristic scorers. The levels differ only in
candidate budgets: root considers up to four deliveries, four builds, and one
urbanisation; rollout considers two deliveries, three builds, one urbanisation,
and five candidates overall. Each accepted candidate stores its full immediate
score once and reuses it during rollout. This keeps the method interpretable while
making no claim of optimality.

Shared lookahead helper code lives in `agents/lookahead_utils.py`.

Historical MCTS and CardAware experiments are not part of the current runtime. Historical notes and generated outputs may still mention them for provenance.

## Current Rule Model

The active runtime requires route-segment maps. Each city-to-city route contains an ordered sequence of abstract track segments, and a route becomes usable only after all of its segments are completed.

Implemented mainline rules include:

- action and income phases;
- configurable actions per turn;
- building one to four consecutive segments on one route;
- route completion after every segment on that route is built;
- removal of incomplete segments during the income phase;
- delivery over explicitly selected completed-route paths;
- locomotive level limiting delivery distance by segment count;
- prevention of skipping an intermediate city demanding the same good colour;
- locomotive upgrades;
- internal automatic financing during paid actions;
- financing obligations and final financing penalties;
- score-based income;
- empty-city markers and configurable end conditions;
- coloured urbanisation of grey cities;
- Major Line and Rail Baron connectivity bonuses;
- an optional representative operation-card framework;
- an AI-ready reset, legal-action, transition, copy, terminal, and scoring interface.

The current route-segment validator enforces continuity within a route: a new segment chain must touch that route's city endpoint or an existing incomplete endpoint. The legacy `require_connected_track_building` configuration field should not be interpreted as global connectivity enforcement to the player's existing completed network.

The simulator has no fixed home city, train position, or moving train token. Issuing financing certificates is not an agent action; payment functions issue the minimum required amount automatically when enabled. The historical `bonds` field name approximates share-certificate financing in this abstraction.

See:

- [notes/RULES_COVERAGE.md](notes/RULES_COVERAGE.md)
- [notes/MODEL_VALIDITY.md](notes/MODEL_VALIDITY.md)

## Scenarios

The current dissertation-facing maps are:

- `official_like`: compact route-segment map for the main comparison and replay;
- `expanded_official_style`: larger route-segment map for scalability analysis.

Both maps are artificial research scenarios. They do not copy official board artwork or official map data.

Earlier toy, semi-realistic, and micro scenarios may remain in repository history or historical experiment material, but they are not the main current five-agent benchmark.

## Running the Application

The full interactive simulator provides agent replay and strategy analysis for
both public maps and all five public agents.

### macOS Apple Silicon

In Finder, double-click:

```text
Launch Railways AI.command
```

The launcher verifies an ARM-native macOS and Python 3.10+ environment, creates
`.venv-macos-arm64`, installs `requirements.txt` when needed, and starts the full
application. See [MACOS_SETUP.md](MACOS_SETUP.md) for first-launch, Gatekeeper,
architecture, and manual-start instructions.

### Cross-platform terminal launch

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_app.py
```

On Windows PowerShell, activate the environment with:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_app.py
```

You can also start Streamlit directly with `python -m streamlit run app.py`.

A useful initial replay configuration is:

```text
Map: official_like
Agent: lookahead_greedy
Seed: 42
Max steps: 30
Frame mode: events
```

The 30-step default is an interactive horizon chosen for a responsive replay. If
the episode has not terminated, the app labels the displayed value as a
**truncated score** rather than a terminal final score.

For an interactive run on the expanded map, `objective_aware_greedy` responds more
quickly because `lookahead_greedy` searches a substantially larger action space.

## Command-Line Replay

Generate an example replay:

```bash
python experiments/animate_agent_episode.py \
  --map official_like \
  --agent lookahead_greedy \
  --seed 42 \
  --max-steps 30 \
  --frame-mode events
```

Replay generation and rendering support live in:

```text
experiments/animate_agent_episode.py
experiments/agent_replay_app.py
```

## Score Terminology

`GameState.final_score()` applies the scoring formula to the current state. The name of the function does not by itself mean that the game ended.

Use these terms:

- **Terminal final score**: the environment reached its game-over state.
- **Truncated score**: execution stopped at `max_steps` before game over.
- **Evaluation score**: a generic term covering both cases.

Benchmark rows include:

```text
terminal
score_type
final_score
```

`final_score` is retained for compatibility and represents the evaluation score at the stopping point. `score_type` is `terminal_final_score` or `truncated_score`.

Do not describe a fixed-horizon group containing non-terminal episodes as completed-game final scores.

## Formal Benchmark Plan

The current methodology is documented in:

[notes/EXPERIMENT_PLAN.md](notes/EXPERIMENT_PLAN.md)

The primary planned comparison is:

```text
Map: official_like
Agents: all five public agents
Episodes: 20 paired seeds
Seeds: 1000–1019
Maximum steps: 60
Cards: disabled
```

Run it with:

```bash
python experiments/run_agent_benchmark.py \
  --maps official_like \
  --agents random greedy_delivery greedy_expansion objective_aware_greedy lookahead_greedy \
  --episodes 20 \
  --max-steps 60 \
  --base-seed 1000 \
  --output-dir experiments/results/formal_benchmark/official_like_60
```

The formal plan also defines:

- 30/60/90-step horizon sensitivity;
- expanded-map scalability experiments;
- a smaller expanded-map lookahead pilot;
- paired seed-by-seed comparisons;
- terminal-rate reporting;
- score and runtime distributions;
- cautious dissertation claim rules.

Seed 42 and the 30-step replay are qualitative inspection settings, not the main
statistical evidence.

## Benchmark Outputs

Outputs are written under the selected output directory and include:

```text
benchmark_rows.csv
benchmark_summary.json
benchmark_summary.md
```

Recorded data include:

- evaluation score and score type;
- terminal and success flags;
- deliveries and completed routes;
- Major Line and Rail Baron bonuses;
- financing;
- action counts;
- urbanisation diagnostics;
- fallback and failed actions;
- runtime;
- efficiency ratios.

The generated Markdown summary reports terminal rate and separates mean terminal final score from mean truncated score when available.

## Smoke Tests

Run the current core checks:

```bash
python experiments/smoke_test_rules.py
python experiments/smoke_test_agents.py
python experiments/smoke_test_agent_benchmark.py
python experiments/smoke_test_app_import.py
python experiments/smoke_test_agent_replay_app.py
python experiments/smoke_test_agent_animation.py
python experiments/smoke_test_lookahead_greedy_agent.py
python experiments/smoke_test_registered_agents.py
python experiments/smoke_test_official_like_baselines.py
python experiments/smoke_test_expanded_official_style_baselines.py
```

Optional focused checks remain for maps and the representative card framework:

```bash
python experiments/smoke_test_maps.py
python experiments/smoke_test_cards.py
```

## Operation-Card Scope

The repository contains a representative operation-card framework and the example deck `data/cards_basic.json`. Cards are opt-in environment functionality and are enabled explicitly through `reset_game(..., card_path=...)`.

The current Streamlit replay and public benchmark runners do not supply a card path, so both are card-disabled. The compatibility helper `app.create_game_state()` can construct a card-enabled state, but the current Streamlit `main()` entry path does not use that helper.

The five public agents do not include a dedicated card-aware policy. Operation cards are therefore not a primary variable or performance claim in the current five-agent dissertation comparison.

## Not Yet Implemented

- full official map data or artwork;
- official track-tile placement and inventory;
- complete terrain, river, mountain, and crossing rules;
- full official financing and income model;
- full official operation-card deck and timing;
- full Rail Baron or Tycoon card system;
- multiplayer auctions and opponent interaction;
- opponent-owned track scoring and payments;
- Genetic Algorithm or Reinforcement Learning agents;
- proven optimal methods for the current official-like and expanded scenarios.

## Repository Structure

```text
railways-world-ai/
|-- app.py
|-- Launch Railways AI.command
|-- MACOS_SETUP.md
|-- README.md
|-- run_app.py
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
|   |-- base_agent.py
|   |-- greedy_delivery_agent.py
|   |-- greedy_expansion_agent.py
|   |-- objective_aware_greedy_agent.py
|   |-- lookahead_greedy_agent.py
|   |-- lookahead_utils.py
|   |-- random_agent.py
|   `-- registry.py
|-- experiments/
|   |-- animate_agent_episode.py
|   |-- agent_replay_app.py
|   |-- run_agent_benchmark.py
|   |-- simulation_runner.py
|   |-- smoke_test_agent_benchmark.py
|   |-- smoke_test_agent_replay_app.py
|   |-- smoke_test_lookahead_greedy_agent.py
|   `-- smoke_test_registered_agents.py
`-- notes/
    |-- EXPERIMENT_PLAN.md
    |-- DISSERTATION_RESULTS_OUTLINE.md
    |-- MODEL_VALIDITY.md
    `-- RULES_COVERAGE.md
```

## Dissertation Claim Boundary

Results support conclusions about the implemented single-player route-segment abstraction under the reported maps, rules, seeds, card setting, and horizons. They do not establish optimal play or performance in the complete multiplayer board game.
