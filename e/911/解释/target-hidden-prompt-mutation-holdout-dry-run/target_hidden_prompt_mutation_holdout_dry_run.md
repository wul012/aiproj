# MiniGPT target-hidden prompt-mutation holdout dry-run

- Status: `pass`
- Decision: `target_hidden_prompt_mutation_holdout_dry_run_passed`
- Cases: `10`
- Source mutation factor: `2.0`
- Source mutated cases: `10`
- Positive passed: `10/10`
- Negative passed: `0`
- Negative control passed: `False`
- Next step: `run_target_hidden_prompt_mutation_holdout_real_replay`

## Dry-Run Rows

| Case | Positive pass | Negative pass | Positive hit | Negative hit | Negative missed |
| --- | --- | --- | --- | --- | --- |
| prompt-mutation-memory_final | True | False | fixed,loss | fixed | loss |
| prompt-mutation-stored_memory | True | False | fixed,loss | fixed | loss |
| prompt-mutation-route_final | True | False | fixed,loss | fixed | loss |
| prompt-mutation-write_memory | True | False | fixed,loss | fixed | loss |
| prompt-mutation-complete_stored | True | False | fixed,loss | fixed | loss |
| prompt-mutation-self_check_output | True | False | fixed,loss | fixed | loss |
| prompt-mutation-return_memory | True | False | fixed,loss | fixed | loss |
| prompt-mutation-final_words_memory | True | False | fixed,loss | fixed | loss |
| prompt-mutation-stored_final | True | False | fixed,loss | fixed | loss |
| prompt-mutation-complete_memory | True | False | fixed,loss | fixed | loss |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | prompt-mutation holdout suite must pass |
| holdout_suite_ready | pass | True | prompt-mutation holdout suite summary must be ready |
| suite_ready | pass | True | benchmark suite must be ready |
| cases_present | pass | 10 | prompt-mutation holdout suite must include cases |
| case_count_matches_summary | pass | 10 | candidate case count must match suite cases |
| mutation_factor_at_least_two | pass | 2.0 | prompt mutation suite should expand source cases by at least 2x |
| prompt_mutated_rows_complete | pass | 10 | every candidate prompt should be marked mutated |
| prompt_mutation_no_task_hints | pass | 0 | prompt mutation suite should have no known task hints |
| expected_terms_complete | pass | ['fixed', 'loss'] | dry-run expects fixed/loss scoring contract |
| positive_rows_pass | pass | 10 | positive continuation must pass every case |
| negative_rows_fail | pass | 0 | negative continuation must not pass any case |
