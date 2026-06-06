# MiniGPT randomized target-hidden holdout dry-run

- Status: `pass`
- Decision: `randomized_target_hidden_holdout_dry_run_passed`
- Cases: `20`
- Source random seed: `914`
- Source randomized factor: `2.0`
- Positive passed: `20/20`
- Negative passed: `0`
- Negative control passed: `False`
- Next step: `run_randomized_target_hidden_holdout_real_replay`

## Dry-Run Rows

| Case | Draw | Positive pass | Negative pass | Positive hit | Negative hit | Negative missed |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-target-hidden-01 | 1 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-02 | 2 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-03 | 3 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-04 | 4 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-05 | 5 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-06 | 6 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-07 | 7 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-08 | 8 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-09 | 9 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-10 | 10 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-11 | 11 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-12 | 12 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-13 | 13 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-14 | 14 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-15 | 15 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-16 | 16 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-17 | 17 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-18 | 18 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-19 | 19 | True | False | fixed,loss | fixed | loss |
| randomized-target-hidden-20 | 20 | True | False | fixed,loss | fixed | loss |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | randomized holdout suite must pass |
| holdout_suite_ready | pass | True | randomized holdout suite summary must be ready |
| suite_ready | pass | True | benchmark suite must be ready |
| cases_present | pass | 20 | randomized holdout suite must include cases |
| case_count_matches_summary | pass | 20 | candidate case count must match suite cases |
| randomized_case_factor_at_least_two | pass | 2.0 | randomized suite should double the source case count |
| all_cases_tokenizer_covered | pass | 20 | all randomized cases must be tokenizer-covered |
| all_cases_target_hidden | pass | 20 | all randomized cases must hide expected terms |
| no_task_hints | pass | 0 | randomized suite should have no known task hints |
| all_prompts_unique | pass | 20 | randomized suite prompts must be unique |
| expected_terms_complete | pass | ['fixed', 'loss'] | dry-run expects fixed/loss scoring contract |
| positive_rows_pass | pass | 20 | positive continuation must pass every case |
| negative_rows_fail | pass | 0 | negative continuation must not pass any case |
