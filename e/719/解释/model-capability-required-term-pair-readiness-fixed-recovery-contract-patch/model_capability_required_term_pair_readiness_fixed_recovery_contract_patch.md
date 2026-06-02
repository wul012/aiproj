# MiniGPT Pair-Readiness Fixed-Recovery Contract Patch

- Status: `pass`
- Decision: `pair_readiness_fixed_recovery_contract_patch_ready`

## Added Rows

- `task: complete required term | prompt: fixed= | answer: fixed | recovery: fixed`
- `case=fixed-recovery | prompt=fixed= | expected=fixed | answer=fixed`
- `fixed direct answer confirmation -> fixed`
- `fixed prompt should complete fixed before loss`
- `fixed branch keeps fixed and rejects loss completion`
- `fixed recovery row preserves fixed token sequence`
- `when prompt begins fixed= the answer remains fixed`
- `required term fixed stays fixed while loss rows stay present`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| repair_plan_passed | pass | pass | repair plan must pass |
| repair_plan_decision | pass | pair_readiness_fixed_recovery_repair_plan_ready | patch follows only a ready fixed-recovery repair plan |
| base_contract_passed | pass | pass | base structured-template contract must pass |
| base_contract_decision | pass | pair_readiness_structured_template_contract_ready | base must be the structured-template contract |
| fixed_rows_added | pass | all fixed rows | all fixed-recovery rows must be present |
| loss_rows_preserved | pass | 11 | loss structured rows must remain present |
| evaluation_probes_preserved | pass | 3 | fixed, loss, and pair probes must be preserved |
| no_exact_eval_row_overlap | pass | [] | exact eval prompts must not be training rows |
| heldout_pair_absent | pass | False | heldout pair probe must not be a training row |
