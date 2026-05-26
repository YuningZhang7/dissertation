# Scenario Design

## Existing Scenarios

### toy_map

Purpose:

- debugging
- smoke tests
- small example

### micro_map

Purpose:

- exact-search benchmark
- optimality-gap comparison
- very small deterministic instance

### toy_medium_map

Purpose:

- baseline comparison
- first MCTS experiments
- medium complexity

### semi_realistic_map

Purpose:

- stronger external validity
- larger graph
- more strategic trade-offs
- closer to a full single-player optimisation problem

## Scenario Comparison Plan

Compare algorithms across:

- `micro_map`
- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Metrics:

- final_score
- raw_score
- deliveries
- built_edges
- bonds
- major_line_bonus
- runtime_seconds
- invalid_action_rate
- terminal_rate
- optimality_gap, for `micro_map`

## Expected Difficulty

The `micro_map` should be easy enough for exhaustive search, but still contain a small trade-off between short deliveries and a delayed major-line bonus.

The semi-realistic map should be harder because:

- more actions are available;
- more long-term network planning is required;
- locomotive upgrades matter more;
- major lines require larger investments;
- grey/non-urbanized cities make urbanisation choices more meaningful;
- regional bottlenecks make early network expansion choices more important.

## Map Design Notes

The `semi_realistic_map` is self-created and artificial. It is not copied from official artwork. It uses four broad regions:

- north-west cluster;
- north-east cluster;
- central hub region;
- south/coastal cluster.

The main bottlenecks connect the north-west to the centre, the centre to the north-east, and the centre to the south/coastal region. This is intended to create trade-offs between short local deliveries, major-line investment, and locomotive upgrades.

## Semi-realistic Scenario Observations

The Phase 3B experiments show that `semi_realistic_map` produces meaningful differences between agents:

- `random` remains weak and variable, with mean final score 3.84 in the 50-episode baseline run.
- `greedy_delivery` achieves a stable mean final score of 22.00 by prioritising immediate deliveries.
- `greedy_expansion` reaches mean final score 87.00 by exploiting the larger map's major-line opportunities.
- `mcts_50` and `mcts_100` outperform `random` and `greedy_delivery`, but do not beat `greedy_expansion` in the current random-rollout configuration.
- Runtime is much higher for MCTS on the semi-realistic map, which confirms that the larger scenario is a more demanding search problem.

These results suggest that the semi-realistic map is useful for future GA, exact benchmark, or tuned MCTS experiments because it rewards longer-term network planning rather than only short delivery selection.
