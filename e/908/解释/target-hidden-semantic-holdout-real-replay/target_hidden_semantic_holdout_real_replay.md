# MiniGPT target-hidden semantic paraphrase holdout real replay

- Status: `pass`
- Decision: `target_hidden_semantic_holdout_real_replay_passed_review_required`
- Holdout model quality ready: `True`
- Semantic model quality ready: `True`
- Passed cases: `5/5`
- Any-hit cases: `5`
- Zero-hit cases: `0`
- Pass rate: `1.0`
- Next step: `review_target_hidden_semantic_holdout_replay_result`

## Replay Rows

| Case | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- |
| semantic-hidden-memory_answer | True | fixed,loss |  |  fixed loss     fixed lo |
| semantic-hidden-stored_result | True | fixed,loss |  |  fixed loss  fixed loss  |
| semantic-hidden-learned_route | True | fixed,loss |  |  fixed loss      fixed l |
| semantic-hidden-final_words | True | fixed,loss |  |  fixed loss   fixed loss |
| semantic-hidden-memory_self_check | True | fixed,loss |  |  fixed loss     Answer w |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_suite_passed | pass | pass | semantic holdout suite must pass |
| holdout_suite_ready | pass | True | semantic holdout suite summary must be ready |
| target_hidden_cases_present | pass | 5 | every semantic suite case must remain target-hidden |
| semantic_no_task_hints | pass | 0 | semantic holdout should have no known task hints |
| dry_run_passed | pass | pass | dry-run must pass before real replay |
| dry_run_ready | pass | True | dry-run summary must be ready |
| expected_terms_complete | pass | ['fixed', 'loss'] | real replay expects fixed/loss contract |
| checkpoint_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\checkpoint.pt | checkpoint.pt must exist |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| cases_present | pass | 5 | semantic holdout suite must include cases |
| all_cases_executed | pass | 5 | real replay should execute every case |
| no_replay_errors | pass | 0 | real replay should not raise generation errors |
