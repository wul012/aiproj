# MiniGPT bounded objective loss signal bridge target-only memory target-hidden tokenizer-covered holdout dry-run

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run_passed`
- Positive passed: `5/5`
- Negative passed: `0`
- Negative control passed: `False`
- Next step: `run_target_hidden_tokenizer_covered_holdout_real_replay`

## Dry-Run Rows

| Case | Positive pass | Negative pass | Positive hit | Negative hit | Negative missed |
| --- | --- | --- | --- | --- | --- |
| target-hidden-answer_learned_pair | True | False | fixed,loss | fixed | loss |
| target-hidden-return_target_pair | True | False | fixed,loss | fixed | loss |
| target-hidden-contrast_route_pair | True | False | fixed,loss | fixed | loss |
| target-hidden-jsonish_answer_terms | True | False | fixed,loss | fixed | loss |
| target-hidden-self_check_pair | True | False | fixed,loss | fixed | loss |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | target-hidden holdout suite must pass |
| holdout_suite_ready | pass | True | target-hidden suite summary must be ready |
| suite_ready | pass | True | benchmark suite must be ready |
| cases_present | pass | 5 | target-hidden holdout suite must include cases |
| target_hidden_cases_present | pass | 5 | every source case must be target-hidden |
| expected_terms_complete | pass | ['fixed', 'loss'] | dry-run expects fixed/loss scoring contract |
| positive_rows_pass | pass | 5 | positive continuation must pass every case |
| negative_rows_fail | pass | 0 | negative continuation must not pass any case |
