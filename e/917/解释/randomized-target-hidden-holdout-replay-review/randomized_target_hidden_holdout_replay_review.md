# MiniGPT randomized target-hidden holdout replay review

- Status: `pass`
- Decision: `randomized_target_hidden_holdout_replay_review_clean_signal_candidate_packet_required`
- Randomized model quality ready: `True`
- Target leakage cases: `0`
- Task hint cases: `0`
- Unique prompts: `20`
- Clean randomized cases: `20`
- Candidate packet: `True`
- Promotion: `False`
- Next step: `build_randomized_holdout_candidate_promotion_packet`

## Review Rows

| Case | Source | Draw | Leakage | Hint | Unique | Randomized | Status | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-target-hidden-01 | prompt-mutation-memory_final | 1 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-02 | prompt-mutation-stored_memory | 2 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-03 | prompt-mutation-route_final | 3 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-04 | prompt-mutation-write_memory | 4 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-05 | prompt-mutation-complete_stored | 5 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-06 | prompt-mutation-self_check_output | 6 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-07 | prompt-mutation-return_memory | 7 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-08 | prompt-mutation-final_words_memory | 8 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-09 | prompt-mutation-stored_final | 9 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-10 | prompt-mutation-complete_memory | 10 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-11 | prompt-mutation-memory_final | 11 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-12 | prompt-mutation-stored_memory | 12 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-13 | prompt-mutation-route_final | 13 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-14 | prompt-mutation-write_memory | 14 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-15 | prompt-mutation-complete_stored | 15 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-16 | prompt-mutation-self_check_output | 16 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-17 | prompt-mutation-return_memory | 17 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-18 | prompt-mutation-final_words_memory | 18 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-19 | prompt-mutation-stored_final | 19 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |
| randomized-target-hidden-20 | prompt-mutation-complete_memory | 20 | False | False | True | True | clean_randomized_target_hidden_prompt | prompt hides expected terms, avoids known task hints, and is a unique randomized prompt |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| real_replay_passed | pass | pass | randomized real replay must pass structurally |
| real_replay_ready | pass | True | randomized real replay summary must be ready |
| randomized_model_ready | pass | True | randomized holdout model signal must be ready |
| suite_passed | pass | pass | randomized holdout suite must pass |
| suite_ready | pass | True | randomized holdout suite summary must be ready |
| candidate_count_at_least_twenty | pass | 20 | randomized review expects at least 20 cases |
| randomized_factor_at_least_two | pass | 2.0 | randomized suite should expand the source case count |
| suite_no_task_hints | pass | 0 | randomized suite should report no known task hints |
| suite_unique_prompts_complete | pass | 20 | every randomized prompt should be unique |
| target_hidden_cases_present | pass | 20 | every randomized case must remain target-hidden |
| cases_present | pass | 20 | suite cases must be present |
| review_rows_complete | pass | 20 | review must cover every case |
