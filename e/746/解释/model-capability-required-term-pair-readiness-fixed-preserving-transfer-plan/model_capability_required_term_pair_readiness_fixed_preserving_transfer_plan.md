# MiniGPT Fixed-Preserving Transfer Plan

- Status: `pass`
- Decision: `pair_readiness_fixed_preserving_transfer_plan_ready`
- Proposed next artifact: `pair_readiness_fixed_preserving_transfer_contract_patch`
- Transfer row budget: `4`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| diagnostic_passed | pass | pass | regression diagnostic must pass |
| diagnostic_decision | pass | pair_readiness_pair_prompt_transfer_regressed_stop_route | plan follows only the regressed transfer route closeout |
| transfer_route_closed | pass | True | full surrogate transfer route must already be closed |
| fixed_regressed | pass | True | plan is specific to fixed-side regression |
| direct_hit_regressed | pass | -1 | transfer hits must be lower than direct-completion hits |
| pair_probe_still_not_ready | pass | False | direct-completion pair probe must still be not ready |

## Patch Strategy

- preserve exact direct-completion rows before adding transfer rows
- replace the broad eight-row surrogate transfer patch with at most four fixed-preserving bridge rows
- include explicit fixed-before-loss guard text so fixed= does not drift to loss
- do not add the exact heldout pair prompt or direct echo of fixed=\|loss=
