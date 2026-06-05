# MiniGPT target-hidden semantic paraphrase holdout dry-run

- Status: `pass`
- Decision: `target_hidden_semantic_holdout_dry_run_passed`
- Positive passed: `5/5`
- Negative passed: `0`
- Negative control passed: `False`
- Next step: `run_target_hidden_semantic_holdout_real_replay`

## Dry-Run Rows

| Case | Positive pass | Negative pass | Positive hit | Negative hit | Negative missed |
| --- | --- | --- | --- | --- | --- |
| semantic-hidden-memory_answer | True | False | fixed,loss | fixed | loss |
| semantic-hidden-stored_result | True | False | fixed,loss | fixed | loss |
| semantic-hidden-learned_route | True | False | fixed,loss | fixed | loss |
| semantic-hidden-final_words | True | False | fixed,loss | fixed | loss |
| semantic-hidden-memory_self_check | True | False | fixed,loss | fixed | loss |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | semantic holdout suite must pass |
| holdout_suite_ready | pass | True | semantic holdout suite summary must be ready |
| suite_ready | pass | True | benchmark suite must be ready |
| cases_present | pass | 5 | semantic holdout suite must include cases |
| semantic_no_task_hints | pass | 0 | semantic holdout should have no known task hints |
| expected_terms_complete | pass | ['fixed', 'loss'] | dry-run expects fixed/loss scoring contract |
| positive_rows_pass | pass | 5 | positive continuation must pass every case |
| negative_rows_fail | pass | 0 | negative continuation must not pass any case |
