# MiniGPT Pair-Readiness Direct-Prompt Bridge Contract Patch

- Status: `pass`
- Decision: `pair_readiness_direct_prompt_bridge_contract_patch_ready`
- Added rows: `8`

## Added Rows

- `bridge=direct_prompt | prompt=fixed= | answer=fixed`
- `bridge fixed raw surface fixed= produces fixed`
- `direct prompt fixed= should continue with fixed`
- `fixed= -> fixed token`
- `bridge=direct_prompt | prompt=loss= | answer=loss`
- `bridge loss raw surface loss= produces loss`
- `direct prompt loss= should continue with loss`
- `loss= -> loss token`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| diagnostic_passed | pass | pass | surface mismatch diagnostic must pass |
| diagnostic_decision | pass | pair_readiness_direct_surface_mismatch_detected | bridge patch follows only a detected direct surface mismatch |
| diagnostic_recommends_bridge | pass | pair_readiness_direct_prompt_bridge_contract_patch | diagnostic must request this patch |
| base_contract_passed | pass | pass | base objective-structure contract must pass |
| base_contract_decision | pass | pair_readiness_objective_structure_contract_ready | base must be the objective-structure contract |
| bridge_rows_added | pass | all bridge rows | all direct prompt bridge rows must be present |
| fixed_bridge_balance | pass | 4 | fixed bridge rows must be balanced |
| loss_bridge_balance | pass | 4 | loss bridge rows must be balanced |
| no_exact_eval_row_overlap | pass | [] | exact eval prompts must not be training rows |
| heldout_pair_absent | pass | False | heldout pair probe must stay out of training rows |
