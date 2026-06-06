# MiniGPT randomized target-hidden holdout real replay

- Status: `pass`
- Decision: `randomized_target_hidden_holdout_real_replay_passed_review_required`
- Model quality ready: `True`
- Passed cases: `20/20`
- Any-hit cases: `20`
- Zero-hit cases: `0`
- Pass rate: `1.0`
- Next step: `review_randomized_target_hidden_holdout_replay_result`

## Replay Rows

| Case | Draw | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- | --- |
| randomized-target-hidden-01 | 1 | True | fixed,loss |  |  fixed loss       fixed  |
| randomized-target-hidden-02 | 2 | True | fixed,loss |  |  fixed losss     fixed l |
| randomized-target-hidden-03 | 3 | True | fixed,loss |  |  fixed loss    fixed los |
| randomized-target-hidden-04 | 4 | True | fixed,loss |  |  fixed loss   fixed loss |
| randomized-target-hidden-05 | 5 | True | fixed,loss |  |  fixed loss        Compl |
| randomized-target-hidden-06 | 6 | True | fixed,loss |  |  fixed loss   fixed loss |
| randomized-target-hidden-07 | 7 | True | fixed,loss |  |  fixed losss fixed loss  |
| randomized-target-hidden-08 | 8 | True | fixed,loss |  |  fixed loss     fixed lo |
| randomized-target-hidden-09 | 9 | True | fixed,loss |  |  fixed loss    fixed los |
| randomized-target-hidden-10 | 10 | True | fixed,loss |  |  fixed loss    answer: f |
| randomized-target-hidden-11 | 11 | True | fixed,loss |  |  fixed loss    fixed los |
| randomized-target-hidden-12 | 12 | True | fixed,loss |  |  fixed loss      fixed l |
| randomized-target-hidden-13 | 13 | True | fixed,loss |  |  fixed loss    fixed los |
| randomized-target-hidden-14 | 14 | True | fixed,loss |  |  fixed loss    fixed los |
| randomized-target-hidden-15 | 15 | True | fixed,loss |  |  fixed loss   fixed loss |
| randomized-target-hidden-16 | 16 | True | fixed,loss |  |  fixed loss  fixed loss  |
| randomized-target-hidden-17 | 17 | True | fixed,loss |  |  fixed loss   fixed loss |
| randomized-target-hidden-18 | 18 | True | fixed,loss |  |  fixed loss  fixed loss  |
| randomized-target-hidden-19 | 19 | True | fixed,loss |  |  fixed loss   fixed loss |
| randomized-target-hidden-20 | 20 | True | fixed,loss |  |  fixed loss  fixed loss  |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | randomized holdout suite must pass |
| holdout_suite_ready | pass | True | randomized holdout suite summary must be ready |
| randomized_case_factor_at_least_two | pass | 2.0 | randomized suite should expand source cases |
| all_prompts_unique | pass | 20 | randomized prompts should be unique |
| all_prompts_target_hidden | pass | 20 | randomized prompts should remain target-hidden |
| dry_run_passed | pass | pass | dry-run must pass before real replay |
| dry_run_ready | pass | True | dry-run summary must be ready |
| negative_control_clean | pass | False | negative dry-run control must fail all cases |
| expected_terms_complete | pass | ['fixed', 'loss'] | real replay expects fixed/loss contract |
| checkpoint_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\checkpoint.pt | checkpoint.pt must exist |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| cases_present | pass | 20 | randomized holdout suite must include cases |
| all_cases_executed | pass | 20 | real replay should execute every case |
| no_replay_errors | pass | 0 | real replay should not raise generation errors |
