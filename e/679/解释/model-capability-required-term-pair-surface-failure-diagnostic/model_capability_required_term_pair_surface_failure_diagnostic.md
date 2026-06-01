# MiniGPT Required-Term Pair Surface Failure Diagnostic

- Status: `pass`
- Decision: `required_term_pair_single_term_surface_failure_isolated`
- Surface failure seeds: `[2535]`
- Surface failure terms: `['loss']`
- Model quality claim: `targeted_surface_failure_diagnostic`

## Seed Rows

| Seed | Generation full | Internal full | Missed terms | Failure term | Classification | Preview |
| ---: | --- | --- | --- | --- | --- | --- |
| 1535 | True | True |  |  | aligned_pair_full |  |
| 2535 | False | True | loss | loss | internal_stable_surface_failure |  candidate l |
| 3535 | True | True |  |  | aligned_pair_full |  |

## Boundary

- Reason: Internal preference is stable, but generation misses `loss` on at least one seed.
- Next action: design a generation-surface policy replay before retraining
