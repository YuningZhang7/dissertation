# Phase 4C Experiment Plan

Phase 4C should evaluate the minimal card framework before adding card-aware search logic.

Planned experiments:

1. Compare existing agents on card-disabled vs card-enabled `toy_map`.
2. Compare existing agents on card-enabled `semi_realistic_map`.
3. Measure whether agents select useful cards or mostly ignore card actions.
4. Report final-score components separately:
   - delivery score
   - major-line bonus
   - operation-card bonus
   - end-game card bonus
   - financing penalty
5. Consider card-aware MCTS only after baseline card-enabled experiments show where current agents struggle.

This phase should not add the full official card deck, multiplayer interaction, GA, or RL. Its purpose is to establish whether the representative card framework changes the optimisation landscape enough to justify card-aware agent design.
