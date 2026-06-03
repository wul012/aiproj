# MiniGPT model capability route promotion bounded real replay

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps`
- Executed: `True`
- Model route quality ready: `False`
- Passed cases: `2/5`
- Pass rate: `0.4`
- Checkpoint: `D:\aiproj\e\770\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-training-run\pair-readiness-training-run\checkpoint.pt`

## Replay Rows

| Case | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- |
| objective-answer-direct | False | loss | fixed | ������������ ���branch lossssssssssss fi |
| objective-answer-role | False |  | fixed,loss | erms ������� ���epans loswer lorerered l |
| objective-answer-contrast | True | fixed,loss |  | pair tokens� ���obred fixed fixed lossss |
| objective-answer-jsonish | True | fixed,loss |  | �� answer_terms�s fixed losss brassssseq |
| objective-answer-check | False | loss | fixed | xed � loss������bred lossssssssssss fixe |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| suite_review_passed | pass | pass | suite review must pass before real replay |
| suite_review_approved | pass | True | suite review must approve real replay |
| benchmark_suite_passed | pass | pass | benchmark suite must pass |
| dry_run_passed | pass | pass | dry-run scorer must pass before real replay |
| dry_run_ready | pass | True | dry-run summary must be ready |
| checkpoint_exists | pass | D:\aiproj\e\770\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-training-run\pair-readiness-training-run\checkpoint.pt | checkpoint.pt must exist |
| tokenizer_exists | pass | D:\aiproj\e\770\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-3838-training-run\pair-readiness-training-run\tokenizer.json | tokenizer.json must exist |
| cases_present | pass | 5 | benchmark suite must provide replay cases |
| all_cases_executed | pass | 5 | real replay should execute every case |
| no_replay_errors | pass | 0 | real replay should not raise generation errors |
