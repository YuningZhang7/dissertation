# Phase 4D Card-Aware Agent Plan

## Purpose

Phase 4D tests whether lightweight card-aware decision guidance improves play under the minimal representative operation-card framework. Phase 4C showed that cards can help, but existing greedy agents often ignore them and fixed-budget MCTS can be distracted by extra card branches on larger scenarios.

The goal is not to add a new optimisation family. It is to add two conservative baselines that still use the existing simulator interface:

- `CardAwareGreedyAgent`
- MCTS with `rollout_policy="card_aware"`

## Card-Aware Greedy Baseline

The card-aware greedy baseline keeps the same one-step action interface as the existing greedy agents. It ranks actions with a small deterministic heuristic:

1. Complete active card objectives when a legal action can do so.
2. Take high-value deliveries.
3. Select a useful available card if the estimated value clears a threshold.
4. Build track that helps deliveries, active card objectives, or major-line progress.
5. Upgrade engine when no stronger immediate action is available.
6. Urbanize when no stronger immediate action is available.
7. Pass if no useful action is available.

To avoid selecting cards blindly, the helper uses:

- `MAX_ACTIVE_CARDS = 3`
- `MIN_CARD_SCORE = 5`

Immediate cash, delivery objectives, network objectives, and end-game scoring cards are scored differently because their value enters the game through different mechanisms.

## Card-Aware MCTS Rollout

The MCTS change is intentionally narrow. The tree policy, UCB selection, state copying, legal action generation, and final evaluation modes are unchanged. The new option only guides rollout action choice:

```bash
rollout_policy="card_aware"
```

This makes the experiment easy to interpret: any change is due to rollout guidance rather than a rewritten MCTS algorithm.

## Experiment Design

The Phase 4D experiment is card-enabled only and compares:

- `greedy_delivery`
- `greedy_expansion`
- `card_aware_greedy`
- `mcts`
- `mcts_majorline`
- `mcts_card_rollout`
- `mcts_majorline_card_rollout`

Maps:

- `toy_map`
- `toy_medium_map`
- `semi_realistic_map`

Standard profile:

- 30 episodes
- MCTS iterations: 25
- rollout depth: 40
- max steps: 500
- seeds 0 to 29

The follow-up comparison script contrasts Phase 4D against the Phase 4C standard card-enabled baselines.

## Expected Interpretation

If the card-aware greedy baseline improves over existing greedy agents, this suggests that the card framework creates useful delayed objectives that simple delivery/build priorities miss.

If card-aware rollouts improve MCTS, this suggests that fixed-budget search benefits from rollout guidance that distinguishes useful card branches from distracting ones.

If results are map-dependent, that is still informative: it would show that cards change the optimisation problem differently depending on network structure, delivery density, and major-line opportunities.
