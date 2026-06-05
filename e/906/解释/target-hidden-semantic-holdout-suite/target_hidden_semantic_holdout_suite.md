# MiniGPT target-hidden semantic paraphrase tokenizer-covered holdout suite

- Status: `pass`
- Decision: `target_hidden_semantic_holdout_suite_ready`
- Candidate cases: `5`
- Tokenizer-covered cases: `5`
- Target-hidden cases: `5`
- Task-hint cases: `0`
- Source task-hint cases: `5`
- Next step: `run_target_hidden_semantic_holdout_dry_run`

## Coverage Rows

| Case | Source | Covered | Target Hidden | Task Hint | Unknown | Prompt |
| --- | --- | --- | --- | --- | --- | --- |
| semantic-hidden-memory_answer | target-hidden-answer_learned_pair | True | True | False | 0 | answer from memory answer: |
| semantic-hidden-stored_result | target-hidden-return_target_pair | True | True | False | 0 | write stored result output: |
| semantic-hidden-learned_route | target-hidden-contrast_route_pair | True | True | False | 0 | complete learned route result: |
| semantic-hidden-final_words | target-hidden-jsonish_answer_terms | True | True | False | 0 | return final words answer: |
| semantic-hidden-memory_self_check | target-hidden-self_check_pair | True | True | False | 0 | self check memory result final: |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| replay_review_passed | pass | pass | v905 replay review must pass |
| review_approves_wider_holdout | pass | True | review must approve wider holdout |
| review_routes_to_semantic_suite | pass | build_semantic_paraphrase_target_hidden_holdout_suite | review must route to semantic suite |
| source_suite_passed | pass | pass | source target-hidden suite must pass |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| case_count_preserved | pass | 5 | semantic suite must preserve case count |
| coverage_rows_complete | pass | 5 | coverage rows must cover every case |
| all_prompts_tokenizer_covered | pass | 5 | all prompts must be tokenizer covered |
| all_prompts_target_hidden | pass | 5 | all prompts must hide expected terms |
| no_prompt_task_hints | pass | 0 | semantic suite should avoid known task-hint terms |
