# Experiment Plan

## Phase 2B Goal

Use the current single-player rule engine as a repeatable benchmark environment for simple baseline strategy agents.

Advanced AI methods are intentionally postponed. The immediate goal is to establish clear baselines and reliable result collection.

## Agents To Compare

- `random`: samples uniformly from legal actions.
- `greedy_delivery`: prioritises immediate delivery score, then simple build/upgrade/urbanize choices.
- `greedy_expansion`: prioritises builds that improve future delivery opportunities, major-line bonuses, and network expansion.

## Metrics

- Final score.
- Raw delivery score.
- Bonds.
- Money.
- Deliveries.
- Built edges.
- Major line bonus.
- Empty city markers.
- Turns.
- Actions taken.
- Invalid actions.
- Runtime seconds.

## Commands

Run all baseline agents:

```bash
python experiments/run_experiments.py --agent all --episodes 100
```

Analyse results:

```bash
python experiments/analyse_results.py --input results/raw/experiment_results.csv
```

Generate plots:

```bash
python experiments/plot_results.py --input results/raw/experiment_results.csv
```

## Interpretation Plan

Compare each baseline by mean final score and stability across seeds. Use deliveries, bonds, built edges, and major-line bonus to explain why one agent performs better or worse. These results will become the reference point for later MCTS, Genetic Algorithm, or Reinforcement Learning experiments.
