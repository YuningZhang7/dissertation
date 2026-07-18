# Rules Coverage

## Current Mainline Runtime

The active simulator is a single-player route-segment abstraction. It is not a full implementation of *Railways of the World*. The current dissertation comparison uses the `official_like` and `expanded` artificial route-segment scenarios and the five public agents exposed by `agents/registry.py`.

Legacy edge-only maps and early MCTS/CardAware experiments are not part of the current mainline runtime.

## Implemented State and Turn Rules

- Cities with demand colours, goods, grey-city status, urbanised status, and empty-city markers.
- City-to-city routes represented by ordered track segments.
- Segment terrain labels and fixed scenario-defined costs.
- Single-player ownership of built and completed track.
- Action and income phases.
- Configurable actions per turn.
- `pass` and `next_turn` actions.
- Score-based income.
- Internal automatic financing during paid actions.
- Financing obligation during the income phase.
- Configurable fixed-turn or empty-city-marker end-condition modes.
- Optional extra turn after the end condition is triggered.
- Final scoring from score, financing penalty, Major Line bonus, Rail Baron bonus, and enabled operation-card bonuses.

## Track Construction

A `build_track_segments` action currently follows these rules:

1. It must contain between one and four segments.
2. Every selected segment must exist and must not already be built.
3. All selected segments must belong to the same route.
4. Segment indices must be consecutive and supplied in increasing order.
5. The selected chain must touch one of that route's city endpoints or an existing incomplete endpoint on the same route.
6. The construction cost is paid through available cash and, when enabled, automatic financing.
7. A route becomes completed only when all of its segments are built.
8. Completed routes and segments remain available for delivery and objective checks.
9. Built but incomplete segments are removed during the income phase.

The active validator therefore enforces route-local continuity. The legacy `require_connected_track_building` configuration field is still present in configuration and model data, but the current route-segment validator does not enforce global connection to the player's previously completed network. Documentation and dissertation claims must follow the implemented validator rather than the legacy field name.

## Goods Delivery

A `deliver_good` action currently requires:

- distinct source and target cities;
- the selected good colour to be present at the source;
- the target demand colour to match the good colour;
- the target not to be a grey city;
- an explicit simple path through completed routes owned by the player;
- total path length, measured in completed track segments, not exceeding the locomotive level;
- no intermediate city on the path demanding the same colour, because such a path would skip an earlier valid destination.

A successful delivery removes one good from the source, updates its empty-city marker if necessary, adds path-length-based score, and consumes one action.

## Locomotive Upgrades

- Locomotive level is capped by the configured maximum.
- Upgrade costs are configured by target level.
- Payment can trigger automatic financing.
- Higher levels permit deliveries over longer completed-route paths.

## Financing

- Voluntary `issue_bond` actions are not part of the legal action space.
- Paid actions call `pay_money`.
- If cash is insufficient and automatic financing is enabled, the minimum required number of financing certificates is issued automatically.
- The historical field name `bonds` remains in the code, but it approximates share-certificate financing in this abstraction.
- Each certificate creates an income-phase obligation and a configurable final-score penalty.

## Urbanisation

- Each legal urbanisation action selects one grey city and one allowed demand colour.
- Urbanisation pays the configured cost through the same financing mechanism.
- The city becomes non-grey and receives the chosen demand colour.
- The city receives a configured number of randomly generated goods.
- Random outcomes are controlled by the experiment seed at environment level.

The public `lookahead_greedy` agent uses a deterministic surrogate seed when simulating candidate urbanisation actions. The real environment transition still uses the active experiment random state, so the simulated and realised new goods are not guaranteed to match exactly.

## Major Line and Rail Baron Objectives

- Major Lines are source-target connectivity objectives evaluated on the completed-route graph.
- Each Major Line can be claimed once and awards its configured bonus.
- One active Rail Baron objective is selected for a game state.
- The Rail Baron objective is claimed when its source and target become connected on the completed-route graph.
- Objective bonuses are included in the scoring formula.

These are simplified connection objectives rather than full official card or map-specific implementations.

## Operation Cards

- A small original JSON-defined card framework is implemented.
- The representative example deck is stored at `data/cards_basic.json`.
- Supported representative effects include immediate cash, delivery objectives, network objectives, and end-game bonuses.
- Cards are opt-in environment functionality enabled explicitly through `reset_game(..., card_path=...)`.
- The current Streamlit replay does not supply a card path and is therefore card-disabled.
- The current public benchmark runner also does not supply a card path and is therefore card-disabled.
- The compatibility helper `app.create_game_state()` can load `data/cards_basic.json`, but the current Streamlit `main()` entry path does not use that helper.
- The five public agents do not include a dedicated card-aware policy, so card behaviour is not a primary variable or performance claim in the current dissertation comparison.

## Current Public Agents

- `random`
- `greedy_delivery`
- `greedy_expansion`
- `objective_aware_greedy`
- `lookahead_greedy`

Historical MCTS and CardAware agent implementations were removed from the active source tree during mainline cleanup. Historical notes and generated result artefacts may retain those names for provenance, but they must not be presented as current runtime components.

## Not Yet Implemented

- Full official map data and artwork.
- Individual official track-tile placement and tile inventory.
- Detailed terrain, river, mountain, crossing, and city-entry construction rules.
- Full official action phase and turn-order rules.
- Full official income, dividend, share, and economic model.
- Full official urbanisation deck and city rules.
- Full official empty-city-marker rules for a selected map.
- Full official Railroad Operations Card deck and timing rules.
- Full Rail Baron or Tycoon card system.
- Multiplayer auctions, blocking, shared goods competition, and opponent interaction.
- Opponent-owned route use and payments.
- Genetic Algorithm or Reinforcement Learning agents.
- Proven optimal solution methods for the official-like and expanded scenarios.

## Experimental Interpretation

Results are evidence about the implemented abstraction only. A benchmark must report the map, agents, seed set, step horizon, card setting, terminal rate, score type, and runtime environment.

`GameState.final_score()` can be evaluated before termination. Therefore:

- a score from a terminal state is a **terminal final score**;
- a score at `max_steps` from a non-terminal state is a **truncated score**.

Fixed-horizon truncated scores are valid for equal-budget policy comparison, but they must not be described as completed-game results.

