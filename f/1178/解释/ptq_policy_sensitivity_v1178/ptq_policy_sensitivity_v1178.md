# MiniGPT PTQ policy sensitivity v1178

- Generated: `2026-06-17T02:51:26Z`
- Status: `pass`
- Decision: `ptq_policy_sensitivity_measured`

## Summary

| Metric | Value |
| --- | --- |
| policy_sensitivity_ready | True |
| source_status | pass |
| source_verdict | per_channel_advantage_not_separable |
| source_ptq_report | f\1175\解释\ptq_v1175\ptq_v1175.json |
| profile_count | 3 |
| passing_profile_count | 3 |
| unique_selected_candidate_count | 3 |
| selected_candidate_ids | group32:3b, per_channel_row:3b, per_tensor:4b |
| selection_stable_across_profiles | False |
| default_profile_candidate | group32:3b |
| default_profile_eff_bits | 3.5 |
| default_profile_dce_mean | 0.064286 |
| default_profile_em_drop | 0.090555 |
| sensitivity_verdict | candidate_choice_changes_with_quality_budget |
| boundary | policy_sensitivity_only_reuses_v1175_quality_cost_evidence |
| next_step | use_balanced_default_unless_product_tolerance_explicitly_prefers_strict_or_aggressive |

## PTQ Policy Profiles

| profile_id | status | selected_candidate_id | selected_eff_bits | selected_dce_mean | selected_kl_mean | selected_em_drop | viable_candidate_count | max_dce_nats | max_exact_match_drop | max_kl_nats |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict_quality | pass | per_tensor:4b | 4.0014 | 0.016405 | 0.030221 | 0.030555 | 9 | 0.02 | 0.04 | 0.04 |
| balanced_default | pass | group32:3b | 3.5 | 0.064286 | 0.07137 | 0.090555 | 10 | 0.08 | 0.1 | 0.1 |
| aggressive_compression | pass | per_channel_row:3b | 3.1878 | 0.086742 | 0.089207 | 0.123333 | 11 | 0.1 | 0.14 | 0.11 |

## Recommendations

- Candidate choice changes across strict/default/aggressive budgets; do not present any single candidate as policy-invariant.
- Use the balanced_default profile as the project default because it keeps dCE, KL, and exact-match drop bounded without overstating runtime benefits.
- Choose strict_quality when visible accuracy is more important than compression; choose aggressive_compression only with an explicit tolerance for larger exact-match loss.
