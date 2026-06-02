# MiniGPT Exact-Surface Repair Plan

- Status: `pass`
- Decision: `pair_readiness_exact_surface_repair_plan_ready`
- Proposed next artifact: `pair_readiness_exact_surface_repair_contract_patch`
- Repair row budget: `4`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| diagnostic_passed | pass | pass | sensitivity diagnostic must pass |
| diagnostic_decision | pass | pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found | plan follows only the prompt-surface sensitivity route |
| promotion_blocked | pass | True | promotion must be blocked before repair |
| exact_surface_missed | pass | ['exact-heldout-pair'] | exact heldout pair surface must be the missed required surface |
| optional_surface_signal_present | pass | ['arrow-heldout-pair'] | at least one optional surface should show pair-full signal before minimal repair |

## Patch Strategy

- preserve exact direct rows fixed=fixed and loss=loss
- preserve the four fixed-preserving transfer rows from v747
- add at most four near-exact surface bridge rows that mention pipe/equals structure without using fixed=\|loss=
- avoid adding the exact heldout prompt as a training row
- rerun materialization, training, and independent pair-probe replay before any promotion
