# MiniGPT Required-Term Pair Fixed-Retention Route Decision

- Status: `pass`
- Decision: `select_fixed_recovery_route_for_loss_rebalance_not_promotion`
- Selected route: `v601-first-token`
- Selected corpus mode: `equals_surface_no_pair_id_fixed_retention_first_token_repair`
- Loss rebalance required: `True`

## Routes

| Route | Type | Hit terms | Missed terms | Pair-full |
| --- | --- | --- | --- | --- |
| v600-balanced | balanced | loss | fixed | False |
| v601-first-token | first-token | fixed | loss | False |
| v602-prompt-guard | prompt-guard | loss | fixed | False |

## Boundary

- Model quality claim: `route_decision_only`
- Reason: The first-token route recovers fixed but loses loss, so it is not a promotion route.
- Next action: build a loss-rebalance objective using the fixed-recovery route as evidence
