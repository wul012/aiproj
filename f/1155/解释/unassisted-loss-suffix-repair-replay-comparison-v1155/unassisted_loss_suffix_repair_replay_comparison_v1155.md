# MiniGPT unassisted loss suffix repair replay comparison v1155

- Generated: `2026-06-12T15:52:18Z`
- Status: `pass`
- Decision: `unassisted_loss_suffix_repair_replay_partial_signal`

## Summary

| Metric | Value |
| --- | --- |
| unassisted_loss_suffix_repair_replay_comparison_ready | True |
| case_count | 5 |
| fixed_hit_case_count | 5 |
| loss_hit_case_count | 0 |
| full_pair_case_count | 0 |
| any_hit_case_count | 5 |
| full_pair_rate | 0.0 |
| all_full_pair_hit | False |
| partial_signal_visible | True |
| model_quality_claim | bounded_holdout_replay_partial_signal |
| promotion_ready | False |
| next_step | diagnose_unassisted_loss_suffix_repair_partial_signal |
| failed_check_count | 0 |

## Replay Generations

| case_id | prompt | continuation | expected_terms | fixed_hit | loss_hit | full_pair_hit | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| unassisted-holdout-01 | answer: |  fixed l | fixed, loss | True | False | False | partial |
| unassisted-holdout-02 | completion: |  fixed l | fixed, loss | True | False | False | partial |
| unassisted-holdout-03 | finish: |  fixed l | fixed, loss | True | False | False | partial |
| unassisted-holdout-04 | state compact signal answer: | e compact signal answer: fixed l | fixed, loss | True | False | False | partial |
| unassisted-holdout-05 | signal: |  fixed l | fixed, loss | True | False | False | partial |
