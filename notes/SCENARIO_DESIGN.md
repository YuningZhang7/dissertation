# Scenario Design

## Existing Scenarios

### toy_map

Purpose:

- debugging
- smoke tests
- small example

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

## Expected Difficulty

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
