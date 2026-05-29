# MiniGPT Model Capability Required-Term Pair Rebalance Seed Stability

- Status: `pass`
- Decision: `required_term_pair_rebalance_seed_stability_not_reproduced`
- Seed-stability decision: `rebalance_full_pairs_not_reproduced_across_seeds`
- Source rebalance decision: `pair_rebalance_full_hit_gain`
- Selected pairs: `1`
- Seeds: `3`
- Pair-seed runs: `3`
- Training pass count: `3`
- Pair-seed full hits: `0`
- Stable pairs: `0`

| Pair | v495 hits | Full-hit seeds | Missed seeds | Full-hit rate | Stable |
| --- | --- | --- | --- | ---: | --- |
| fixed, loss | fixed, loss |  | 496, 1496, 2496 | 0.0 | False |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The v495 full-hit pair did not reproduce full-hit behavior under the configured seed repeat.
- Next action: treat v495 full-hit as fragile and inspect corpus/model capacity before expanding target groups
