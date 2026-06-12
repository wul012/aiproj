# MiniGPT unassisted holdout repair seed corpus v1149

- Generated: `2026-06-12T13:11:57Z`
- Status: `pass`
- Decision: `unassisted_holdout_repair_seed_corpus_ready`

## Summary

| Metric | Value |
| --- | --- |
| unassisted_holdout_repair_seed_corpus_ready | True |
| example_count | 9 |
| unique_prompt_count | 6 |
| pair_example_count | 7 |
| target_free_holdout_prompt_count | 5 |
| training_only_context_count | 1 |
| decoder_anchor_example_count | 0 |
| corpus_char_count | 198 |
| model_quality_claim | seed_corpus_only |
| promotion_ready | False |
| proposed_next_artifact | unassisted_holdout_repair_training_run_v1150 |
| next_step | run_unassisted_holdout_repair_training |
| failed_check_count | 0 |

## Seed Corpus Examples

| example_id | kind | prompt | completion | text | decoder_anchor | training_only_context | prompt_contains_target_terms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair-repair-01 | full_pair | answer: |  fixed loss | answer: fixed loss | False | False | False |
| pair-repair-02 | full_pair | answer: |  fixed loss | answer: fixed loss | False | False | False |
| pair-repair-03 | full_pair | completion: |  fixed loss | completion: fixed loss | False | False | False |
| pair-repair-04 | full_pair | finish: |  fixed loss | finish: fixed loss | False | False | False |
| pair-repair-05 | full_pair | state compact signal answer: |  fixed loss | state compact signal answer: fixed loss | False | False | False |
| fixed-first-01 | fixed_first | answer: |  fixed | answer: fixed | False | False | False |
| fixed-first-02 | fixed_first | completion: |  fixed | completion: fixed | False | False | False |
| loss-after-fixed-01 | loss_after_model_fixed | answer: fixed |  loss | answer: fixed loss | False | True | True |
| pair-short-01 | short_pair | signal: |  fixed loss | signal: fixed loss | False | False | False |
