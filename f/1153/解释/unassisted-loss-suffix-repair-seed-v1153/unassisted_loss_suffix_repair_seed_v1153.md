# MiniGPT unassisted loss suffix repair seed v1153

- Generated: `2026-06-12T15:03:52Z`
- Status: `pass`
- Decision: `unassisted_loss_suffix_repair_seed_ready`

## Summary

| Metric | Value |
| --- | --- |
| unassisted_loss_suffix_repair_seed_ready | True |
| base_example_count | 9 |
| repair_example_count | 6 |
| revised_example_count | 15 |
| loss_suffix_repair_example_count | 5 |
| zero_hit_full_pair_repair_example_count | 1 |
| target_free_holdout_prompt_count | 5 |
| training_only_context_count | 6 |
| corpus_char_count | 347 |
| model_quality_claim | seed_revision_only |
| promotion_ready | False |
| proposed_next_artifact | unassisted_loss_suffix_repair_training_run_v1154 |
| next_step | run_unassisted_loss_suffix_repair_training |
| failed_check_count | 0 |

## Revised Seed Rows

| example_id | kind | prompt | completion | repair_source_case_id | training_only_context | prompt_contains_target_terms |
| --- | --- | --- | --- | --- | --- | --- |
| pair-repair-01 | full_pair | answer: |  fixed loss |  | False | False |
| pair-repair-02 | full_pair | answer: |  fixed loss |  | False | False |
| pair-repair-03 | full_pair | completion: |  fixed loss |  | False | False |
| pair-repair-04 | full_pair | finish: |  fixed loss |  | False | False |
| pair-repair-05 | full_pair | state compact signal answer: |  fixed loss |  | False | False |
| fixed-first-01 | fixed_first | answer: |  fixed |  | False | False |
| fixed-first-02 | fixed_first | completion: |  fixed |  | False | False |
| loss-after-fixed-01 | loss_after_model_fixed | answer: fixed |  loss |  | True | True |
| pair-short-01 | short_pair | signal: |  fixed loss |  | False | False |
| loss-suffix-repair-01 | loss_suffix_after_fixed | answer: fixed |  loss | unassisted-holdout-01 | True | True |
| loss-suffix-repair-02 | loss_suffix_after_fixed | finish: fixed |  loss | unassisted-holdout-03 | True | True |
| loss-suffix-repair-03 | loss_suffix_after_fixed | state compact signal answer: fixed |  loss | unassisted-holdout-04 | True | True |
| loss-suffix-repair-04 | loss_suffix_after_fixed | signal: fixed |  loss | unassisted-holdout-05 | True | True |
| zero-hit-full-pair-repair-05 | zero_hit_full_pair_reinforcement | completion: |  fixed loss | unassisted-holdout-02 | False | False |
| loss-suffix-repair-06 | loss_suffix_after_fixed | completion: fixed |  loss | unassisted-holdout-02 | True | True |

## Recommendations

- Run bounded CPU training from the v1153 corpus before replaying holdout prompts.
- Keep v1153 holdout prompts target-free; do not evaluate on loss-suffix training-only prompts.
