# MiniGPT Required-Term Pair Fixed-Retention Objective Comparison

- Status: `pass`
- Decision: `select_fixed_retention_route_for_loss_rebalance`
- Compared reports: `3`
- Pair-full reports: `0`
- Fixed-only tradeoffs: `2`
- Loss-only tradeoffs: `0`
- Fixed recovery route: `v612-delimiter-span`

## Branch Rows

| Route | Mode | Hit terms | Missed terms | Pair-full profiles |
| --- | --- | --- | --- | --- |
| v611-contrast-free | equals_surface_no_pair_id_fixed_retention_contrast_free_repair |  | fixed,loss |  |
| v612-delimiter-span | equals_surface_no_pair_id_fixed_retention_delimiter_span_repair | fixed | loss |  |
| v613-context-switch | equals_surface_no_pair_id_fixed_retention_context_switch_repair | fixed | loss |  |

## Boundary

- Model quality claim: `comparison_only`
- Reason: The compared routes do not yet provide pair-full evidence.
- Next action: inspect first-token preferences before another objective
