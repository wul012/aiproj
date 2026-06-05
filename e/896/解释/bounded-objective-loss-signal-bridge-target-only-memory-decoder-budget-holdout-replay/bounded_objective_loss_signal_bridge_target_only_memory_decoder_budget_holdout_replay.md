# MiniGPT bounded objective loss signal bridge target-only memory decoder-budget holdout replay

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_partial_model_gap`
- Source contract recovered: `True`
- Holdout quality ready: `False`
- Passed cases: `1/5`
- Any-hit cases: `1`
- Promotion ready: `False`
- Model quality claim: `objective_contract_recovered_holdout_failed`
- Next step: `diagnose_holdout_prompt_generalization_gap_before_more_training`

## Replay Rows

| Case | Pass | Hit terms | Missed terms | Budget | Continuation |
| --- | --- | --- | --- | --- | --- |
| objective-answer-direct | False |  | fixed,loss | 24 | ����������������������� ���n can can cal ss canompl |
| objective-answer-role | False |  | fixed,loss | 24 | ����� paired required terms ������� ���an tin can cacacacacact  |
| objective-answer-contrast | False |  | fixed,loss | 24 | ��������������� pair tokens� ���nis canompletion s: s ca |
| objective-answer-jsonish | False |  | fixed,loss | 24 | �� ��O� ���� answer_terms��������� answer_terms: canicaly th anss acactl |
| objective-answer-check | True | fixed,loss |  | 24 | ����������� fixed � loss������et t os can cacat s caca |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| suite_review_passed | pass | pass | suite review must pass before real replay |
| suite_review_approved | pass | True | suite review must approve real replay |
| benchmark_suite_passed | pass | pass | benchmark suite must pass |
| dry_run_passed | pass | pass | dry-run scorer must pass before real replay |
| dry_run_ready | pass | True | dry-run summary must be ready |
| checkpoint_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\checkpoint.pt | checkpoint.pt must exist |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| cases_present | pass | 5 | benchmark suite must provide replay cases |
| all_cases_executed | pass | 5 | real replay should execute every case |
| no_replay_errors | pass | 0 | real replay should not raise generation errors |
| decoder_budget_replay_passed | pass | pass | decoder-budget replay must pass structurally |
| decoder_budget_replay_ready | pass | True | decoder-budget replay comparison must be ready |
| source_objective_contract_recovered | pass | True | source replay must recover the original objective contract before holdout |
| source_next_step_requires_holdout | pass | run_unchanged_bounded_suite_holdout_replay | source replay must explicitly require unchanged holdout replay |
