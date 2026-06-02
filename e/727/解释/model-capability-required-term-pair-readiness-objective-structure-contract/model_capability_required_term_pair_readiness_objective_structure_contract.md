# MiniGPT Pair-Readiness Objective-Structure Contract

- Status: `pass`
- Decision: `pair_readiness_objective_structure_contract_ready`
- Heldout pair probe: `fixed=|loss=`

## Row Families

| Family | Role | Target | Rows |
| --- | --- | --- | --- |
| task_id_direct_fixed | direct_term_completion | fixed | 4 |
| task_id_direct_loss | direct_term_completion | loss | 4 |
| paired_block_forward | paired_branch_completion | fixed+loss | 3 |
| paired_block_reverse | paired_branch_completion | loss+fixed | 3 |
| boundary_contrast | anti_contamination | fixed/loss | 4 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| plan_passed | pass | pass | objective-structure plan must pass |
| plan_decision | pass | pair_readiness_objective_structure_plan_ready | contract follows only a ready objective-structure plan |
| next_artifact_matches | pass | pair_readiness_objective_structure_contract | plan must request this contract artifact |
| training_rows_present | pass | 18 | objective-structure rows must be substantial enough to materialize |
| direct_family_balance | pass | fixed=4, loss=4 | fixed/loss direct row families must be balanced |
| paired_forward_present | pass | 3 | forward paired block rows must be present |
| paired_reverse_present | pass | 3 | reverse paired block rows must be present |
| evaluation_probes_present | pass | 3 | fixed, loss, and pair probes must be preserved |
| no_exact_eval_row_overlap | pass | [] | exact eval prompts must not be training rows |
| heldout_pair_absent | pass | False | heldout pair probe must stay out of training rows |
