# MiniGPT target-hidden prompt-mutation holdout real replay

- Status: `pass`
- Decision: `target_hidden_prompt_mutation_holdout_real_replay_passed_review_required`
- Model quality ready: `True`
- Passed cases: `10/10`
- Any-hit cases: `10`
- Zero-hit cases: `0`
- Pass rate: `1.0`
- Next step: `review_target_hidden_prompt_mutation_holdout_replay_result`

## Replay Rows

| Case | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- |
| prompt-mutation-memory_final | True | fixed,loss |  |  fixed losss       fixed |
| prompt-mutation-stored_memory | True | fixed,loss |  |  fixed loss     fixed lo |
| prompt-mutation-route_final | True | fixed,loss |  |  fixed loss    fixed los |
| prompt-mutation-write_memory | True | fixed,loss |  |  fixed loss   fixed loss |
| prompt-mutation-complete_stored | True | fixed,loss |  |  fixed loss   fixed loss |
| prompt-mutation-self_check_output | True | fixed,loss |  |  fixed losss       fixed |
| prompt-mutation-return_memory | True | fixed,loss |  |  fixed loss      fixed l |
| prompt-mutation-final_words_memory | True | fixed,loss |  |  fixed loss   fixed loss |
| prompt-mutation-stored_final | True | fixed,loss |  |  fixed loss   fixed loss |
| prompt-mutation-complete_memory | True | fixed,loss |  |  fixed loss      fixed l |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | prompt-mutation holdout suite must pass |
| holdout_suite_ready | pass | True | prompt-mutation holdout suite summary must be ready |
| mutation_factor_at_least_two | pass | 2.0 | prompt mutation suite should expand source cases |
| prompt_mutated_rows_complete | pass | 10 | all candidate prompts should be mutated |
| dry_run_passed | pass | pass | dry-run must pass before real replay |
| dry_run_ready | pass | True | dry-run summary must be ready |
| expected_terms_complete | pass | ['fixed', 'loss'] | real replay expects fixed/loss contract |
| checkpoint_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\checkpoint.pt | checkpoint.pt must exist |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| cases_present | pass | 10 | prompt-mutation holdout suite must include cases |
| all_cases_executed | pass | 10 | real replay should execute every case |
| no_replay_errors | pass | 0 | real replay should not raise generation errors |
