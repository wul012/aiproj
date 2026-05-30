# MiniGPT Model Capability Required-Term Pair Decoding Sweep

- Status: `pass`
- Decision: `required_term_pair_decoding_sweep_partial`
- Sweep decision: `pair_decoding_sweep_partial_only`
- Source capacity decision: `pair_capacity_sweep_partial_only`
- Targets: `2`
- Profiles: `4`
- Probe hits: `8`
- Full-hit profile targets: `0`
- Decoding full-hit observed: `False`

## Profile Results

| Target | Profile | Hits | Missed | Hit rate | Full hit |
| --- | --- | --- | --- | ---: | --- |
| 01-fixed-loss-baseline-repeat | deterministic-12 | loss | fixed | 0.5 | False |
| 01-fixed-loss-baseline-repeat | deterministic-24 | loss | fixed | 0.5 | False |
| 01-fixed-loss-baseline-repeat | sample-top5-24 | loss | fixed | 0.5 | False |
| 01-fixed-loss-baseline-repeat | sample-open-24 | loss | fixed | 0.5 | False |
| 01-fixed-loss-longer-iters | deterministic-12 | loss | fixed | 0.5 | False |
| 01-fixed-loss-longer-iters | deterministic-24 | loss | fixed | 0.5 | False |
| 01-fixed-loss-longer-iters | sample-top5-24 | fixed | loss | 0.5 | False |
| 01-fixed-loss-longer-iters | sample-open-24 | fixed | loss | 0.5 | False |

## Target Summary

| Target | Variant | Full-hit profiles | Partial profiles | Best profile | Best hits |
| --- | --- | --- | --- | --- | ---: |
| 01-fixed-loss-baseline-repeat | baseline-repeat |  | deterministic-12, deterministic-24, sample-top5-24, sample-open-24 | sample-top5-24 | 1 |
| 01-fixed-loss-longer-iters | longer-iters |  | deterministic-12, deterministic-24, sample-top5-24, sample-open-24 | sample-top5-24 | 1 |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Decoding changes still produced only partial pair hits from the existing v497 checkpoints.
- Next action: inspect prompt target separation and corpus row design before training larger pair checkpoints
