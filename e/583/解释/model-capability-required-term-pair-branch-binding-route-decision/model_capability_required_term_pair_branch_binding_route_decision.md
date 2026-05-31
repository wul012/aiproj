# MiniGPT Required-Term Pair Branch-Binding Route Decision

- Status: `pass`
- Decision: `stop_branch_binding_v1_and_keep_residual_baseline`
- Branch-binding routes: `2`
- Branch-binding visible hits: `0`
- Best residual signal: `v571-loss-balanced`

## Route Rows

| Route | Type | Pair-full | Hit terms | Reasons |
| --- | --- | ---: | --- | --- |
| v571-loss-balanced | baseline | 0/1 | fixed | no_pair_full_seed,loss_term_missing |
| v579-branch-binding | branch_binding | 0/1 |  | no_pair_full_seed,no_visible_term_hit,loss_term_missing,branch_binding_not_promotable |
| v581-branch-binding-no-space | branch_binding | 0/1 |  | no_pair_full_seed,no_visible_term_hit,loss_term_missing,branch_binding_not_promotable |

## Boundary

- Model quality claim: `route_decision_only`
- Reason: Compared branch-binding routes did not reach pair-full and did not preserve the baseline partial hit.
- Next action: stop branch-binding v1/v2; require a stronger objective before another training run
