# Rules Coverage

## Implemented Rules

- Visual railway map using a graph of cities and links.
- Cities with demand colors, goods, urbanized status, gray-city support, and empty city markers.
- Railway links with fixed build costs, built status, and single-player ownership.
- Single-player turn structure with an action phase and income phase.
- Configurable actions per turn.
- Track construction as one city-to-city edge per action.
- Optional connected track-building restriction. With `require_connected_track_building = true`, the first track may start anywhere, then later track must touch the player's existing network. This is a simplifying network-contiguity assumption, not an official fixed-start rule.
- Goods delivery over built links only.
- Explicit route-based delivery actions with a selected `path` field.
- Locomotive level limiting delivery path length.
- Delivery scoring based on path length.
- Rule preventing a delivery from skipping an intermediate city that demands the delivered good color.
- Internal share/bond financing during payments, configurable financing value, and configurable final penalty.
- Financing interest/dividend during income phase.
- Score-based income using a configurable income table.
- Engine upgrades using configurable level-by-level costs.
- Empty city markers when a city loses its last good.
- Fixed-turn end condition.
- Empty-city-marker end condition with optional extra turn after the trigger.
- Simplified urbanize action for gray or non-urbanized cities.
- Major-line data loading, connection-based claiming, one-time bonus scoring, and action-history logging.
- Minimal representative operation-card framework with JSON loading, card selection actions, immediate cash effects, delivery objectives, network objectives, and end-game scoring cards.
- AI-ready environment functions: reset, legal actions, apply action, copy state, terminal check, final score.

## Supervisor Feedback Corrections

- The model has no fixed player starting city, home city, train position, or moving train token.
- The first built edge can be anywhere on the map. If connected track building is enabled, later builds must touch the player's existing network only as a simplifying continuity assumption.
- Goods delivery is based on source-city goods, target demand, built paths, locomotive level, and route validity. It is not based on a player origin city.
- Issuing shares/bonds is no longer exposed as an agent action. The legacy `issue_bond` action is also rejected by the external action interface. Financing is handled internally by `pay_money` when an action cost must be paid and automatic financing is enabled.
- The code still uses the historical field name `bonds` in some places. This currently approximates Railways of the World's share certificate financing mechanism.

## Simplified Rules

- Each city-to-city link is modelled as one edge, not individual track tiles.
- Track costs are fixed edge costs rather than detailed terrain, track tile, river, or mountain costs.
- Connected track building checks only whether a candidate edge touches the player's existing graph; it does not yet enforce tile placement or terrain constraints.
- All built links are owned by the single player.
- Delivery route selection uses explicit simple graph paths, but does not yet model opponent track fees or complex official route constraints.
- Income uses a small configurable score table rather than the full official income chart.
- Share/bond financing is simplified to a fixed certificate value and fixed income-phase obligation.
- Urbanize uses a simple cost, demand color, and random new goods.
- Major lines are represented as source-target connection bonuses rather than full official route cards.
- Operation cards use a small original test deck rather than the official deck or official card text.
- The map is a toy map rather than an official board map.
- End condition can be set to `fixed_turns` or `empty_city_markers`.

## Not Yet Implemented

- Full official action phase details.
- First-player auction and turn-order bidding.
- Full urbanize deck/city rules.
- Full empty city marker rules from each official map.
- Full income and dividend rules.
- Full bond and share/economic model.
- Major Lines with official route requirements and map-specific bonuses.
- Full official Railroad Operations Card deck and full official card timing.
- Full Rail Baron / Tycoon objective-card system.
- Full terrain-based track building.
- Track tile placement and tile limits.
- Official map-specific rules.
- Official Eastern U.S. map data.
- Opponent-owned track scoring.

## Intentionally Excluded for Single-Player Version

- Player-vs-player competition.
- First player auction.
- Turn order bidding.
- Competition for goods.
- Multiplayer blocking and route competition.
- Opponent-owned track scoring.
- Leader-follower model.

## Current Experimental Use

The rule engine is now used by baseline automated agents. These agents are intended as simple benchmarks before implementing MCTS, Genetic Algorithms, Reinforcement Learning, or other advanced optimisation methods.

Baseline, MCTS, and exact-benchmark experiments currently support `micro_map`, `toy_map`, `toy_medium_map`, and `semi_realistic_map`. The maps are artificial and self-created; they are intended to create route-building and delivery trade-offs without using official copyrighted map artwork.

## Phase 3A Map Realism

Phase 3A improves scenario realism by adding `semi_realistic_map`, a larger artificial graph with multiple regions, bottleneck routes, grey cities, varied edge costs, and more major lines.

This improves external validity compared with the small toy maps, but it still does not fully implement official multiplayer rules, official map-specific rules, terrain/tile placement, operation cards, Rail Baron cards, or opponent-owned track scoring.

## Phase 3B Semi-realistic Experiment Reporting

Phase 3B runs baseline and MCTS experiments on `semi_realistic_map`. The results show that the larger map changes algorithm behaviour: `greedy_expansion` benefits strongly from major-line bonuses, while MCTS improves over random and immediate-delivery greed but has higher runtime and does not yet dominate the expansion heuristic.

This phase strengthens experimental reporting, but it does not add new official rules. The same single-player abstractions and exclusions still apply.

## Phase 3D Exact Benchmark

Phase 3D adds exact exhaustive search on `micro_map`. This is an evaluation tool rather than a new game rule: it searches the existing legal-action space to compute the true optimum under the implemented single-player abstraction.

Exact search is intentionally limited to very small instances because the legal action space grows quickly on larger maps.

## Phase 4 Minimal Card Framework

Phase 4 adds a small representative card framework to support fuller-rule modelling without attempting to copy or implement the complete official deck. The framework loads original simplified card definitions from `data/cards_basic.json`, stores available and owned card state, exposes `select_operation_card(card_id)` as a normal player action when cards are enabled, and supports immediate cash, delivery-objective, network-objective, and end-game scoring card types.

Cards are disabled by default in `reset_game` unless a `card_path` is supplied. This keeps existing card-free experiments and the `micro_map` exact benchmark comparable. The Streamlit app enables the basic card deck for demonstration.

## Next Rule-Fidelity Checklist

1. Decide whether each turn should always have exactly three actions or allow a formal end-turn/pass phase.
2. Add official-style route choice details such as opponent track payments if multiplayer is ever reintroduced.
3. Add terrain and tile-level build costs.
4. Improve urbanize rules and goods generation.
5. Calibrate income and share-certificate financing rules against the selected official map/ruleset.
6. Expand the minimal card framework toward a selected official-like operation-card subset.
7. Add Rail Baron / Tycoon objective-card support.
8. Expand major-line validation to match official card/map requirements.
9. Calibrate `semi_realistic_map` and scenario-specific configs against dissertation experiment needs.
10. Add automated test coverage for edge cases before implementing advanced AI.
