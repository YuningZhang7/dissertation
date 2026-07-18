# Presentation Lookahead Diagnosis

Scenario: `official_like`, seed `42`, max steps `60`.

| agent | first 20 urbanize | total urbanize | bonds | deliveries | completed routes | urbanized cities | final score | terminal | runtime seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| urbanization_aware_lookahead_greedy | 2 | 2 | 100 | 21 | 15 | 10 | 20 | True | 18.9075 |
| presentation_lookahead_greedy | 0 | 1 | 66 | 19 | 15 | 9 | 55 | True | 23.7891 |
| objective_aware_greedy | 0 | 0 | 111 | 12 | 15 | 8 | -41 | False | 1.3260 |

## Interpretation

- `presentation_lookahead_greedy` is intended for replay clarity, not maximum benchmark score.
- It gates early/speculative urbanization and gives more weight to completed routes, deliveries, and bond control.
- Lower first-20-step urbanization than the experimental lookahead agent indicates a more readable early replay.
- Remaining urbanization is expected to occur near the built network or when it opens direct delivery potential.

## Before/After Summary

- Original lookahead first-20 urbanize actions: 2
- Presentation lookahead first-20 urbanize actions: 0
- Original lookahead total urbanize actions: 2
- Presentation lookahead total urbanize actions: 1
- Original lookahead bonds: 100
- Presentation lookahead bonds: 66
- Original lookahead deliveries: 21
- Presentation lookahead deliveries: 19
- Original lookahead completed routes: 15
- Presentation lookahead completed routes: 15
