# MiniGPT Required-Term Pair Fixed-Retention Objective Comparison

- Status: `pass`
- Decision: `fixed_retention_objectives_confirm_branch_tradeoff`
- Compared reports: `3`
- Pair-full reports: `0`
- Fixed-only tradeoffs: `1`
- Loss-only tradeoffs: `2`
- Fixed recovery route: `v601-first-token`

## Branch Rows

| Route | Mode | Hit terms | Missed terms | Pair-full profiles |
| --- | --- | --- | --- | --- |
| v600-balanced | equals_surface_no_pair_id_fixed_retention_balanced_repair | loss | fixed |  |
| v601-first-token | equals_surface_no_pair_id_fixed_retention_first_token_repair | fixed | loss |  |
| v602-prompt-guard | equals_surface_no_pair_id_fixed_retention_prompt_guard_repair | loss | fixed |  |

## Boundary

- Model quality claim: `tradeoff_only`
- Reason: The routes recover different branches but no route keeps both at once.
- Next action: select the fixed recovery route for a loss-rebalance objective or stability replay
