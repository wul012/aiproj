# MiniGPT Exact-Surface Repair Contract Patch

- Status: `pass`
- Decision: `pair_readiness_exact_surface_repair_contract_patch_ready`
- Added rows: `4`

## Added Rows

- `exact_surface_bridge pipe equals tokens map fixed and loss => fixed loss`
- `exact_surface_bridge fixed equals pipe loss equals expects fixed loss`
- `exact_surface_bridge compact pipe structure keeps fixed before loss`
- `exact_surface_bridge no space pipe joins fixed token and loss token`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| repair_plan_passed | pass | pass | exact-surface repair plan must pass |
| repair_plan_decision | pass | pair_readiness_exact_surface_repair_plan_ready | patch follows only a ready exact-surface repair plan |
| next_artifact_matches | pass | pair_readiness_exact_surface_repair_contract_patch | plan must request this patch artifact |
| base_contract_passed | pass | pass | base fixed-preserving contract must pass |
| base_contract_decision | pass | pair_readiness_fixed_preserving_transfer_contract_patch_ready | base must be the fixed-preserving transfer contract patch |
| exact_surface_rows_added | pass | all exact-surface rows | all exact-surface repair rows must be present |
| repair_row_budget_respected | pass | 4 | patch must respect plan row budget |
| fixed_preserving_rows_preserved | pass | all fixed-preserving rows | patch must preserve fixed-preserving transfer rows |
| exact_direct_rows_preserved | pass | ['fixed=fixed', 'loss=loss'] | direct completion rows must be preserved |
| heldout_pair_absent | pass | False | heldout pair prompt must stay out of all training rows |
| heldout_pair_absent_from_patch | pass | False | patch rows must not train on exact heldout pair prompt |
| no_exact_eval_row_overlap | pass | [] | exact eval prompts must not be training rows |
