# MiniGPT target-hidden prompt-mutation tokenizer-covered holdout suite

- Status: `pass`
- Decision: `target_hidden_prompt_mutation_holdout_suite_ready`
- Candidate cases: `10`
- Mutation factor: `2.0`
- Tokenizer-covered cases: `10`
- Target-hidden cases: `10`
- Task-hint cases: `0`
- Prompt-mutated cases: `10`
- Next step: `run_target_hidden_prompt_mutation_holdout_dry_run`

## Coverage Rows

| Case | Source | Covered | Target Hidden | Task Hint | Mutated | Unknown | Prompt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| prompt-mutation-memory_final | semantic-hidden-memory_answer | True | True | False | True | 0 | memory answer final: |
| prompt-mutation-stored_memory | semantic-hidden-stored_result | True | True | False | True | 0 | stored memory output: |
| prompt-mutation-route_final | semantic-hidden-learned_route | True | True | False | True | 0 | learned final route result: |
| prompt-mutation-write_memory | semantic-hidden-final_words | True | True | False | True | 0 | write final memory answer: |
| prompt-mutation-complete_stored | semantic-hidden-memory_self_check | True | True | False | True | 0 | complete stored route final: |
| prompt-mutation-self_check_output | semantic-hidden-memory_answer | True | True | False | True | 0 | self check stored memory output: |
| prompt-mutation-return_memory | semantic-hidden-stored_result | True | True | False | True | 0 | return learned memory result: |
| prompt-mutation-final_words_memory | semantic-hidden-learned_route | True | True | False | True | 0 | final words memory answer: |
| prompt-mutation-stored_final | semantic-hidden-final_words | True | True | False | True | 0 | stored final words output: |
| prompt-mutation-complete_memory | semantic-hidden-memory_self_check | True | True | False | True | 0 | complete memory route result: |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| replay_review_passed | pass | pass | v909 replay review must pass |
| review_approves_prompt_mutation | pass | True | review must approve prompt-mutation holdout |
| review_routes_to_prompt_mutation | pass | build_prompt_mutation_target_hidden_holdout_suite | review must route to prompt-mutation suite |
| source_suite_passed | pass | pass | source semantic holdout suite must pass |
| source_suite_ready | pass | True | source semantic suite summary must be ready |
| tokenizer_exists | pass | e\890\解释\bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-training-run\run\tokenizer.json | tokenizer.json must exist |
| candidate_expands_source | pass | 10 | prompt mutation suite should expand the source case count |
| coverage_rows_complete | pass | 10 | coverage rows must cover every case |
| all_prompts_tokenizer_covered | pass | 10 | all prompts must be tokenizer covered |
| all_prompts_target_hidden | pass | 10 | all prompts must hide expected terms |
| no_prompt_task_hints | pass | 0 | prompt mutations should avoid known task-hint terms |
| all_prompts_mutated | pass | 10 | candidate prompts should differ from source prompts |
