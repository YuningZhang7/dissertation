# Current Dissertation Experiment Plan

## Status

This document defines the current five-agent route-segment benchmark. Earlier MCTS, card-aware, edge-only, and toy-map plans are historical and should not be used as the main dissertation methodology.

The active agents are:

- `random`
- `greedy_delivery`
- `greedy_expansion`
- `objective_aware_greedy`
- `lookahead_greedy`

The active benchmark maps are:

- `official_like`
- `expanded`

## Research Questions

### RQ1 — Behaviour

How do the five interpretable agents differ in delivery, route construction, locomotive upgrades, urbanisation, financing, and objective completion?

### RQ2 — Objective Awareness

Does `objective_aware_greedy` improve over simple delivery-only and expansion-only heuristics under the same map, seed set, and action horizon?

### RQ3 — Bounded Lookahead

Does `lookahead_greedy` improve decision quality over the one-step objective-aware baseline, and what runtime cost does it introduce?

### RQ4 — Scenario Scale

How do agent quality, behaviour, and runtime change from the compact `official_like` map to the larger `expanded` map?

### RQ5 — Robustness

Are observed rankings stable across seeds, or are they driven by a small number of replay-friendly runs such as seed 42?

## Experimental Principles

1. Use the same seed set for every agent within a map and protocol.
2. Keep map, config, card setting, and `max_steps` fixed within a comparison.
3. Treat seed 42 as a demo seed only, not as standalone evidence.
4. Report unsuccessful runs, fallback actions, and non-terminal episodes rather than silently dropping them.
5. Report runtime separately from score and do not treat a slower agent as uniformly better without discussing computational cost.
6. Do not combine results produced by different model versions or removed agents in the primary tables.
7. Keep the current benchmark card-disabled unless a separate card experiment is explicitly defined.

## Score Semantics

`GameState.final_score()` applies the scoring formula to the state at the point where execution stops. The benchmark must distinguish:

- **Terminal final score**: the environment reached game over.
- **Truncated score**: execution reached `max_steps` before game over.

The CSV retains the historical `final_score` field for compatibility, but it should be interpreted as the **evaluation score at the stopping point**. The row-level `terminal` and `score_type` fields identify whether it is a terminal final score or a truncated score.

Do not write “mean final score” for a group containing non-terminal episodes without qualification. Prefer:

- “mean evaluation score at the 60-step horizon”; or
- “mean terminal final score”, when all included rows are terminal.

## Protocol A — Primary Compact-Map Comparison

Purpose: compare all five agents under a common fixed action budget on the main dissertation scenario.

Recommended settings:

```text
Map: official_like
Agents: all five public agents
Episodes: 20
Seeds: 1000–1019
Maximum steps: 60
Cards: disabled
```

Command:

```bash
python experiments/run_agent_benchmark.py \
  --maps official_like \
  --agents random greedy_delivery greedy_expansion objective_aware_greedy lookahead_greedy \
  --episodes 20 \
  --max-steps 60 \
  --base-seed 1000 \
  --output-dir experiments/results/formal_benchmark/official_like_60
```

Why 20 seeds:

- it is large enough to move beyond anecdotal single-seed evidence;
- it supports paired seed-by-seed comparisons;
- it remains computationally practical for the slower lookahead agent.

If runtime permits, repeat with 30 seeds before final submission. Do not change the seed count after inspecting which count produces a preferred ranking.

## Protocol B — Horizon Sensitivity

Purpose: determine whether agent rankings depend on the chosen truncation horizon.

Run the compact-map comparison at:

```text
30 steps
60 steps
90 steps
```

Use the same 20 seeds and all five agents for each horizon.

Commands follow the Protocol A command with only `--max-steps` and `--output-dir` changed.

Interpretation:

- 30 steps represents short-term planning and matches the meeting replay horizon;
- 60 steps is the primary dissertation fixed-horizon comparison;
- 90 steps tests whether rankings persist later in play.

Horizon analyses must be reported as fixed-horizon evaluation scores unless all runs terminate.

## Protocol C — Expanded-Map Scalability

Purpose: evaluate how the larger action space affects behaviour and runtime.

### C1: Main expanded comparison for faster agents

```text
Map: expanded
Agents: random, greedy_delivery, greedy_expansion, objective_aware_greedy
Episodes: 20
Seeds: 2000–2019
Maximum steps: 60
Cards: disabled
```

```bash
python experiments/run_agent_benchmark.py \
  --maps expanded \
  --agents random greedy_delivery greedy_expansion objective_aware_greedy \
  --episodes 20 \
  --max-steps 60 \
  --base-seed 2000 \
  --output-dir experiments/results/formal_benchmark/expanded_fast_agents_60
```

### C2: Focused lookahead scalability pilot

```text
Map: expanded
Agents: objective_aware_greedy, lookahead_greedy
Episodes: 5
Seeds: 2000–2004
Maximum steps: 30
Cards: disabled
```

```bash
python experiments/run_agent_benchmark.py \
  --maps expanded \
  --agents objective_aware_greedy lookahead_greedy \
  --episodes 5 \
  --max-steps 30 \
  --base-seed 2000 \
  --output-dir experiments/results/formal_benchmark/expanded_lookahead_pilot_30
```

C2 is a scalability pilot, not a full-quality ranking. Its purpose is to quantify runtime growth and determine whether a larger expanded-map lookahead experiment is feasible. The dissertation should explicitly state the smaller sample and shorter horizon.

## Protocol D — Demo Reproducibility Check

Purpose: retain a reproducible presentation example without confusing it with formal evidence.

```text
Map: official_like
Agent: lookahead_greedy
Seed: 42
Maximum steps: 30
Frame mode: events
```

```bash
python experiments/animate_agent_episode.py \
  --map official_like \
  --agent lookahead_greedy \
  --seed 42 \
  --max-steps 30 \
  --frame-mode events
```

Report this as a qualitative case study or replay illustration only.

## Primary Metrics

### Outcome

- evaluation score at stopping point;
- terminal flag and terminal rate;
- score type: terminal final score or truncated score;
- raw player score;
- Major Line bonus;
- Rail Baron bonus.

### Behaviour

- delivered goods count;
- completed routes and completed segments;
- build, delivery, upgrade, urbanise, pass, and next-turn action counts;
- urbanised city count;
- locomotive level;
- empty-city-marker count.

### Cost and Reliability

- financing certificates (`bonds` field);
- certificates issued during the episode;
- estimated construction cost;
- runtime per episode;
- success rate;
- fallback actions;
- failed actions.

### Secondary Efficiency Metrics

- evaluation score per step;
- deliveries per financing certificate;
- completed routes per financing certificate.

Efficiency ratios should remain secondary because a denominator of zero or very small financing values can make ratios unstable.

## Statistical Analysis

Because all agents use the same seeds within a protocol, comparisons should be paired by seed.

For each map and horizon:

1. Report mean, median, standard deviation, minimum, and maximum evaluation score.
2. Report terminal rate and the number of terminal versus truncated episodes.
3. Report mean and median runtime.
4. Show score distributions rather than only a single average.
5. For the main comparisons, calculate paired score differences against `objective_aware_greedy`.
6. Report a 95% bootstrap confidence interval for the paired mean or median difference.
7. Optionally use a Wilcoxon signed-rank test when the paired differences are non-normal, with Holm correction if several agents are tested against the same baseline.
8. Report the magnitude and direction of differences even when a significance test is inconclusive.

Do not run significance tests on the five-episode expanded lookahead pilot as if it were a fully powered experiment.

## Figures and Tables

Recommended dissertation outputs:

1. Main table for `official_like`, 60 steps, 20 seeds.
2. Box or violin plot of evaluation score by agent.
3. Runtime plot on a logarithmic scale if lookahead dominates the range.
4. Behaviour profile showing deliveries, completed routes, urbanisation, and financing.
5. Horizon-sensitivity plot for 30, 60, and 90 steps.
6. Expanded-map runtime and outcome table, clearly separating C1 and C2.
7. One replay figure or action trace for seed 42 as a qualitative example.

## Validity Checks Before Running the Final Benchmark

Run:

```bash
python experiments/smoke_test_rules.py
python experiments/smoke_test_agents.py
python experiments/smoke_test_agent_benchmark.py
python experiments/smoke_test_agent_animation_app.py
python experiments/smoke_test_lookahead_greedy_agent.py
python experiments/smoke_test_meeting_demo.py
```

Also record:

- commit SHA;
- Python version;
- package versions;
- operating system and CPU;
- whether runs were executed serially or in parallel;
- exact commands and output directories.

## Decision Rules for Dissertation Claims

- Claim that an agent performs better only when the multi-seed result supports it.
- Qualify conclusions by map and horizon.
- Separate outcome quality from runtime cost.
- Do not describe `lookahead_greedy` as optimal.
- Do not describe a non-terminal score as a completed-game final score.
- Do not generalise results to the full multiplayer board game.
- Treat expanded-map lookahead conclusions as exploratory unless the full planned seed count is completed.
