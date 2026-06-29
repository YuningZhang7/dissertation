# Phase 6: Single-Player Official-Rule-Compatible Refactor

## Purpose

The simulator will remain a single-player railway optimisation environment while
moving its non-competitive mechanics closer to the functional rules of
*Railways of the World*. The target is an official-rule-compatible abstraction,
not a complete digital reproduction of the physical board game.

This distinction matters for the dissertation. The simulator should capture the
decisions that affect network optimisation—financing, construction, delivery,
engine capacity, urbanisation, objectives, income, and game end—without claiming
to reproduce every physical component or multiplayer interaction.

## Current Simplified Assumptions

The current implementation deliberately simplifies several rules:

- one player owns every constructed link;
- a build action constructs one complete city-to-city graph edge;
- track costs are fixed per edge rather than per terrain segment;
- incomplete track does not exist and therefore cannot be removed at income;
- the default scenario starts with money and does not expose voluntary bonds;
- the default locomotive limit is six;
- urbanisation and goods generation use a representative rule;
- operation cards use a small original test deck and a simple availability list;
- Rail Baron/Tycoon private objectives are not yet modelled;
- artificial graph maps stand in for an official board; and
- the default game can end after a fixed number of turns.

These assumptions remain valid for the existing scenarios and archived
experiments. Phase 6 introduces separate data and compatibility paths so old
experiments can still be reproduced.

## Target Scope

The Phase 6 target is a `single-player official-rule-compatible railway
optimisation simulator` with:

- one player and one agent;
- three actions followed by an income phase;
- voluntary and automatic bond financing;
- route-segment construction with terrain costs;
- at most four consecutive segments per build action;
- removal of incomplete track during the income phase;
- delivery over completed track, limited by locomotive level and city colour;
- grey-city urbanisation, goods placement, and empty-city-marker handling;
- locomotive levels up to eight;
- major-line rewards and representative operation-card timing categories;
- an optional private Rail Baron/Tycoon end-game objective;
- an empty-city-marker end trigger followed by one final full turn; and
- final scoring that includes bonuses and bond penalties.

## Deliberate Exclusions

Multiplayer state, opponents, first-player auctions, player-order bidding,
opponent-track payments, competitive route blocking, and multiplayer
tie-breakers are out of scope. First-player auction is omitted because turn
order has no strategic meaning in a single-player optimisation setting.

Exact hex placement is also out of scope. Reproducing tile orientation,
inventory, and board geometry would add a large physical-placement subsystem
without being necessary to study the main optimisation decisions selected for
this dissertation.

## Route-Segment Abstraction

A `Route` represents a potential city-to-city connection. Ordered
`TrackSegment` objects represent the smaller pieces of that route. Each segment
records its endpoints, terrain, cost, construction state, and owner.

This abstraction preserves the functional consequences of physical track
placement:

- a build action can place one to four consecutive pieces;
- construction cost is the sum of segment terrain costs;
- a build chain stops when it reaches the destination city;
- a partially built route has an exposed endpoint; and
- built but incomplete segments can be removed during income.

The loader should accept both legacy `edges` maps and new `routes` maps. Legacy
maps continue to use the existing edge rules; the official-like map uses the
segment rules.

Phase 6C-1 introduced the `Route` and `TrackSegment` data structures and
dual-format map loading. Phases 6C-2 through 6E-1 subsequently added segment
construction, route completion and cleanup, segment-distance delivery, and
route-based major-line scoring.

Phase 6E-2 adds `official_like_route_segment_map.json`, a medium-sized
single-player scenario for experiments. It is an original functional abstraction,
not a reproduction of an official board, and exercises route construction,
delivery, major-line scoring, grey-city urbanisation, bond financing, and income
cleanup. `mini_route_segment_map.json` remains the compact unit-test map; the
official-like scenario is intended for scenario smoke tests and later agent
evaluation.

Phase 6F-1 adds a deterministic baseline evaluation runner for the official-like
route-segment scenario. It compares the existing baseline agents using repeatable
episode seeds and records per-episode CSV metrics plus aggregated JSON metrics for
later dissertation analysis. The runner provides baseline behaviour and
sanity-check evidence for the implemented rules; it is not evidence of optimality.

## Planned Rule Changes

Implementation will proceed in small, testable increments:

1. Add a separate official single-player configuration. It starts with zero
   money, permits voluntary and automatic bonds, uses three actions, supports
   locomotive levels through eight, and uses the empty-city-marker end rule.
2. Restore `issue_bond` as a legal zero-action-cost decision. Each bond adds
   five money, costs one interest at income, cannot be repaid, and subtracts one
   final victory point. Automatic financing remains available for required
   payments.
3. Restrict urbanisation to grey cities, charge the configured cost, assign a
   valid city colour, add two goods, and remove an existing empty-city marker.
4. Tighten delivery validation before the map refactor: reject grey
   destinations, enforce locomotive range, prevent passing through a matching
   city, require player ownership of the first link, and score by path length.
5. Add `Route` and `TrackSegment`, dual-format map loading, segment build legal
   actions, route completion, and major-line checks.
6. Remove incomplete route segments during income while preserving completed
   routes and recording all removals in action history. Delivery distance then
   changes from edge count to completed segment count.
7. Add a medium-sized artificial official-like map with coloured and grey
   cities, initial goods, varied terrain, major lines, and enough goods to make
   the empty-city-marker end condition meaningful.
8. Evolve operation-card storage toward deck, display, owned, and discard
   areas, with objective, once-per-turn, immediate, held, passive, and end-game
   timing categories. This remains a representative original card set rather
   than a copy of the official deck.
9. Add a small configurable Rail Baron/Tycoon objective model and include its
   earned bonus in final scoring.
10. Update agents only after the new rule tests pass. Existing agents remain
    baselines; advanced search and agent optimisation are not part of the rule
    refactor.

The provisional engine upgrade costs in
`data/official_single_player_rules_config.json` are a configurable approximation
for the simulator. They must be described as such in dissertation reporting and
can be calibrated later without changing rule-engine code.

## Compatibility Strategy

- Do not change `data/rules_config.json` or the legacy artificial maps in place.
- Add new models and actions alongside compatibility wrappers where practical.
- Keep `build_track(edge_id)` for legacy maps while official-like route maps use
  `build_track_segments(segment_ids)`.
- Preserve existing smoke tests and add focused Phase 6 tests.
- Keep archived experiment outputs labelled with the rules/configuration that
  produced them; results from old and Phase 6 rulesets are not directly pooled.

## Validation Strategy

`experiments/smoke_test_official_single_player_rules.py` will become the Phase 6
acceptance test. It will verify configuration loading and initial state, bond
issuance and interest, final bond penalties, urbanisation constraints and ECM
removal, delivery constraints, ECM end timing, segment build limits, incomplete
track cleanup, and preservation of completed routes.

During implementation:

- run the focused Phase 6 smoke test after every rule increment;
- run `experiments/smoke_test_rules.py` to detect legacy-rule regressions;
- run map, agent, card, and experiment smoke tests after data-model changes;
- use deterministic seeds when testing random goods placement; and
- run short episodes on both a legacy edge map and the official-like route map
  before larger experiments.

Phase 6 is complete only when the official smoke test passes, legacy scenarios
still load, and a short experiment can finish using the official-like map and
official single-player configuration.
