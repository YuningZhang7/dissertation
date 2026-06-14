# Model Validity and Scope

## Purpose of the Model

This simulator is a rule-based single-player abstraction of Railways of the World. It is designed as an optimisation and AI testbed, not as a full commercial game implementation.

## Core Mechanics Preserved

- Graph-based railway network construction
- City-to-city railway links
- Goods located at cities
- City demand colours
- Goods delivery through built railway paths
- Explicit delivery-route selection
- Locomotive level limiting delivery distance
- Money, internal share/bond financing, and financing obligations
- Income phase
- Empty city markers
- Major-line bonuses
- Minimal representative operation-card objectives and bonuses
- Final scoring
- Single-player action sequence
- Legal-action interface for algorithms
- Repeatable experiment framework for baseline and MCTS agents

## Simplifications

- Maps are artificial rather than official.
- Each city-to-city connection is modelled as one graph edge rather than individual track tiles.
- Track cost is a fixed edge cost rather than computed from detailed terrain tiles.
- Terrain, rivers, mountains, tile inventory, and crossing rules are not yet modelled.
- A minimal representative operation-card framework is implemented, but the full official deck and timing rules are not.
- Rail Baron cards are not fully implemented.
- Multiplayer auction and opponent interaction are excluded.
- Opponent-owned track scoring is excluded.
- Some official map-specific rules are not yet included.
- Income, share/bond financing, urbanisation, and end conditions are simplified but configurable.
- There is no fixed player start city, home city, train position, or moving train token.
- The optional connected-track rule is a simplifying network-contiguity assumption, not a claim that the official game has a fixed origin.

## Why the Simplified Model Is Still Useful

The current model captures the core sequential network design problem:

- expand a railway network;
- manage limited money;
- use internal financing when payments exceed available cash;
- decide when to upgrade locomotives;
- choose which goods to deliver;
- balance short-term scoring and long-term network expansion;
- pursue major-line bonuses while maintaining delivery opportunities.
- optionally select simplified operation cards that add immediate, delivery, network, or end-game objectives.

This is enough to compare algorithmic strategies under a defined abstraction. It also gives a clear bridge from operations research ideas such as graph search, heuristic construction, simulation, and sequential decision-making to a visual and testable local environment.

## Limits of Current Experimental Claims

The current experiments do not claim to solve the full official board game. They compare algorithms under a defined single-player abstraction.

Results should be interpreted as evidence about this simplified network-design environment. Strong performance by an agent means it performs well under the implemented rules, maps, and scoring assumptions. It does not yet imply strong play in the complete multiplayer board game.

After supervisor feedback, the action model was corrected so that share issuing is no longer exposed as an agent decision. The legacy `issue_bond` action is rejected by the external action interface, and all financing is handled internally through `pay_money` during paid actions. The model also avoids any fixed start-city or train-position assumption, because Railways of the World does not have a player start location in the sense used by train-token movement games.

Phase 4 adds a minimal original card framework as a fuller-rule foundation. It supports JSON-defined immediate cash cards, delivery objectives, network objectives, and end-game scoring cards. It is not a complete official card system and does not copy official card text.

Cards are opt-in for programmatic simulations through `reset_game(..., card_path=...)`. The Streamlit demo enables `data/cards_basic.json`, while the exact `micro_map` benchmark remains card-disabled by default so earlier exact-search results stay comparable.

## Path Toward Greater Realism

1. `micro_map` for exact optimality benchmarking.
2. `toy_map` for debugging.
3. `toy_medium_map` for baseline comparison.
4. `semi_realistic_map` for stronger external validity.
5. Minimal card-enabled scenarios for fuller-rule comparison.
6. Optional official-like map and rules if time permits.

The Phase 3A goal is to move from artificial debugging maps toward a more realistic single-player optimisation scenario without copying official artwork or attempting a full commercial game implementation.
