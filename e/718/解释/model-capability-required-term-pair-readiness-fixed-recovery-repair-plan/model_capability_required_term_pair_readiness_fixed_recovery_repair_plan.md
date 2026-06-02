# MiniGPT Pair-Readiness Fixed-Recovery Repair Plan

- Status: `pass`
- Decision: `pair_readiness_fixed_recovery_repair_plan_ready`
- Proposed next artifact: `pair_readiness_fixed_recovery_contract_patch`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| route_comparison_passed | pass | pass | source route comparison must pass |
| route_comparison_decision | pass | pair_readiness_structured_template_changes_failure_shape_without_pair_full | fixed recovery follows only a structured-template failure-shape change |
| failure_shape_changed | pass | True | structured route must change failure shape |
| structured_hits_loss | pass | ['loss'] | structured route should retain loss before fixed recovery |
| structured_misses_fixed | pass | ['fixed'] | structured route should miss fixed before fixed recovery |
| no_pair_full_route | pass | False | no route should already be pair-full |
| structured_not_above_baseline | pass | 0 | structured route should be a shape change, not an improvement |
| structured_and_baseline_best | pass | ['baseline-split', 'structured-template'] | baseline and structured routes should be tied best evidence |

## Contract Patch

- `add fixed answer confirmation rows after structured prompt-answer rows`
- `add fixed anti-loss contamination rows`
- `preserve loss structured rows from v714 because loss recovered in v716`
- `keep heldout pair probe excluded from training rows`
- `compare fixed-recovery run against v707 baseline and v716 structured-template before any promotion`
