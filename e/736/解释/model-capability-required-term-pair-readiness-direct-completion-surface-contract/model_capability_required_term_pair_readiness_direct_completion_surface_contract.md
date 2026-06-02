# MiniGPT Pair-Readiness Direct-Completion Surface Contract

- Status: `pass`
- Decision: `pair_readiness_direct_completion_surface_contract_ready`
- Heldout pair probe: `fixed=|loss=`

## Row Families

| Family | Role | Target | Rows |
| --- | --- | --- | --- |
| exact_direct_completion | direct_completion_surface | fixed/loss | 2 |
| fixed_prefix_ladder | direct_completion_prefix | fixed | 3 |
| loss_prefix_ladder | direct_completion_prefix | loss | 3 |
| paired_order_forward | paired_order_surface | fixed+loss | 2 |
| paired_order_reverse | paired_order_surface | loss+fixed | 2 |
| direct_boundary_contrast | anti_contamination | fixed/loss | 4 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| closeout_plan_passed | pass | pass | bridge closeout plan must pass |
| closeout_plan_decision | pass | pair_readiness_bridge_closeout_plan_ready | contract follows only a ready bridge closeout plan |
| next_artifact_matches | pass | pair_readiness_direct_completion_surface_contract | closeout plan must request this contract artifact |
| training_rows_present | pass | 16 | direct-completion surface rows must be materializable |
| exact_fixed_completion_present | pass | ['fixed=fixed', 'loss=loss'] | exact fixed completion row must be present |
| exact_loss_completion_present | pass | ['fixed=fixed', 'loss=loss'] | exact loss completion row must be present |
| prefix_ladder_balance | pass | fixed=3, loss=3 | fixed and loss prefix ladders must contain the same number of rows |
| paired_forward_present | pass | 2 | forward paired order rows must be present |
| paired_reverse_present | pass | 2 | reverse paired order rows must be present |
| evaluation_probes_present | pass | 3 | fixed, loss, and pair probes must be preserved |
| no_exact_eval_row_overlap | pass | [] | exact eval prompts must not be training rows |
| heldout_pair_absent | pass | False | heldout pair probe must stay out of training rows |
