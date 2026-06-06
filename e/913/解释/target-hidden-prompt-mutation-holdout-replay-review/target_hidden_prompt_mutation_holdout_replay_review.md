# MiniGPT target-hidden prompt-mutation holdout replay review

- Status: `pass`
- Decision: `target_hidden_prompt_mutation_holdout_replay_review_clean_signal_randomized_holdout_required`
- Prompt-mutation model quality ready: `True`
- Target leakage cases: `0`
- Task hint cases: `0`
- Prompt-mutated cases: `10`
- Clean prompt-mutation cases: `10`
- Approved for randomized prompt holdout: `True`
- Approved for promotion: `False`
- Next step: `build_randomized_target_hidden_holdout_suite`

## Review Rows

| Case | Source | Leakage | Leaked | Hint | Hint terms | Mutated | Status | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| prompt-mutation-memory_final | semantic-hidden-memory_answer | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-stored_memory | semantic-hidden-stored_result | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-route_final | semantic-hidden-learned_route | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-write_memory | semantic-hidden-final_words | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-complete_stored | semantic-hidden-memory_self_check | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-self_check_output | semantic-hidden-memory_answer | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-return_memory | semantic-hidden-stored_result | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-final_words_memory | semantic-hidden-learned_route | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-stored_final | semantic-hidden-final_words | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |
| prompt-mutation-complete_memory | semantic-hidden-memory_self_check | False |  | False |  | True | clean_prompt_mutation_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and differs from source prompts |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| real_replay_passed | pass | pass | prompt-mutation real replay must pass structurally |
| real_replay_ready | pass | True | prompt-mutation real replay summary must be ready |
| prompt_mutation_model_ready | pass | True | prompt-mutation holdout model signal must be ready |
| suite_passed | pass | pass | prompt-mutation holdout suite must pass |
| suite_ready | pass | True | prompt-mutation holdout suite summary must be ready |
| mutation_factor_at_least_two | pass | 2.0 | prompt-mutation suite should expand source cases |
| suite_no_task_hints | pass | 0 | prompt-mutation suite should report no known task hints |
| prompt_mutated_rows_complete | pass | 10 | every suite case should be prompt-mutated |
| target_hidden_cases_present | pass | 10 | every suite case must remain target-hidden |
| cases_present | pass | 10 | suite cases must be present |
| review_rows_complete | pass | 10 | review must cover every case |
