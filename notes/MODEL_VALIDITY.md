# Model Validity and Scope

## Purpose of the Model

This simulator is a rule-based single-player abstraction inspired by *Railways of the World*. It is designed as a dissertation testbed for interpretable sequential decision-making and optimisation strategies, not as a full commercial game implementation.

The current mainline runtime is route-segment based. A city-to-city route contains an ordered sequence of abstract track segments, and a route becomes usable for delivery only after all of its segments have been completed.

## Core Mechanics Preserved

- Graph-based railway network construction.
- Ordered route segments with build costs and completion state.
- Cities containing goods and cities demanding goods by colour.
- Explicit source, destination, and route-path selection for deliveries.
- Locomotive level limiting delivery distance by completed segment count.
- Money, internal financing certificates, and income-phase financing obligations.
- Action and income phases with a configurable number of actions per turn.
- Empty-city markers and configurable end-condition handling.
- Major Line connection bonuses.
- One active Rail Baron connection objective.
- Coloured urbanisation of grey cities.
- An optional representative operation-card framework that can be enabled explicitly.
- A common legal-action and state-transition interface for all public agents.
- Reproducible replay and multi-seed benchmark tooling.

## Current Public Decision Policies

The dissertation-facing mainline exposes five interpretable agents:

- `random`;
- `greedy_delivery`;
- `greedy_expansion`;
- `objective_aware_greedy`;
- `lookahead_greedy`.

`objective_aware_greedy` is the strongest one-step heuristic baseline. `lookahead_greedy` adds bounded depth-two lookahead, candidate-action pruning, and conservative urbanisation planning. Historical MCTS and card-aware experiments are retained only as repository history or historical result notes; their agent implementations are not part of the current mainline comparison.

## Simplifications

- The maps and city names are artificial research scenarios rather than official board data.
- Route segments are abstract ordered units, not individual official track tiles.
- Segment costs are fixed in the scenario data rather than calculated from full terrain, river, mountain, crossing, and tile-inventory rules.
- A build action may place up to four consecutive segments on one route. The active validator enforces route-local continuity from a route endpoint or an existing incomplete endpoint.
- Incomplete segments are removed during the income phase if their route has not been completed.
- The legacy `require_connected_track_building` configuration field should not be interpreted as enforcement of global connectivity to the player's existing completed network in the current route-segment validator.
- All completed routes are owned by the single player.
- Multiplayer auctions, blocking, opponent track fees, and shared goods competition are excluded.
- Income, financing, urbanisation, end conditions, Major Lines, and Rail Baron objectives are simplified abstractions.
- Urbanisation adds randomly generated goods under the configured random seed.
- The operation-card framework uses the small original test deck `data/cards_basic.json` rather than official card text or the full official timing rules.
- Cards are enabled only when a caller supplies `reset_game(..., card_path=...)`.
- Public agents do not contain a dedicated card-aware decision model; the card framework is optional environment functionality rather than a primary part of the current five-agent comparison.
- There is no fixed player start city, home city, train position, or moving train token.

## Why the Simplified Model Is Useful

The model captures a controlled sequential network-design problem in which an agent must:

- choose where and when to construct routes;
- complete a route before temporary work is removed;
- balance immediate deliveries against future network value;
- manage automatic financing and its penalties;
- decide when locomotive upgrades create useful delivery opportunities;
- pursue Major Line and Rail Baron connection rewards;
- decide whether urbanising a grey city creates enough near-term or objective value.

This supports interpretable comparisons between policies under a precisely defined abstraction. It also connects graph search, heuristic construction, simulation, and sequential decision-making to a visual and reproducible environment.

## Limits of Experimental Claims

The experiments compare agents only under the implemented rules, maps, scoring function, action horizon, and random seeds. Strong performance does not imply strong play in the complete multiplayer board game.

The project should not claim optimality for `lookahead_greedy`. It is a hand-designed bounded-lookahead heuristic with a restricted candidate set, not exhaustive search or a proven solver.

The current Streamlit replay and public benchmark runners do not supply a card path, so both are card-disabled. The compatibility helper `app.create_game_state()` can construct a card-enabled state using `data/cards_basic.json`, but the current Streamlit `main()` entry path does not use that helper. Operation cards are therefore outside the primary five-agent performance comparison unless a separate card-enabled experiment is explicitly designed and reported.

## Score Terminology

`GameState.final_score()` applies the final scoring formula to the current state. Its interpretation depends on why an episode stopped:

- **Terminal final score**: the score when the environment reached its game-over state.
- **Truncated score**: the same scoring formula evaluated when a benchmark or replay stopped at `max_steps` before game termination.

A truncated score is useful for fixed-horizon comparison, but it must not be described as a completed-game outcome. Benchmark rows record the terminal flag, and current reporting should distinguish the two score types.

## Path Toward Greater Realism

1. Calibrate segment costs, income, financing, urbanisation, and end conditions against a selected rule interpretation.
2. Add terrain and tile-level construction constraints only if they are needed for the research questions.
3. Define a dedicated fixed-turn terminal benchmark configuration if completed-game comparisons are required.
4. Extend operation cards only after deciding whether card-aware decision-making remains in dissertation scope.
5. Treat multiplayer interaction as a separate future model rather than mixing it into the current single-player evaluation.
