# Meeting Demo Scope

## Purpose

The meeting demo presents the parts of the dissertation prototype that are easiest to explain, inspect, and reproduce: route-segment construction, legal-action generation, automatic financing, completed-route delivery, objective bonuses, interpretable agent behaviour, and replay visualisation.

The demo is evidence that the implemented abstraction and agent interface work. It is not the formal dissertation benchmark and should not be used on its own to claim that one agent is generally best.

## Included Agents

- `RandomAgent`: a legal-action reference baseline.
- `GreedyDeliveryAgent`: prioritises immediately available deliveries.
- `GreedyExpansionAgent`: prioritises network growth.
- `ObjectiveAwareGreedyAgent`: the strongest one-step objective-aware baseline.
- `LookaheadGreedyAgent`: the final bounded-lookahead agent for readable replay demonstrations.

These are the only agents exposed by `agents/registry.py`, the Streamlit selector, and the current benchmark defaults. Shared lookahead support code lives in `agents/lookahead_utils.py`.

## Historical Exploratory Agents

Earlier project phases investigated MCTS and card-aware heuristics. Their active agent implementations and experiment entry points were removed during the five-agent mainline cleanup. Historical notes and generated result artefacts may still mention them for provenance.

Do not state that MCTS or CardAware source files remain in the current runtime, and do not include their historical results in the current five-agent comparison without clearly labelling them as results from an earlier model version.

## Card System

The repository contains a representative operation-card framework and the example deck `data/cards_basic.json`. This optional environment functionality can be enabled explicitly through `reset_game(..., card_path=...)`.

The current Streamlit replay and public benchmark runners do not supply a card path, so both are card-disabled. The compatibility helper `app.create_game_state()` can construct a card-enabled state, but the current Streamlit `main()` entry path does not use it.

The current meeting replay focuses on route-segment construction, automatic financing, delivery, urbanisation, objectives, and interpretable agent behaviour. Operation cards are implemented optional functionality but are not enabled in the current replay and are not part of the current five-agent performance comparison.

## Recommended Meeting Configuration

Use the compact map and the replay-friendly agent:

```text
Map: official_like
Agent: lookahead_greedy
Seed: 42
Max steps: 30
Frame mode: events
```

The 30-step value is intentionally a presentation horizon. It keeps replay generation responsive and produces a readable sequence of decisions. If the episode has not terminated, the displayed value is a **truncated score**, not a terminal final score.

For the expanded map, prefer:

```text
Map: expanded
Agent: objective_aware_greedy
Seed: 42
Max steps: 30
Frame mode: events
```

Avoid relying on a live expanded-map `lookahead_greedy` run during a meeting because its bounded simulations are substantially slower on the larger action space.

## Recommended Meeting Path

1. Launch the Streamlit replay interface with `python run_app.py`.
2. Explain that routes contain ordered segments and become usable only when completed.
3. Show automatic financing, completed-route delivery, and objective bonuses.
4. Run `official_like`, `lookahead_greedy`, seed 42, for 30 steps in event-frame mode.
5. Point out whether the episode is terminal and use the corresponding score terminology.
6. Explain that all five agents share the same legal-action environment interface.
7. Present formal multi-seed benchmark results separately from the single replay.

## Quick Benchmark Warning

```bash
python experiments/run_agent_benchmark.py --quick
```

is a smoke/development comparison only. It uses very few episodes, a short horizon, and excludes `lookahead_greedy` for speed. It must not be used as the main dissertation evidence.

