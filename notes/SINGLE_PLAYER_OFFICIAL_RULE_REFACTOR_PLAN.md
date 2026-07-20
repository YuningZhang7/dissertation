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
experiments. Phase 6 originally introduced separate data and compatibility paths so old
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

Phase 6F-2 adds a route-segment-aware greedy heuristic agent. Unlike the earlier
legacy-oriented greedy agents, it prioritises completed-route deliveries and
segment builds that complete or extend useful routes. It is intended as a stronger
interpretable baseline, not an optimal solver.

Phase 6F-3 adds an expanded official-style route-segment scenario map. The new map
is a fictional experimental network and is not a reproduction of the official
board. It increases the number of cities, route corridors, terrain-dependent track
segments, gray cities, and major-line objectives to provide a more strategically
varied environment for agent evaluation.

The project now uses three route-segment maps:

- `mini_route_segment_map.json`: unit tests
- `official_like_route_segment_map.json`: small scenario and smoke tests
- `expanded_official_style_route_segment_map.json`: larger experiment scenario

The expanded map still uses predefined route corridors. It does not implement full
hex-tile placement or free-form track drawing.

Phase 6F-4 adds a single-player Rail Baron-style objective system. Each compatible
map can define Rail Baron objectives as source-target connection goals. At game
reset, one active objective is assigned deterministically unless an explicit
objective ID is provided. When the player connects the objective endpoints through
the player-owned completed-route network, the objective is claimed and a one-time
bonus is awarded.

This is an official-style abstraction rather than a full reproduction of an
official Rail Baron deck. Multiplayer, auction, operation-card deck handling, and
full official-board reproduction remain outside the scope.

Phase 6F-5 adds a lightweight state visualization and replay facility. It renders
route-segment maps, city state, built and completed track, major lines, and the
active Rail Baron objective. The feature is intended for debugging and dissertation
presentation rather than as a full interactive GUI.

Phase 6F-6 adds a non-interactive agent animation viewer. It provides both a CLI
animation generator and a lightweight Streamlit replay launcher. The user
selects a map, a registered agent, seed, maximum steps, and frame mode, and the
system automatically runs an episode. The output includes a compact HTML replay
viewer with playback controls, a main animation frame, an action-history panel,
PNG frames, logs, and summary JSON. The replay launcher embeds that generated
replay and reports its output path and summary metrics. It is intended for
interactive inspection and debugging, not manual gameplay. `--frame-mode all` captures
every action, while `--frame-mode events` limits rendered frames to key events while
retaining the complete action history. Launch the demo with
`streamlit run experiments/agent_replay_app.py`.

Phase 6F-7 introduced an objective-aware greedy agent. Unlike the earlier
`route_segment_greedy` baseline, this agent scores candidate actions using one-step
simulation and explicit progress toward deliveries, Rail Baron objectives, Major
Lines, route completion, and debt-adjusted cost. The agent remains deterministic
and interpretable; it is intended as a stronger heuristic baseline rather than an
optimal planner. It is still a one-step heuristic, does not search over full plans,
and may make locally reasonable but globally suboptimal decisions.

Phase 6F-8 introduced `adaptive_objective_greedy`, a stronger deterministic
heuristic baseline. It extends `objective_aware_greedy` with phase-aware weights,
objective ROI scoring, debt-level-sensitive penalties, future delivery value
estimation, stronger incomplete-route handling, and optional bounded shallow
lookahead over top candidate actions. Lookahead is implemented but disabled by
default so expanded-map runs remain lightweight. The agent remains interpretable
and does not use learning, MCTS, or full-plan search. It is still heuristic, has no
global-optimality guarantee, and relies on hand-designed weights that should be
evaluated empirically.

Phase 6F-9 introduced a reproducible multi-seed benchmark runner for comparing
registered agents across the official-like and expanded maps. It writes per-episode
CSV rows, grouped JSON summaries, and a Markdown summary. The benchmark is intended
for development comparison of heuristic baselines, not final dissertation results.
It can compare `route_segment_greedy`, `objective_aware_greedy`, and
`adaptive_objective_greedy` over multiple seeds and longer episodes before deciding
whether additional heuristic tuning is justified.

Phase 6F-10 extended the benchmark system with behaviour diagnostics and
recommendation support. In addition to final score, it records action mix, bond
usage, estimated build cost, score efficiency, deliveries and routes per bond, and
objective claim events. The analysis helper identifies the best-performing
heuristic per map and highlights whether `adaptive_objective_greedy` improves on
`objective_aware_greedy`. Recommendations remain benchmark-based: when
`objective_aware_greedy` leads longer runs, it is the default replay-interface
heuristic while `adaptive_objective_greedy` remains experimental.

### Phase 6F-11: Agent Replay Interface Cleanup

Phase 6F-11 polished the Streamlit replay interface as a formal project component.
The interface now defaults to `objective_aware_greedy`, hides baseline and
experimental agents unless requested, and includes concise rule, agent, and
benchmark status panels. Follow-up corrections made financing automatic-only and
made the normal runtime route-segment-only. Construction now uses
`build_track_segments`, delivery requires completed routes, and Major Line and Rail
Baron connectivity use the completed-route graph. Historical edge-map data remains
in the research repository but is rejected by the normal runtime and excluded from
the presentation package.

## Planned Rule Changes

Implementation will proceed in small, testable increments:

1. Add a separate official single-player configuration. It starts with zero
   money, permits voluntary and automatic bonds, uses three actions, supports
   locomotive levels through eight, and uses the empty-city-marker end rule.
2. Keep bond issuance internal to payment handling. When cash is insufficient and
   automatic financing is enabled, issue only the financing certificates needed to
   cover the shortfall. Financing is not a selectable player action; certificates
   still cost one interest at income, cannot be repaid, and subtract one final
   victory point.
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
- Historical edge-map files remain available only as research artifacts; the normal
  runtime rejects maps without routes and track segments.
- Use `build_track_segments(segment_ids)` as the only construction action.
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
- run short episodes on both the official-like and expanded official-style
  route-segment maps before larger experiments.

Phase 6 is complete only when the official smoke test passes, legacy edge-only maps
are rejected clearly, and short experiments finish on both route-segment maps with
the official single-player configuration.
