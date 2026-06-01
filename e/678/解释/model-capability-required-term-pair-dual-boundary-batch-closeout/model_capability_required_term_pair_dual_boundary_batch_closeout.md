# MiniGPT Required-Term Pair Dual-Boundary Batch Closeout

- Status: `pass`
- Decision: `required_term_pair_dual_boundary_internal_stable_generation_surface_unstable`
- Generation pair-full seeds: `2/3`
- Internal pair-full seeds: `3/3`
- Promotion ready: `False`
- Model quality claim: `targeted_internal_preference_stable_signal_only`

## Seeds

| Seed | Generation pair-full | Internal pair-full | Aligned | Classification |
| ---: | --- | --- | --- | --- |
| 1535 | True | True | True | generation_internal_pair_full |
| 2535 | False | True | False | internal_only_generation_surface_miss |
| 3535 | True | True | True | generation_internal_pair_full |

## Boundary

- Reason: Internal forced-choice is stable across seeds, but generation pair-full is not stable.
- Next action: focus next experiments on generation surface stability or decoding policy, not internal preference repair
