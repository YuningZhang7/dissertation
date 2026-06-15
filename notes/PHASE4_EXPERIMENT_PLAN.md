# Phase 4C Experiment Pipeline

Phase 4C evaluates the minimal card framework before adding card-aware search logic.

## Implemented Commands

Run a card-free or card-enabled baseline:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --map data/toy_map.json --cards none
python experiments/run_experiments.py --agent all --episodes 50 --map data/toy_map.json --cards basic
```

Run the standard comparison pipeline:

```bash
python experiments/run_phase4_card_experiments.py
```

Run the fast pipeline verification:

```bash
python experiments/smoke_test_phase4_experiments.py
```

## Output Files

- `results/raw/phase4_card_disabled_results.csv`
- `results/raw/phase4_card_enabled_results.csv`
- `results/summary/phase4_card_comparison_summary.csv`
- `results/summary/phase4_card_comparison_summary.md`

## Captured Metrics

The raw results include final score, raw delivery score, major-line bonus, operation-card bonus, end-game card bonus, financing penalty, cards selected, cards completed, active cards, available cards remaining, invalid actions, and runtime.

The summary groups results by map, card mode, and agent. It reports score distribution, score composition, card-selection frequency, invalid actions, and runtime.

## Interpretation Plan

1. Compare existing agents on card-disabled vs card-enabled `toy_map`.
2. Compare existing agents on card-disabled vs card-enabled `toy_medium_map` and `semi_realistic_map`.
3. Measure whether agents select useful cards or mostly ignore card actions.
4. Report final-score components separately:
   - delivery score
   - major-line bonus
   - operation-card bonus
   - end-game card bonus
   - financing penalty
5. Consider card-aware MCTS only after baseline card-enabled experiments show where current agents struggle.

## Limitations

The current agents are not card-aware. Any card use emerges from the existing legal-action interface and current action priorities. The representative cards are original simplified test cards rather than the official deck. The exact `micro_map` benchmark remains card-disabled and is not part of this comparison.

This phase does not add the full official card deck, multiplayer interaction, GA, or RL. Its purpose is to establish whether the representative card framework changes the optimisation landscape enough to justify card-aware agent design.
