# Phase 4 Card Discussion Points

## What Changed After Adding Cards?

The representative card framework adds optional actions, delayed rewards, and alternative scoring routes. Under the implemented abstraction, an agent can spend an action selecting a card instead of immediately building, delivering, upgrading, or urbanising. This changes both the available action space and the composition of final score.

## Which Agents Used Cards?

Random and MCTS agents can select cards because they sample or search legal actions. Their card use should be evaluated through cards selected, cards completed, operation-card bonus, end-game-card bonus, and the resulting final-score change. Existing greedy agents may select few or no cards when their fixed priorities continue to find delivery, build, or upgrade actions.

In the 30-episode standard run, Random selected 4.87 to 7.03 cards per episode and both MCTS variants selected 5.07 to 7.93. The greedy agents selected all eight cards on `toy_map`, where their higher-priority actions eventually became exhausted, but selected none on `toy_medium_map` or `semi_realistic_map`.

## Why Did Greedy Agents Ignore Cards?

The current greedy agents were designed for the basic-rule simulator. Their priorities value immediate delivery and network expansion, but do not estimate delayed card rewards. Ignoring cards is therefore evidence about the limits of the existing heuristic under the fuller action model, not evidence that cards themselves have no value.

## Why Can Cards Help MCTS?

MCTS can discover card value when rollouts connect selection to later deliveries, network completion, or end-game scoring. Cards may reward routes that are not attractive under immediate delivery score alone, giving search a reason to coordinate actions over a longer horizon.

The standard run supports this interpretation on `toy_map` and `toy_medium_map`: card-enabled MCTS improved by 20.90 and 5.73 mean points, while major-line-aware MCTS improved by 22.07 and 5.50.

## Why Can Cards Hurt or Complicate MCTS?

Every available card adds another branch. Objective cards also delay their reward until later actions satisfy a condition. With a fixed iteration budget, the search must spread simulations across more actions and may not revisit a promising card branch often enough. Stronger MCTS budgets should therefore be interpreted alongside runtime and branching cost.

On `semi_realistic_map`, ordinary MCTS declined by 1.43 mean points and major-line-aware MCTS changed by only +0.33. Card bonuses were offset by lower delivery and major-line components. This is preliminary evidence that added options can make a fixed search budget less effective even when those options contain real rewards.

## What Does This Say About the Optimisation Problem?

The fuller rule model is a richer sequential network optimisation problem than the basic-rule version. Decisions now trade immediate deliveries and construction against optional objectives whose benefits depend on future network and delivery choices. This supports studying both score performance and behaviour, rather than treating final score as the only useful outcome.

## What Does the mcts100 Budget Check Show?

The 10-episode mcts100 diagnostic increased MCTS from 25 to 100 iterations and rollout depth from 40 to 80. Absolute performance improved strongly on `toy_medium_map` and `semi_realistic_map`, confirming that the standard search budget constrained overall solution quality.

The card-specific result was mixed. Card effects stayed strongly positive on `toy_map`, became slightly smaller on `toy_medium_map`, and did not improve on `semi_realistic_map`. Ordinary MCTS changed from a -1.43 card effect under the standard profile to -5.00 under mcts100. Major-line-aware MCTS changed from +0.33 to 0.00.

This suggests that simply increasing search budget is not enough to resolve the semi-realistic card trade-off. High-budget agents still selected and completed cards, but card-enabled plans lost delivery and major-line value relative to card-disabled plans. A card-aware rollout policy or evaluation feature may help the search distinguish cards that complement the current network plan from cards that distract from it.

The result remains map-dependent. Cards were consistently valuable on the simpler `toy_map` and remained beneficial on `toy_medium_map`. The larger semi-realistic scenario presents more competing network, delivery, major-line, financing, and card priorities. Further testing is required before claiming that a card-aware agent is generally superior.

## What Does Phase 4D Add?

Phase 4D tests that next step directly. It adds a lightweight card-aware greedy baseline and a card-aware MCTS rollout policy without changing the core rules, financing model, action interface, or MCTS tree policy.

The card-aware greedy baseline shows that explicit card heuristics can help, but also that greedy card use is not automatically superior. It improves over greedy delivery on `toy_map` and `semi_realistic_map`, but scores 23.00 on `toy_medium_map` compared with greedy delivery's 32.00. In that case, selecting and completing cards comes at too high a delivery-score cost.

The card-aware rollout result is stronger. Compared with Phase 4C card-enabled MCTS, card-aware rollout improves mean final score by +7.33 on `toy_map`, +13.07 on `toy_medium_map`, and +62.50 on `semi_realistic_map`. The major-line-aware card rollout also improves by +6.80, +13.33, and +32.07 on the same maps.

This supports the interpretation that MCTS needed better rollout guidance rather than only a larger budget. However, the result is not free: on `semi_realistic_map`, card-aware rollout raises ordinary MCTS mean runtime from about 14.21 seconds to 41.51 seconds per episode. This makes Phase 4D a score-runtime trade-off rather than a simple dominance result.

## Limitations

- The cards are an original simplified representative deck, not the full official deck.
- The maps are artificial research scenarios.
- Existing greedy and MCTS policies are not card-aware in Phase 4C.
- Finite samples and MCTS budget affect estimated performance.
- The mcts100 diagnostic used 10 episodes, compared with 30 for the standard profile.
- Higher-budget runtime was approximately four times the standard MCTS runtime on larger maps.
- Results describe the implemented single-player abstraction, not the full official multiplayer game.
