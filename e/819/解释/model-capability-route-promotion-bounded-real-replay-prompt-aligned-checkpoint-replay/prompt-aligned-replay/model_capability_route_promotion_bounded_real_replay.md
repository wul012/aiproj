# MiniGPT model capability route promotion bounded real replay

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps`
- Executed: `True`
- Model route quality ready: `False`
- Passed cases: `0/5`
- Pass rate: `0.0`
- Checkpoint: `e\818\解释\model-capability-route-promotion-bounded-real-replay-prompt-aligned-training-run\run\checkpoint.pt`

## Replay Rows

| Case | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- |
| objective-answer-direct | False |  | fixed,loss | txrd Ai si  t iits ssdee |
| objective-answer-role | False |  | fixed,loss | aired required terms 的两个角色词。 输出：   i i  d  a  dt a  n ff |
| objective-answer-contrast | False |  | fixed,loss | fi i     t nt   ddtiffdd |
| objective-answer-jsonish | False |  | fixed,loss | wer_terms，包含两个英文词。 answer_terms:fts   td st    ets dfta  |
| objective-answer-check | False |  | fixed,loss | fi         t e  ien ff   |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| suite_review_passed | pass | pass | suite review must pass before real replay |
| suite_review_approved | pass | True | suite review must approve real replay |
| benchmark_suite_passed | pass | pass | benchmark suite must pass |
| dry_run_passed | pass | pass | dry-run scorer must pass before real replay |
| dry_run_ready | pass | True | dry-run summary must be ready |
| checkpoint_exists | pass | e\818\解释\model-capability-route-promotion-bounded-real-replay-prompt-aligned-training-run\run\checkpoint.pt | checkpoint.pt must exist |
| tokenizer_exists | pass | e\818\解释\model-capability-route-promotion-bounded-real-replay-prompt-aligned-training-run\run\tokenizer.json | tokenizer.json must exist |
| cases_present | pass | 5 | benchmark suite must provide replay cases |
| all_cases_executed | pass | 5 | real replay should execute every case |
| no_replay_errors | pass | 0 | real replay should not raise generation errors |
