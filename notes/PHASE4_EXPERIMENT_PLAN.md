# Phase 4C Experiment Pipeline

Phase 4C evaluates the minimal card framework before adding card-aware search logic.

## Implemented Commands

Run a card-free or card-enabled baseline:

```bash
python experiments/run_experiments.py --agent all --episodes 50 --map data/toy_map.json --cards none
python experiments/run_experiments.py --agent all --episodes 50 --map data/toy_map.json --cards basic
```

Run the quick verification profile:

```bash
python experiments/run_phase4_card_experiments.py --profile quick
```

Run the dissertation-scale standard profile:

```bash
python experiments/run_phase4_card_experiments.py --profile standard
```

Run the stronger MCTS profile when runtime permits:

```bash
python experiments/run_phase4_card_experiments.py --profile mcts100
```

Run the fast pipeline verification:

```bash
python experiments/smoke_test_phase4_experiments.py
```

## Experiment Profiles

| profile | episodes | MCTS iterations | rollout depth | max steps | purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| `quick` | 2 | 5 | 20 | 100 | Fast pipeline verification |
| `standard` | 30 | 25 | 40 | 500 | Dissertation-scale baseline comparison |
| `mcts100` | 20 | 100 | 80 | 500 | Stronger MCTS comparison if runtime permits |

Explicit CLI values override profile defaults.

## Output Files

Each output includes the selected profile name. The standard run writes:

- `results/raw/phase4_standard_card_disabled_results.csv`
- `results/raw/phase4_standard_card_enabled_results.csv`
- `results/summary/phase4_standard_card_comparison_summary.csv`
- `results/summary/phase4_standard_card_comparison_summary.md`
- `results/summary/phase4_standard_card_effect_table.csv`
- `results/summary/phase4_standard_card_effect_table.md`
- `results/summary/phase4_standard_card_usage_table.csv`
- `results/summary/phase4_standard_card_usage_table.md`

## Captured Metrics

The raw results include final score, raw delivery score, major-line bonus, operation-card bonus, end-game card bonus, financing penalty, cards selected, cards completed, active cards, available cards remaining, invalid actions, and runtime.

The full summary groups results by map, card mode, and agent. It reports score distribution, score composition, card-selection frequency, invalid actions, and runtime. The card-effect table directly compares enabled and disabled mean final scores. The card-usage table reports selection, completion, operation-card bonus, and end-game-card bonus for enabled runs.

Validate generated files with:

```bash
python experiments/validate_phase4_card_results.py --profile standard
```

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
