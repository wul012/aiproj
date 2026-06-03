# MiniGPT model capability route promotion bounded real replay

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps`
- Executed: `True`
- Model route quality ready: `False`
- Passed cases: `0/5`
- Pass rate: `0.0`
- Checkpoint: `D:\aiproj\e\810\解释\model-capability-route-promotion-bounded-real-replay-repair-training-run\run\checkpoint.pt`

## Replay Rows

| Case | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- |
| objective-answer-direct | False |  | fixed,loss | eeelidd i文ded 答rdd ddcoc |
| objective-answer-role | False |  | fixed,loss | aired required terms 的两个角色词。 输出：iieeds  cceee  ec r文e文文e |
| objective-answer-contrast | False |  | fixed,loss | ��任务：�要��，只��目标 pair tokens。 ��：clcle c    dc答deei sreen |
| objective-answer-jsonish | False |  | fixed,loss | �er�terms，��两个英文词。 ans�er�terms:i文rd文ddddissecroernneior |
| objective-answer-check | False |  | fixed,loss | 输e答  d答答c 答iicdcirec i d |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| suite_review_passed | pass | pass | suite review must pass before real replay |
| suite_review_approved | pass | True | suite review must approve real replay |
| benchmark_suite_passed | pass | pass | benchmark suite must pass |
| dry_run_passed | pass | pass | dry-run scorer must pass before real replay |
| dry_run_ready | pass | True | dry-run summary must be ready |
| checkpoint_exists | pass | D:\aiproj\e\810\解释\model-capability-route-promotion-bounded-real-replay-repair-training-run\run\checkpoint.pt | checkpoint.pt must exist |
| tokenizer_exists | pass | D:\aiproj\e\810\解释\model-capability-route-promotion-bounded-real-replay-repair-training-run\run\tokenizer.json | tokenizer.json must exist |
| cases_present | pass | 5 | benchmark suite must provide replay cases |
| all_cases_executed | pass | 5 | real replay should execute every case |
| no_replay_errors | pass | 0 | real replay should not raise generation errors |
