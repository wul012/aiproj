# MiniGPT bounded objective loss signal bridge target-only memory stabilized loss-suffix uptake patch

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_ready`
- Patch examples: `24`
- Fixed-l uptake: `6`
- Fixed-lo uptake: `3`
- Global suffix: `6`
- Surface carry-forward: `9`

## Patch Examples

| Example | Kind | Text | Source |
| --- | --- | --- | --- |
| canonical_direct_completion-fixed-l-to-loss-a | fixed_l_to_loss_uptake | fixed l fixed loss | canonical_direct_completion |
| canonical_direct_completion-fixed-l-to-loss-b | fixed_l_to_loss_uptake | fixed l fixed loss | canonical_direct_completion |
| canonical_direct_completion-fixed-lo-to-loss | fixed_lo_to_loss_uptake | fixed lo fixed loss | canonical_direct_completion |
| canonical_direct_completion-surface-pair | surface_pair_carry_forward | Complete with exactly two tokens: fixed loss completion: fixed loss | canonical_direct_completion |
| minimal_direct_completion-fixed-l-to-loss-a | fixed_l_to_loss_uptake | fixed l fixed loss | minimal_direct_completion |
| minimal_direct_completion-fixed-l-to-loss-b | fixed_l_to_loss_uptake | fixed l fixed loss | minimal_direct_completion |
| minimal_direct_completion-fixed-lo-to-loss | fixed_lo_to_loss_uptake | fixed lo fixed loss | minimal_direct_completion |
| minimal_direct_completion-surface-pair | surface_pair_carry_forward | Complete with exactly two tokens: fixed loss completion: fixed loss | minimal_direct_completion |
| completion_label_surface-fixed-l-to-loss-a | fixed_l_to_loss_uptake | fixed l fixed loss | completion_label_surface |
| completion_label_surface-fixed-l-to-loss-b | fixed_l_to_loss_uptake | fixed l fixed loss | completion_label_surface |
| completion_label_surface-fixed-lo-to-loss | fixed_lo_to_loss_uptake | fixed lo fixed loss | completion_label_surface |
| completion_label_surface-surface-pair | surface_pair_carry_forward | Complete with exactly two tokens: fixed loss completion: fixed loss | completion_label_surface |
| global-suffix-uptake-1 | global_suffix_uptake | loss fixed loss | global |
| global-suffix-uptake-2 | global_suffix_uptake | l loss fixed loss | global |
| global-suffix-uptake-3 | global_suffix_uptake | lo loss fixed loss | global |
| global-suffix-uptake-4 | global_suffix_uptake | fixed loss fixed loss | global |
| global-suffix-uptake-5 | global_suffix_uptake | fixed l loss fixed loss | global |
| global-suffix-uptake-6 | global_suffix_uptake | fixed lo loss fixed loss | global |
| surface-carry-forward-1 | surface_pair_carry_forward | Answer with exactly two tokens: fixed loss answer: fixed loss | global |
| surface-carry-forward-2 | surface_pair_carry_forward | Answer with exactly two words: fixed loss answer: fixed loss | global |
| surface-carry-forward-3 | surface_pair_carry_forward | Complete with exactly two tokens: fixed loss completion: fixed loss | global |
| surface-carry-forward-4 | surface_pair_carry_forward | Complete with exactly two words: fixed loss completion: fixed loss | global |
| surface-carry-forward-5 | surface_pair_carry_forward | answer: fixed loss | global |
| surface-carry-forward-6 | surface_pair_carry_forward | completion: fixed loss | global |
