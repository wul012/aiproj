# MiniGPT randomized target-hidden tokenizer-covered holdout suite

- Status: `pass`
- Decision: `randomized_target_hidden_holdout_suite_ready`
- Candidate cases: `20`
- Random seed: `914`
- Randomized factor: `2.0`
- Tokenizer-covered cases: `20`
- Target-hidden cases: `20`
- Task-hint cases: `0`
- Unique prompts: `20`
- Next step: `dry_run_randomized_target_hidden_holdout`

## Coverage Rows

| Case | Source | Draw | Covered | Target Hidden | Hint | Unique | Unknown | Prompt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-target-hidden-01 | prompt-mutation-memory_final | 1 | True | True | False | True | 0 | memory final answer output: |
| randomized-target-hidden-02 | prompt-mutation-stored_memory | 2 | True | True | False | True | 0 | result stored answer final: |
| randomized-target-hidden-03 | prompt-mutation-route_final | 3 | True | True | False | True | 0 | result learned self result: |
| randomized-target-hidden-04 | prompt-mutation-write_memory | 4 | True | True | False | True | 0 | self stored result final: |
| randomized-target-hidden-05 | prompt-mutation-complete_stored | 5 | True | True | False | True | 0 | memory result answer answer: |
| randomized-target-hidden-06 | prompt-mutation-self_check_output | 6 | True | True | False | True | 0 | result write answer result: |
| randomized-target-hidden-07 | prompt-mutation-return_memory | 7 | True | True | False | True | 0 | write self final final: |
| randomized-target-hidden-08 | prompt-mutation-final_words_memory | 8 | True | True | False | True | 0 | final complete result result: |
| randomized-target-hidden-09 | prompt-mutation-stored_final | 9 | True | True | False | True | 0 | complete check write output: |
| randomized-target-hidden-10 | prompt-mutation-complete_memory | 10 | True | True | False | True | 0 | complete final words answer: |
| randomized-target-hidden-11 | prompt-mutation-memory_final | 11 | True | True | False | True | 0 | answer result write result: |
| randomized-target-hidden-12 | prompt-mutation-stored_memory | 12 | True | True | False | True | 0 | check answer memory answer: |
| randomized-target-hidden-13 | prompt-mutation-route_final | 13 | True | True | False | True | 0 | write complete self answer: |
| randomized-target-hidden-14 | prompt-mutation-write_memory | 14 | True | True | False | True | 0 | write result final output: |
| randomized-target-hidden-15 | prompt-mutation-complete_stored | 15 | True | True | False | True | 0 | words complete write result: |
| randomized-target-hidden-16 | prompt-mutation-self_check_output | 16 | True | True | False | True | 0 | words result write final: |
| randomized-target-hidden-17 | prompt-mutation-return_memory | 17 | True | True | False | True | 0 | route result final final: |
| randomized-target-hidden-18 | prompt-mutation-final_words_memory | 18 | True | True | False | True | 0 | check route learned final: |
| randomized-target-hidden-19 | prompt-mutation-stored_final | 19 | True | True | False | True | 0 | final words write output: |
| randomized-target-hidden-20 | prompt-mutation-complete_memory | 20 | True | True | False | True | 0 | stored result answer final: |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| replay_review_passed | pass | pass | v913 replay review must pass |
| review_approves_randomized_holdout | pass | True | review must approve randomized holdout |
| review_routes_to_randomized_suite | pass | build_randomized_target_hidden_holdout_suite | review must route to randomized holdout suite |
| source_suite_passed | pass | pass | source prompt-mutation suite must pass |
| source_suite_ready | pass | True | source prompt-mutation suite summary must be ready |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| seed_positive | pass | 914 | random seed must be positive and reproducible |
| candidate_expands_source | pass | 20 | randomized suite should double the source prompt-mutation case count |
| coverage_rows_complete | pass | 20 | coverage rows must cover every case |
| all_prompts_tokenizer_covered | pass | 20 | all randomized prompts must be tokenizer covered |
| all_prompts_target_hidden | pass | 20 | all randomized prompts must hide expected terms |
| no_prompt_task_hints | pass | 0 | randomized prompts should avoid known task-hint terms |
| all_prompts_unique | pass | 20 | randomized prompts must be unique |
| all_prompts_new_vs_source | pass | 20 | randomized prompts should differ from source prompts |
