# Dissertation Results and Discussion Outline

This file is a writing aid for the current route-segment dissertation. It replaces earlier outlines centred on edge-only maps, MCTS, and CardAware agents.

The dissertation must remain explicit that the project is a simplified single-player railway optimisation abstraction, not a full official implementation of *Railways of the World*.

## RQ1: Does the simulator provide a useful and reproducible railway decision abstraction?

### Evidence to present

- A route-segment state model with cities, ordered segments, completed routes, goods, demand colours, financing, locomotive levels, urbanisation, Major Lines, and Rail Baron objectives.
- A single legal-action and transition interface used by all five agents, replay generation, and benchmark tooling.
- Automatic financing rather than a voluntary bond action.
- No fixed home city, train position, or moving train token.
- Smoke tests for construction, delivery paths, financing, urbanisation, objectives, replay compatibility, and benchmark output.
- Artificial maps and explicit rule-scope documentation.

### Suggested interpretation

The simulator is sufficiently expressive for controlled comparisons of interpretable sequential policies. Its validity is internal to the implemented abstraction: it preserves network-building and delivery trade-offs while deliberately excluding multiplayer interaction and official tile-level detail.

### Claims to avoid

- “Complete implementation of Railways of the World.”
- “Official map simulation.”
- “Validated model of expert human play.”

## RQ2: How do simple baseline policies behave?

### Agents

- `random`
- `greedy_delivery`
- `greedy_expansion`

### Evidence to collect

- evaluation score at the stopping point;
- deliveries;
- completed routes;
- financing certificates;
- build, delivery, upgrade, urbanise, and pass actions;
- runtime;
- terminal rate.

### Discussion angle

The simple baselines isolate distinct decision biases:

- random provides a legal-action reference;
- delivery greed exploits immediate opportunities but may fail to create future routes;
- expansion greed creates network capacity but may overbuild, under-deliver, or accumulate financing penalties.

The value of these agents is diagnostic rather than competitive: their behaviour makes the environment's trade-offs visible.

## RQ3: What is gained by objective-aware one-step decision-making?

### Agent

- `objective_aware_greedy`

### Evidence to collect

Compare it with the three simple baselines using the same seeds and horizon. Examine:

- paired score differences;
- Major Line and Rail Baron bonuses;
- completed routes and delivery opportunities;
- financing;
- locomotive upgrades;
- runtime.

### Discussion angle

`objective_aware_greedy` combines immediate delivery with hand-designed scores for route completion, future delivery potential, objective progress, construction cost, and financing. It is the strongest one-step baseline, but it remains myopic because it evaluates only the immediate successor state and gives currently legal deliveries hard priority.

### Claims to avoid

- Do not call it globally optimal.
- Do not claim it evaluates every action type uniformly; urbanisation is not part of its primary scored action set.

## RQ4: Does bounded lookahead improve decisions, and at what computational cost?

### Agent

- `lookahead_greedy`

### Evidence to collect

Compare it directly with `objective_aware_greedy` on paired seeds:

- evaluation score;
- delivery and route completion;
- urbanisation count and timing;
- financing;
- objective bonuses;
- runtime;
- fallback and failed actions.

### Method description

`lookahead_greedy`:

- generates a restricted candidate set;
- keeps top delivery and build actions, upgrades, and at most one gated urbanisation candidate;
- simulates candidate transitions;
- performs depth-two bounded rollout;
- combines immediate heuristic value with discounted future value.

### Discussion angle

The central question is not only whether lookahead scores more highly, but whether any improvement justifies the additional computation. A strong result would be a measured score–runtime trade-off, not a claim of universal superiority.

### Limitations to state

- candidate pruning can exclude the best action;
- evaluation weights are hand-designed;
- depth is limited;
- urbanisation simulation uses a deterministic surrogate seed that may not match realised random goods exactly;
- runtime grows rapidly with the action space.

## RQ5: How robust are findings across horizons, seeds, and map size?

### Evidence to collect

- `official_like` at 30, 60, and 90 steps;
- 20 paired seeds for the primary 60-step comparison;
- expanded-map comparison for faster agents;
- focused expanded-map lookahead pilot;
- score distributions and confidence intervals;
- terminal versus truncated episode counts;
- runtime distributions.

### Discussion angle

Seed 42 is a qualitative replay example only. Formal conclusions should be based on multi-seed results. Rankings that change across horizons or maps should be reported as scenario-dependent rather than treated as contradictions.

The expanded map is especially important for demonstrating the computational cost of lookahead. A smaller lookahead pilot can support a scalability observation, but not a fully powered quality ranking.

## Score Reporting

`GameState.final_score()` is a scoring formula, not proof that the game ended.

Use the following terminology consistently:

- **terminal final score** when `terminal=True`;
- **truncated score at the N-step horizon** when `terminal=False` because `max_steps=N` was reached;
- **evaluation score** when referring generically to both categories.

Do not report a mixed group as “mean final score” without qualification. Preferred wording:

> At the 60-step horizon, `agent_name` achieved a mean evaluation score of X across 20 seeds; Y% of episodes were terminal.

For a fully terminal subset:

> Among terminal episodes, the mean terminal final score was X.

## Recommended Results Structure

### 1. Experimental setup

- commit SHA and environment;
- maps and configuration;
- agents;
- seed sets;
- action horizons;
- card-disabled benchmark setting;
- score terminology;
- hardware and serial/parallel execution.

### 2. Primary compact-map comparison

- main metric table;
- score distribution;
- behaviour metrics;
- paired differences against `objective_aware_greedy`;
- runtime comparison.

### 3. Horizon sensitivity

- 30-, 60-, and 90-step comparison;
- terminal rates;
- changes in ranking or behaviour.

### 4. Expanded-map scalability

- faster-agent main comparison;
- focused lookahead pilot;
- explicit sample-size and horizon differences;
- runtime growth.

### 5. Qualitative replay case study

- seed 42, official-like, 30 steps;
- selected action trace or screenshots;
- explanation of route completion, delivery, objective planning, and controlled urbanisation;
- explicit statement that this is illustrative rather than statistical evidence.

### 6. Discussion

- objective awareness versus simple greed;
- bounded lookahead versus one-step scoring;
- quality versus runtime;
- sensitivity to scenario and horizon;
- implications for interpretable OR/AI methods.

## Threats to Validity

### Internal validity

- hand-designed heuristic weights;
- random urbanisation goods;
- finite candidate sets and horizons;
- possible non-terminal episodes;
- runtime dependence on implementation and hardware.

### Construct validity

- artificial maps;
- simplified financing and income;
- abstract route segments rather than official tiles;
- simplified Major Line and Rail Baron objectives;
- cards enabled in the visual app but disabled in the main benchmark.

### External validity

- single-player only;
- no auctions, blocking, shared goods competition, or opponent-owned track;
- no evidence about expert or multiplayer performance;
- no claim of transfer to the full commercial game.

### Conclusion validity

- limited seeds for expensive experiments;
- multiple comparisons;
- potential score–runtime trade-offs hidden by score-only rankings;
- expanded lookahead pilot too small for strong inferential claims.

## Future Work

- dedicated fixed-turn configuration for guaranteed terminal comparisons;
- more systematic heuristic-weight sensitivity analysis;
- deterministic or expectation-based urbanisation transition modelling;
- larger expanded-map lookahead experiments if computation permits;
- exact or optimisation-based comparison on a deliberately small route-segment instance;
- learned or adaptive policies only after the current benchmark and rule abstraction are stable;
- multiplayer interaction as a separate future model.
