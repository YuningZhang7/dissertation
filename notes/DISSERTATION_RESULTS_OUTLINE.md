# Dissertation Results Outline

This outline is a writing aid for the Results, Discussion, and Evaluation chapters. It is not a finished dissertation chapter. Wording should remain cautious: the project is a single-player optimisation abstraction, not a full official implementation of Railways of the World.

## RQ1: Can the simulator represent a useful single-player railway optimisation abstraction?

Evidence:

- Implemented a rule-based simulator with cities, possible railway links, goods, demands, track building, deliveries, money, financing, locomotive upgrades, urbanisation, major-line bonuses, and representative operation cards.
- Corrected the action model after supervisor feedback:
  - no fixed start city, home city, train position, or moving train token
  - delivery source chosen from cities containing goods
  - financing handled internally through `pay_money`
  - external `issue_bond` actions rejected by `apply_action`
- Legal action interface supports Random, Greedy, MCTS, exact search, and UI play through the same state transition functions.
- Smoke tests cover rule transitions, financing, delivery paths, cards, agents, MCTS, exact search, and the Streamlit import path.
- Exact benchmark on `micro_map` gives a known optimum and validates replay of the optimal action sequence.

Possible wording:

The simulator is sufficiently expressive for controlled optimisation experiments, while deliberately excluding multiplayer auction, opponent interaction, official map detail, and the full official card deck.

## RQ2: How do baseline agents behave?

Evidence:

- Random agent provides a low-structure baseline.
- GreedyDelivery prioritises immediate deliveries and can perform well on small delivery-dense maps.
- GreedyExpansion prioritises network growth and major-line potential but can overbuild or accumulate financing penalties.
- MCTS improves planning quality by searching legal action sequences.
- Major-line-aware MCTS introduces a domain-specific evaluation signal for longer-term connection goals.
- Exact benchmark on `micro_map` shows:
  - exact optimum: 10
  - GreedyDelivery reaches the optimum on this small instance
  - limited-budget MCTS approaches the optimum but is not always exact

Discussion angle:

Baseline behaviour is interpretable: greedy policies reveal the trade-off between immediate delivery and expansion, while MCTS is more flexible but budget-sensitive.

## RQ3: What changes when representative operation cards are added?

Evidence:

- Phase 4C compares card-disabled and card-enabled versions of the same maps and agents.
- The card framework supports original simplified cards:
  - immediate cash
  - delivery objectives
  - network objectives
  - end-game scoring
- Card-enabled play changes score composition:
  - operation-card bonus
  - end-game-card bonus
  - changes in delivery score
  - changes in major-line bonus
  - changes in financing penalty
- Random and MCTS select cards on all maps.
- Existing greedy agents often ignore cards on larger maps because their priorities are not card-aware.
- Card-enabled MCTS benefits on `toy_map` and `toy_medium_map`, but ordinary MCTS slightly declines on `semi_realistic_map` under the standard budget.

Discussion angle:

Cards make the environment a richer sequential optimisation problem with delayed rewards and optional objectives. The benefit of cards depends on whether an agent can coordinate card selection with future deliveries and network construction.

## RQ4: Does higher MCTS budget solve card branching?

Evidence:

- Phase 4C-MCTS100 increases MCTS iterations from 25 to 100 and rollout depth from 40 to 80.
- Absolute MCTS scores improve, especially on medium and semi-realistic maps.
- Runtime rises substantially.
- The card effect on `semi_realistic_map` does not improve:
  - ordinary MCTS card effect becomes more negative in the 10-episode diagnostic
  - major-line-aware MCTS card effect is neutral in that run

Discussion angle:

More search improves raw planning quality, but it does not by itself solve the card branching problem. A larger budget can still spend effort on card plans that reduce delivery or major-line value.

## RQ5: Do card-aware heuristics help?

Evidence:

- Phase 4D adds:
  - `CardAwareGreedyAgent`
  - MCTS with `rollout_policy="card_aware"`
- Card-aware greedy:
  - improves over greedy expansion on all maps
  - improves over greedy delivery on `toy_map` and `semi_realistic_map`
  - underperforms greedy delivery on `toy_medium_map`
- Card-aware MCTS rollout improves over ordinary card-enabled MCTS on all three maps:
  - +7.33 on `toy_map`
  - +13.07 on `toy_medium_map`
  - +62.50 on `semi_realistic_map`
- Card-aware major-line rollout also improves over major-line-aware MCTS on all three maps.
- Runtime cost increases substantially, especially on `semi_realistic_map`.

Discussion angle:

Card-aware rollout guidance helps MCTS convert card opportunities into better plans, but this is a score-runtime trade-off. The result supports card-aware search guidance as a useful extension, not as a final optimised algorithm.

## Limitations

- Single-player abstraction only.
- Not a full official implementation of Railways of the World.
- No multiplayer auction, opponent track usage, or player interaction.
- No official full map.
- No full official operation-card deck.
- Representative cards are original simplified cards.
- Terrain and tile-level track placement are abstracted as graph edges.
- Financing field names still use `bonds` for compatibility, approximating share certificates.
- Experimental maps are artificial research scenarios.
- MCTS results depend on finite seeds, rollout policy, candidate action generation, and local runtime budget.
- Phase 4D card-aware heuristics are hand-designed and not exhaustively tuned.

## Future Work

- Expand the card framework with a broader representative operation-card set.
- Add Rail Baron / Tycoon-style objective cards in a controlled abstraction.
- Improve card-aware MCTS with explicit value features or learned rollout policies.
- Compare larger map sets and more seed runs.
- Add sensitivity analysis for financing, major-line bonus values, and card reward values.
- Consider GA or reinforcement learning only after the current rule abstraction and card framework are stable.
- Explore multiplayer interaction as a separate future model rather than mixing it into the current single-player experiments.
