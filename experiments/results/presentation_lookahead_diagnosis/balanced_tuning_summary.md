# Balanced Presentation Lookahead Tuning Summary

Scenario: `official_like`, seeds `0`-`9`, max steps `60`.

| agent | mean final_score | median final_score | mean deliveries | mean completed routes | mean bonds | mean urbanize actions | mean first20 urbanize | success count | fallback count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| urbanization_aware_lookahead_greedy | 22.80 | 23.50 | 20.80 | 14.90 | 97.70 | 2.00 | 1.90 | 10 | 0 |
| presentation_lookahead_greedy | 51.50 | 49.50 | 20.40 | 15.00 | 63.60 | 2.00 | 1.00 | 10 | 0 |
| objective_aware_greedy | -41.00 | -41.00 | 12.00 | 15.00 | 111.00 | 0.00 | 0.00 | 0 | 0 |

## Tuning Read

- The balanced variant should keep early urbanization readable while allowing useful urbanize actions when they connect to deliveries, objectives, or the built network.
- Presentation mean first-20 urbanize actions: 1.00.
- Presentation mean urbanize actions: 2.00.
- Presentation mean bonds: 63.60.
- Presentation mean deliveries: 20.40.
- Presentation mean final score: 51.50.
