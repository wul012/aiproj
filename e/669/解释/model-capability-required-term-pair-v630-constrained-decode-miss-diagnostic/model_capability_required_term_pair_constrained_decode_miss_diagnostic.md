# MiniGPT Required-Term Pair Constrained Decode Miss Diagnostic

- Status: `pass`
- Decision: `fixed_branch_still_missed_after_constrained_decode`
- Fixed constrained hit: `False`
- Loss constrained hit: `True`
- Fixed miss class: `prefix_fragment_without_full_term`
- Recommended next route: `explicit_dual_objective_boundary_for_fixed_retention`

## Diagnostic Rows

| Term | Profile | Hit | Miss class | Prefix present | Preview |
| --- | --- | --- | --- | --- | --- |
| fixed | default | False | equals_surface_drift_without_term | False |  d= los\nd=fi |
| fixed | block_competing_initial | False | prefix_fragment_without_full_term | True |  d= cans\nfix |
| loss | default | False | equals_surface_drift_without_term | False |  fixe fixed= |
| loss | block_competing_initial | True | not_missed | True |  lossssssss= |

## Boundary

- Model quality claim: `decode_diagnostic_only`
- Reason: Blocking the competing initial recovers loss, but fixed remains a miss.
- Next action: design an explicit dual-objective boundary that preserves fixed while retaining loss
