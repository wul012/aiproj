# MiniGPT bounded objective loss signal bridge target-only memory loss-suffix replay regression diagnostic

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_sample_success_contract_regression`
- Sample has `fixed loss`: `True`
- Objective recovered: `False`
- Any-hit delta: `-1`
- Zero-hit delta: `1`
- Completion surface regressed to zero: `True`
- Next step: `build_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch`

## Regression

| Metric | Value |
| --- | --- |
| any_hit_delta | -1 |
| baseline_any_hit_case_count | 3 |
| baseline_passed_case_count | 0 |
| baseline_zero_hit_case_count | 0 |
| completion_surface_baseline_label | fixed_l_partial |
| completion_surface_current_label | completion_surface_zero_regression |
| completion_surface_regressed_to_zero | True |
| current_any_hit_case_count | 2 |
| current_passed_case_count | 0 |
| current_zero_hit_case_count | 1 |
| fixed_l_partial_case_count | 2 |
| next_step | build_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch |
| objective_contract_recovered | False |
| passed_case_delta | 0 |
| ready | True |
| sample_contract_gap | True |
| zero_hit_delta | 1 |

## Current Case Diagnostics

| Case | Label | Any hit | Hit | Missed | Continuation |
| --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | fixed_l_partial | True | fixed | loss |  fixed l |
| minimal_direct_completion | fixed_l_partial | True | fixed | loss |  fixed l |
| completion_label_surface | completion_surface_zero_regression | False |  | fixed,loss |  an: fix |

## Baseline Case Diagnostics

| Case | Label | Any hit | Hit | Missed | Continuation |
| --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | fixed_l_partial | True | fixed | loss |  fixed l |
| minimal_direct_completion | fixed_l_partial | True | fixed | loss |  fixed l |
| completion_label_surface | fixed_l_partial | True | fixed | loss |  fixed l |
