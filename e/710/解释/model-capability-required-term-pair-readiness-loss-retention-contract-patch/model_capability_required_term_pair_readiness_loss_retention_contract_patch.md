# MiniGPT Pair-Readiness Loss-Retention Contract Patch

- Status: `pass`
- Decision: `pair_readiness_loss_retention_contract_patch_ready`

## Added Rows

- `loss=l`
- `loss=lo`
- `loss=los`
- `loss=loss`
- `loss branch keeps l before fixed`
- `loss branch resists fixed completion`
- `loss prompt should not become fixed`
- `loss direct retention beats fixed pollution`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| repair_plan_passed | pass | pass | repair plan must pass |
| repair_plan_decision | pass | pair_readiness_loss_retention_repair_plan_ready | patch follows only a ready loss-retention repair plan |
| base_contract_passed | pass | pass | base contract must pass |
| base_contract_decision | pass | pair_readiness_split_contract_ready | base must be the original split contract |
| loss_rows_added | pass | all loss rows | all loss-retention rows must be present |
| heldout_pair_absent | pass | False | heldout pair probe must not be a training row |
| evaluation_probes_preserved | pass | 3 | fixed, loss, and pair probes must be preserved |
