# MiniGPT PTQ deployment candidate selector v1177

- Generated: `2026-06-17T01:41:06Z`
- Status: `pass`
- Decision: `ptq_deployment_candidate_selected`

## Summary

| Metric | Value |
| --- | --- |
| candidate_ready | True |
| source_status | pass |
| source_decision | ptq_measured |
| source_verdict | per_channel_advantage_not_separable |
| source_ptq_report | f\1175\解释\ptq_v1175\ptq_v1175.json |
| policy | max_dce_nats=0.08, max_exact_match_drop=0.1, max_kl_nats=0.1 |
| fp32_ce | 0.080853 |
| fp32_exact_match | 0.883333 |
| candidate_count | 15 |
| viable_candidate_count | 10 |
| selected_candidate_id | group32:3b |
| selected_granularity | group32 |
| selected_bits | 3 |
| selected_eff_bits | 3.5 |
| selected_ce_mean | 0.145139 |
| selected_dce_mean | 0.064286 |
| selected_kl_mean | 0.07137 |
| selected_em_mean | 0.792778 |
| selected_em_drop | 0.090555 |
| selected_effective_bit_reduction_vs_fp32 | 0.890625 |
| boundary | quality_cost_selection_only_no_int_kernel_speed_or_memory_claim |
| next_step | measure_selected_ptq_candidate_with_real_runtime_or_keep_as_quality_cost_reference |

## PTQ Candidate Rows

| candidate_id | granularity | bits | eff_bits | ce_mean | dce_mean | kl_mean | em_mean | em_drop | quality_budget_pass | reject_reasons | viable_rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| per_tensor:8b | per_tensor | 8 | 8.0014 | 0.080932 | 7.9e-05 | 9.4e-05 | 0.881111 | 0.002222 | True |  | 8 |
| per_tensor:6b | per_tensor | 6 | 6.0014 | 0.083875 | 0.003022 | 0.001815 | 0.878333 | 0.005 | True |  | 5 |
| per_tensor:4b | per_tensor | 4 | 4.0014 | 0.097258 | 0.016405 | 0.030221 | 0.852778 | 0.030555 | True |  | 2 |
| per_tensor:3b | per_tensor | 3 | 3.0014 | 0.539784 | 0.458931 | 0.489815 | 0.465 | 0.418333 | False | dce_above_budget,exact_match_drop_above_budget,kl_above_budget |  |
| per_tensor:2b | per_tensor | 2 | 2.0014 | 5.039588 | 4.958735 | 4.975965 | 0.0 | 0.883333 | False | dce_above_budget,exact_match_drop_above_budget,kl_above_budget |  |
| per_channel_row:8b | per_channel_row | 8 | 8.1878 | 0.081116 | 0.000263 | 3.6e-05 | 0.883333 | 0.0 | True |  | 9 |
| per_channel_row:6b | per_channel_row | 6 | 6.1878 | 0.080865 | 1.2e-05 | 0.000849 | 0.881667 | 0.001666 | True |  | 6 |
| per_channel_row:4b | per_channel_row | 4 | 4.1878 | 0.091388 | 0.010535 | 0.011153 | 0.864444 | 0.018889 | True |  | 3 |
| per_channel_row:3b | per_channel_row | 3 | 3.1878 | 0.167595 | 0.086742 | 0.089207 | 0.76 | 0.123333 | False | dce_above_budget,exact_match_drop_above_budget |  |
| per_channel_row:2b | per_channel_row | 2 | 2.1878 | 3.013654 | 2.932801 | 2.938791 | 0.023889 | 0.859444 | False | dce_above_budget,exact_match_drop_above_budget,kl_above_budget |  |
| group32:8b | group32 | 8 | 8.5 | 0.080992 | 0.000139 | 2.9e-05 | 0.881667 | 0.001666 | True |  | 10 |
| group32:6b | group32 | 6 | 6.5 | 0.081697 | 0.000844 | 0.000588 | 0.88 | 0.003333 | True |  | 7 |
| group32:4b | group32 | 4 | 4.5 | 0.090183 | 0.00933 | 0.009255 | 0.865 | 0.018333 | True |  | 4 |
| group32:3b | group32 | 3 | 3.5 | 0.145139 | 0.064286 | 0.07137 | 0.792778 | 0.090555 | True |  | 1 |
| group32:2b | group32 | 2 | 2.5 | 2.095955 | 2.015102 | 2.025453 | 0.058333 | 0.825 | False | dce_above_budget,exact_match_drop_above_budget,kl_above_budget |  |

## Recommendations

- Selected group32:3b as the lowest effective-bits candidate inside the configured quality budget.
- Keep the v1175 verdict in view (per_channel_advantage_not_separable): this is a quality-cost candidate, not proof of runtime speed or memory savings.
- Before deployment, validate the selected scheme with a real quantized runtime kernel or keep it as an offline compression-quality reference.
