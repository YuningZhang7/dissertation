# Meeting Demo Scope

## Purpose

The meeting demo presents the parts of the dissertation prototype that are easiest to explain, inspect, and reproduce: simulator correctness, legal-action generation, representative operation cards, and interpretable baseline behaviour.

## Included Agents

- `RandomAgent`: a legal-action reference baseline.
- `GreedyDeliveryAgent`: prioritises immediately valuable deliveries.
- `GreedyExpansionAgent`: prioritises network growth before delivery.

These are the only agents exposed by `agents/registry.py`, the Streamlit selector, and the main `experiments/run_experiments.py` comparison.

## Excluded From the Main Demo

- `MCTSAgent` needs more tuning and validation before it can support a concise meeting claim.
- `CardAwareGreedyAgent` adds card-specific heuristic assumptions that make the comparison less direct.

Their source files and historical experiment scripts remain in the full research repository. Exclusion is a scope-control decision, not a claim that these exploratory components never existed.

## Card System

The representative operation-card framework remains enabled in the visual demo. Cards are part of the environment and scoring model; only the separate card-aware agent is excluded from the main comparison.

## Recommended Meeting Path

1. Launch the Streamlit simulator with `python run_app.py`.
2. Show the graph map, player state, legal manual actions, financing, and card panel.
3. Run one action or a complete episode with each of the three baseline agents.
4. Explain that all agents share the same legal-action environment interface.
5. Use `python experiments/run_experiments.py --agent all --episodes 10 --map all` for a small reproducible comparison.

## Package

Create the clean meeting package with:

```bash
python scripts/create_meeting_demo_package.py
```

The generated package intentionally omits exploratory agent modules, MCTS/card-aware experiment scripts, and their result artefacts.
