# MiniGPT bounded objective loss signal bridge target-only memory target-hidden tokenizer-covered holdout suite

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_ready`
- Candidate cases: `5`
- Tokenizer-covered cases: `5`
- Target-hidden cases: `5`
- Candidate unknown tokens: `0`
- Source leakage cases: `5`
- Next step: `run_target_hidden_tokenizer_covered_holdout_dry_run`

## Coverage Rows

| Case | Source | Covered | Target Hidden | Unknown | Leaked Terms | Prompt |
| --- | --- | --- | --- | --- | --- | --- |
| target-hidden-answer_learned_pair | tokenizer-covered-answer_exact_terms | True | True | 0 | [] | answer with the learned pair answer: |
| target-hidden-return_target_pair | tokenizer-covered-return_target_words | True | True | 0 | [] | return the target pair output: |
| target-hidden-contrast_route_pair | tokenizer-covered-contrast_route_result | True | True | 0 | [] | contrast route pair result: |
| target-hidden-jsonish_answer_terms | tokenizer-covered-jsonish_answer_terms | True | True | 0 | [] | jsonish answer_terms target pair answer_terms: |
| target-hidden-self_check_pair | tokenizer-covered-self_check_terms | True | True | 0 | [] | self check requires target pair final answer: |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| replay_review_passed | pass | pass | replay review must pass |
| review_routes_to_target_hidden_suite | pass | build_target_hidden_tokenizer_covered_holdout_suite | review must route to target-hidden suite |
| source_suite_passed | pass | pass | source suite must pass |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| case_count_preserved | pass | 5 | target-hidden suite must preserve case count |
| coverage_rows_complete | pass | 5 | coverage rows must cover every case |
| all_prompts_tokenizer_covered | pass | 5 | all prompts must be tokenizer covered |
| all_prompts_target_hidden | pass | 5 | all prompts must hide expected terms |
