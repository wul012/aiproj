# MiniGPT bounded objective loss signal bridge target-only memory decoder-budget holdout gap diagnostic

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_tokenizer_coverage_blocks_promotion`
- Dominant gap: `tokenizer_prompt_coverage_gap`
- Tokenizer coverage gaps: `4`
- Unseen prompt surface gaps: `0`
- Required-term generation gaps: `0`
- Prompt unknown tokens: `96`
- Prompt unknown rows: `5`
- Replacement rows: `5`
- Next step: `build_tokenizer_coverage_aware_holdout_suite_before_more_training`

## Diagnostic Rows

| Case | Pass | Failure class | Unknown | In corpus | Replacement | Hit terms | Missed terms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective-answer-direct | False | tokenizer_prompt_coverage_gap | 26 | False | 26 |  | fixed,loss |
| objective-answer-role | False | tokenizer_prompt_coverage_gap | 15 | False | 15 |  | fixed,loss |
| objective-answer-contrast | False | tokenizer_prompt_coverage_gap | 19 | False | 19 |  | fixed,loss |
| objective-answer-jsonish | False | tokenizer_prompt_coverage_gap | 18 | False | 18 |  | fixed,loss |
| objective-answer-check | True | passed | 18 | False | 18 | fixed,loss |  |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_replay_passed | pass | pass | holdout replay must pass structurally |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| training_corpus_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\prepared_corpus.txt | prepared training corpus must exist |
| replay_rows_present | pass | 5 | holdout replay must include replay rows |
| diagnostic_rows_complete | pass | 5 | diagnostic should cover every replay row |
