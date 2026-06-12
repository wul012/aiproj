# MiniGPT decoder anchor vs unassisted holdout comparison v1147

- Generated: `2026-06-12T12:15:48Z`
- Status: `pass`
- Decision: `decoder_anchor_signal_exceeds_unassisted_holdout_replay`

## Summary

| Metric | Value |
| --- | --- |
| decoder_anchor_holdout_comparison_ready | True |
| anchor_probe_case_count | 5 |
| anchor_fragment_hit_count | 5 |
| anchor_loss_hit_count | 4 |
| unassisted_case_count | 5 |
| unassisted_any_term_hit_count | 3 |
| unassisted_fixed_hit_count | 0 |
| unassisted_loss_hit_count | 3 |
| unassisted_full_pair_count | 0 |
| anchor_fragment_hit_rate | 1.0 |
| unassisted_any_term_hit_rate | 0.6 |
| anchor_over_unassisted_hit_delta | 2 |
| model_quality_claim | anchor_assisted_signal_exceeds_unassisted_holdout_replay |
| promotion_ready | False |
| unassisted_success_claim | False |
| next_step | build_unassisted_holdout_repair_plan |
| failed_check_count | 0 |

## Anchor vs Unassisted Comparison Rows

| case_id | anchor_prompt | anchor_combined | anchor_fragment_hit | anchor_loss_hit | unassisted_prompt | unassisted_continuation | unassisted_hit_terms | unassisted_full_pair_hit | fragment_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| answer-colon-pair | fixed  | fixed lossssss | True | True | answer: |  the tos |  | False | 1 |
| answer-space-pair | lo | losssss nn | True | True | answer:  | lossssss | loss | False | 0 |
| completion-colon-pair | los | losssss nnn | True | True | completion: |  tosssss |  | False | 1 |
| finish-space-pair | fixed | fixed fixe fi | True | False | finish:  | ter loss | loss | False | 0 |
| compact-signal-answer-pair | fi | fier losss | True | True | state compact signal answer: | t signal answer: losssss | loss | False | 0 |

## Recommendations

- Keep v1147 as a contrastive diagnostic: anchor-assisted fragments are stronger than unassisted holdout responses.
- Do not promote the checkpoint until an unassisted fixed/loss pair replay passes.
- Use the next version to plan or train a small unassisted holdout repair rather than adding another governance wrapper.
