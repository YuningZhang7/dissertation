# Project Status: Dissertation-Ready Experimental Prototype

The project has reached a dissertation-ready experimental prototype stage. It is not a complete official implementation of Railways of the World, but it now provides a coherent rule-based optimisation environment, multiple agent baselines, exact benchmarking on a tiny map, representative card extensions, and reproducible experiment summaries.

## Implemented Features

- Single-player graph-based railway simulator.
- No fixed start city, home city, train position, or moving train token.
- Track building on configurable map graphs.
- Goods delivery from any valid source city to any valid demanding target city through built railway paths.
- Locomotive range constraints and explicit route validation.
- Money, income, internal financing, and final financing penalty.
- External `issue_bond` action rejected; financing occurs through `pay_money`.
- Engine upgrade and simplified urbanisation actions.
- Major-line loading, claiming, and scoring.
- Minimal representative operation-card framework:
  - immediate cash
  - delivery objective
  - network objective
  - end-game scoring
- Streamlit visual demo with card-enabled scenarios.
- Shared legal-action interface for manual play, agents, MCTS, and exact search.

## Implemented Agents and Search

- Random agent.
- Greedy delivery agent.
- Greedy expansion agent.
- Card-aware greedy agent.
- MCTS.
- Major-line-aware MCTS.
- MCTS with card-aware rollout.
- Major-line-aware MCTS with card-aware rollout.
- Exact solver for tiny benchmark maps.

## Experiments Completed

- Baseline agent experiments on artificial maps.
- MCTS and major-line-aware MCTS experiments.
- Exact benchmark on `micro_map`.
- Phase 4 card-disabled vs card-enabled comparisons.
- Phase 4C standard card experiment.
- Phase 4C MCTS100 budget diagnostic.
- Phase 4D card-aware greedy and card-aware rollout experiment.

## Key Results

- The exact `micro_map` optimum is 10, with an 8-action optimal sequence.
- Greedy delivery reaches the exact optimum on `micro_map`.
- MCTS approaches the exact optimum under limited budgets.
- Representative cards change score composition and add delayed objectives.
- Existing greedy agents often ignore cards on larger maps.
- Higher MCTS budget improves absolute performance but does not fully solve card-enabled branching trade-offs.
- Card-aware greedy is useful but map-dependent.
- Card-aware MCTS rollout improves strongly over ordinary card-enabled MCTS on the tested maps, especially `semi_realistic_map`.
- Card-aware MCTS rollout also increases runtime substantially.

## Dissertation Evidence Package

Traceability and presentation support now include:

- `notes/EXPERIMENT_MANIFEST.md`
- `notes/DISSERTATION_RESULTS_OUTLINE.md`
- `notes/PROJECT_STATUS_FINAL.md`
- `experiments/validate_all_results.py`
- `experiments/generate_dissertation_figures.py`
- `experiments/export_dissertation_tables.py`
- dissertation figures under `results/figures/`
- dissertation tables under `results/tables/`

## Known Simplifications

- Single-player only.
- No multiplayer auction.
- No opponent-owned tracks or opponent payments.
- No full official map.
- No tile-level track placement.
- No full official operation-card deck.
- No full Rail Baron / Tycoon objective deck.
- Terrain is abstracted through edge costs rather than tile geometry.
- Financing still uses historical `bonds` field names internally, while modelling an approximate share-certificate mechanism.
- Representative cards are original simplified cards, not copied official card text.
- Maps are artificial research scenarios rather than official game boards.

## Not Implemented

- Genetic algorithms.
- Reinforcement learning.
- Multiplayer interaction.
- Full official deck and map.
- Full official income/dividend rules.
- Card-aware MCTS value function tuning beyond rollout guidance.

## Next Possible Work

- Expand the representative card set.
- Add a small Rail Baron / Tycoon-style objective-card subset.
- Run larger-seed Phase 4D confirmation experiments if time allows.
- Optimise card-aware rollout runtime.
- Add sensitivity analysis for card rewards, major-line values, and financing parameters.
- Consider GA or reinforcement learning only after dissertation core results are written up.
