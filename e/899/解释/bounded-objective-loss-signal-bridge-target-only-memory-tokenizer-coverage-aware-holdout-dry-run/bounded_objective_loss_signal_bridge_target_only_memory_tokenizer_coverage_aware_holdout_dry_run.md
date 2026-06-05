# MiniGPT bounded objective loss signal bridge target-only memory tokenizer-coverage-aware holdout dry-run

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_passed`
- Positive passed: `5/5`
- Negative passed: `0`
- Negative control passed: `False`
- Next step: `run_tokenizer_coverage_aware_holdout_real_replay`

## Dry-Run Rows

| Case | Positive pass | Negative pass | Positive hit | Negative hit |
| --- | --- | --- | --- | --- |
| tokenizer-covered-answer_exact_terms | True | False | fixed,loss | fixed |
| tokenizer-covered-return_target_words | True | False | fixed,loss | fixed |
| tokenizer-covered-contrast_route_result | True | False | fixed,loss | fixed |
| tokenizer-covered-jsonish_answer_terms | True | False | fixed,loss | fixed |
| tokenizer-covered-self_check_terms | True | False | fixed,loss | fixed |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | tokenizer-coverage-aware holdout suite must pass |
| holdout_suite_ready | pass | True | holdout suite summary must be ready |
| suite_ready | pass | True | benchmark suite must be ready |
| cases_present | pass | 5 | holdout suite must include cases |
| expected_terms_complete | pass | ['fixed', 'loss'] | dry-run expects fixed/loss scoring contract |
| positive_rows_pass | pass | 5 | positive continuation must pass every case |
| negative_rows_fail | pass | 0 | negative continuation must not pass any case |
