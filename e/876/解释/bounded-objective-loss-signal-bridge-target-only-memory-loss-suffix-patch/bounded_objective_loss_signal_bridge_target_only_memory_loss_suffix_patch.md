# MiniGPT bounded objective loss signal bridge target-only memory loss-suffix patch

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_ready`
- Patch examples: `27`
- Target-pair examples: `12`
- Loss-suffix examples: `9`
- Loss-prefix bridge examples: `3`

## Patch Examples

| Example | Kind | Text | Source |
| --- | --- | --- | --- |
| canonical_direct_completion-target-pair-a | target_pair_memory | fixed loss | canonical_direct_completion |
| canonical_direct_completion-target-pair-b | target_pair_memory | fixed loss | canonical_direct_completion |
| canonical_direct_completion-loss-suffix | loss_suffix_memory | loss | canonical_direct_completion |
| canonical_direct_completion-prefix-bridge | loss_prefix_bridge | fixed l loss fixed loss | canonical_direct_completion |
| canonical_direct_completion-label-pair | minimal_label_pair | completion: fixed loss | canonical_direct_completion |
| minimal_direct_completion-target-pair-a | target_pair_memory | fixed loss | minimal_direct_completion |
| minimal_direct_completion-target-pair-b | target_pair_memory | fixed loss | minimal_direct_completion |
| minimal_direct_completion-loss-suffix | loss_suffix_memory | loss | minimal_direct_completion |
| minimal_direct_completion-prefix-bridge | loss_prefix_bridge | fixed l loss fixed loss | minimal_direct_completion |
| minimal_direct_completion-label-pair | minimal_label_pair | completion: fixed loss | minimal_direct_completion |
| completion_label_surface-target-pair-a | target_pair_memory | fixed loss | completion_label_surface |
| completion_label_surface-target-pair-b | target_pair_memory | fixed loss | completion_label_surface |
| completion_label_surface-loss-suffix | loss_suffix_memory | loss | completion_label_surface |
| completion_label_surface-prefix-bridge | loss_prefix_bridge | fixed l loss fixed loss | completion_label_surface |
| completion_label_surface-label-pair | minimal_label_pair | completion: fixed loss | completion_label_surface |
| global-loss-memory-1 | loss_suffix_memory | loss | global |
| global-loss-memory-2 | loss_suffix_memory | loss | global |
| global-loss-memory-3 | loss_suffix_memory | loss | global |
| global-loss-memory-4 | loss_suffix_memory | loss | global |
| global-loss-memory-5 | loss_suffix_memory | loss | global |
| global-loss-memory-6 | loss_suffix_memory | loss | global |
| global-fixed-loss-pair-1 | target_pair_memory | fixed loss | global |
| global-fixed-loss-pair-2 | target_pair_memory | fixed loss | global |
| global-fixed-loss-pair-3 | target_pair_memory | fixed loss | global |
| global-fixed-loss-pair-4 | target_pair_memory | fixed loss | global |
| global-fixed-loss-pair-5 | target_pair_memory | fixed loss | global |
| global-fixed-loss-pair-6 | target_pair_memory | fixed loss | global |
