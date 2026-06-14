# Rule Fidelity Roadmap

## Already Implemented

- Turn/action/income structure
- Track building as graph edges
- Connected track-building restriction
- Explicit route-based goods delivery
- Locomotive upgrades
- Internal share/bond financing and income-phase obligations
- Basic income phase
- Empty city markers
- Fixed-turn and empty-city-marker end conditions
- Urbanize simplified
- Major-line bonuses
- Baseline and MCTS agent support
- Multi-map experiment runners
- MCTS tuning and validation scripts
- Corrected action space: share/bond issuing is financing, not a normal agent action
- No fixed start city, home city, train position, or moving train token

## High Priority Next Rules

These rules most affect optimisation behaviour:

1. More realistic map data
2. More realistic edge costs
3. More realistic income table
4. More complete share-certificate/payment rules
5. More complete major-line data
6. More complete end condition
7. Better urbanize/goods replenishment rules

## Medium Priority Rules

1. Rail Baron / objective cards
2. A small representative subset of operation cards
3. Different scenario configurations
4. Map-specific bonuses
5. Scenario-specific starting money and turn limits
6. Alternative scoring variants for sensitivity analysis

## Low Priority / Future Work

1. Full operation card deck
2. Full official individual tile placement
3. Official map-specific exceptions
4. Multiplayer auction
5. Opponent-owned track scoring
6. Leader-follower two-player model

## Excluded for Current Single-player Scope

Multiplayer interaction is intentionally excluded for now. The dissertation prototype focuses on the single-player optimisation problem: building a network, managing money and internal financing, selecting deliveries, upgrading locomotive capacity, and comparing automated decision policies.

This keeps the computational question clear and allows baseline and MCTS agents to be compared without needing to model opponent behaviour.
