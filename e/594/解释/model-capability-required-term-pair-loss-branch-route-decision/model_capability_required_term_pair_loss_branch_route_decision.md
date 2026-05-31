# MiniGPT Required-Term Pair Loss-Branch Route Decision

- Status: `pass`
- Decision: `select_targeted_loss_branch_for_seed_stability_not_promotion`
- Selected stability route: `v590-targeted`
- Fixed-retention required: `True`
- Model quality claim: `route_decision_only`

## Routes

| Route | Type | Hit terms | Missed terms | Candidate | Rejection reasons |
| --- | --- | --- | --- | --- | --- |
| v590-targeted | targeted | loss | fixed | True | no_pair_full,fixed_missing,loss_only_tradeoff |
| v591-dual-anchor | dual_anchor | loss | fixed | False | no_pair_full,fixed_missing,loss_only_tradeoff |
| v592-micro-span | micro_span | loss | fixed | False | no_pair_full,fixed_missing,loss_only_tradeoff |

## Boundary

- Reason: All available loss-branch routes recover loss but miss fixed; the simplest route is selected only as a stability baseline.
- Next action: run targeted loss-branch seed stability, then design a fixed-retention objective
