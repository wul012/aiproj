# MiniGPT bounded objective loss signal bridge target-only memory tokenizer-coverage-aware holdout suite

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready`
- Candidate cases: `5`
- Tokenizer-covered cases: `5`
- Candidate unknown tokens: `0`
- Source unknown rows: `5`
- Next step: `run_tokenizer_coverage_aware_holdout_dry_run`

## Coverage Rows

| Case | Source | Covered | Unknown | Prompt |
| --- | --- | --- | --- | --- |
| tokenizer-covered-answer_exact_terms | objective-answer-direct | True | 0 | answer with exactly two words: fixed loss answer: |
| tokenizer-covered-return_target_words | objective-answer-role | True | 0 | return the two target words fixed loss output: |
| tokenizer-covered-contrast_route_result | objective-answer-contrast | True | 0 | contrast route result fixed loss result: |
| tokenizer-covered-jsonish_answer_terms | objective-answer-jsonish | True | 0 | jsonish answer_terms fixed loss answer_terms: |
| tokenizer-covered-self_check_terms | objective-answer-check | True | 0 | self check requires fixed and loss final answer: |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| holdout_gap_diagnostic_passed | pass | pass | holdout gap diagnostic must pass |
| diagnostic_routes_to_tokenizer_coverage_suite | pass | build_tokenizer_coverage_aware_holdout_suite_before_more_training | diagnostic must route to tokenizer-coverage-aware holdout suite |
| source_benchmark_suite_passed | pass | pass | source benchmark suite must pass |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| case_count_preserved | pass | 5 | candidate suite must preserve source case count |
| coverage_rows_complete | pass | 5 | coverage report must cover every candidate case |
| all_candidate_prompts_tokenizer_covered | pass | 5 | every candidate prompt must be tokenizer covered |
