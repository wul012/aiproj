# MiniGPT Model Capability Required-Term Pair Capacity Sweep

- Status: `pass`
- Decision: `required_term_pair_capacity_sweep_partial`
- Sweep decision: `pair_capacity_sweep_partial_only`
- Source seed-stability decision: `rebalance_full_pairs_not_reproduced_across_seeds`
- Selected pairs: `1`
- Capacity variants: `4`
- Variant runs: `4`
- Training pass count: `4`
- Full-hit variant pairs: `0`
- Capacity full-hit observed: `False`

## Variant Results

| Pair | Variant | Hits | Missed | Hit rate | Full hit |
| --- | --- | --- | --- | ---: | --- |
| 01-fixed-loss | baseline-repeat | loss | fixed | 0.5 | False |
| 01-fixed-loss | longer-iters | loss | fixed | 0.5 | False |
| 01-fixed-loss | wider-embd |  | fixed, loss | 0.0 | False |
| 01-fixed-loss | denser-corpus |  | fixed, loss | 0.0 | False |

## Pair Summary

| Pair | Full-hit variants | Partial variants | Best variant | Best hit count |
| --- | --- | --- | --- | ---: |
| 01-fixed-loss |  | baseline-repeat, longer-iters | longer-iters | 1 |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The sweep still produced only partial pair hits; capacity changes did not recover the v495 full-hit.
- Next action: inspect corpus prompts and generation decoding before adding more terms to the checkpoint
