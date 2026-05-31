# MiniGPT Required-Term Pair Target-Anchor Route Decision

- Status: `pass`
- Decision: `keep_target_anchor_as_residual_not_promoted`
- Target-anchor routes: `1`
- Target-anchor visible hits: `1`
- Residual routes: `v571-loss-balanced,v584-target-anchor`

## Route Rows

| Route | Type | Pair-full | Hit terms | Reasons |
| --- | --- | ---: | --- | --- |
| v571-loss-balanced | baseline | 0/1 | fixed | no_pair_full_seed,loss_term_missing |
| v579-branch-binding | branch_binding | 0/1 |  | no_pair_full_seed,loss_term_missing,no_visible_term_hit |
| v581-branch-binding-no-space | branch_binding | 0/1 |  | no_pair_full_seed,loss_term_missing,no_visible_term_hit |
| v584-target-anchor | target_anchor | 0/1 | fixed | no_pair_full_seed,loss_term_missing,target_anchor_residual_fixed_only |

## Boundary

- Model quality claim: `route_decision_only`
- Reason: Target-anchor recovered only a fixed partial hit and did not recover loss.
- Next action: keep target-anchor as residual evidence; design a loss-branch objective before more training
