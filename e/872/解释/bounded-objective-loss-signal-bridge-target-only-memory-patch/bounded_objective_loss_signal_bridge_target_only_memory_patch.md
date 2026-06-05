# MiniGPT bounded objective loss signal bridge target-only memory patch

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_patch_ready`
- Patch examples: `24`
- Target-only examples: `14`
- Prompt-target memory: `3`
- Label-target memory: `3`
- Claim: `target_only_memory_patch_only`

## Patch Examples

| Example | Kind | Text | Source | Class |
| --- | --- | --- | --- | --- |
| canonical_direct_completion-target-only-a | target_only_completion_memory | fixed loss | canonical_direct_completion | exact_label_echo |
| canonical_direct_completion-target-only-b | target_only_completion_memory | fixed loss | canonical_direct_completion | exact_label_echo |
| canonical_direct_completion-prompt-target-memory | prompt_target_memory | Answer with exactly two tokens: fixed loss fixed loss | canonical_direct_completion | exact_label_echo |
| canonical_direct_completion-label-target-memory | label_target_memory | answer: fixed loss | canonical_direct_completion | exact_label_echo |
| minimal_direct_completion-target-only-a | target_only_completion_memory | fixed loss | minimal_direct_completion | exact_label_echo |
| minimal_direct_completion-target-only-b | target_only_completion_memory | fixed loss | minimal_direct_completion | exact_label_echo |
| minimal_direct_completion-prompt-target-memory | prompt_target_memory | Answer with exactly two words: fixed loss fixed loss | minimal_direct_completion | exact_label_echo |
| minimal_direct_completion-label-target-memory | label_target_memory | answer: fixed loss | minimal_direct_completion | exact_label_echo |
| completion_label_surface-target-only-a | target_only_completion_memory | fixed loss | completion_label_surface | label_prefix_fragment |
| completion_label_surface-target-only-b | target_only_completion_memory | fixed loss | completion_label_surface | label_prefix_fragment |
| completion_label_surface-prompt-target-memory | prompt_target_memory | Complete with exactly two tokens: fixed loss fixed loss | completion_label_surface | label_prefix_fragment |
| completion_label_surface-label-target-memory | label_target_memory | completion: fixed loss | completion_label_surface | label_prefix_fragment |
| global-fixed-loss-memory-1 | target_only_completion_memory | fixed loss | global | target_memory |
| global-fixed-loss-memory-2 | target_only_completion_memory | fixed loss | global | target_memory |
| global-fixed-loss-memory-3 | target_only_completion_memory | fixed loss | global | target_memory |
| global-fixed-loss-memory-4 | target_only_completion_memory | fixed loss | global | target_memory |
| global-fixed-loss-memory-5 | target_only_completion_memory | fixed loss | global | target_memory |
| global-fixed-loss-memory-6 | target_only_completion_memory | fixed loss | global | target_memory |
| global-fixed-loss-memory-7 | target_only_completion_memory | fixed loss | global | target_memory |
| global-fixed-loss-memory-8 | target_only_completion_memory | fixed loss | global | target_memory |
| global-two-token-answer | plain_target_statement | two token answer fixed loss | global | target_memory |
| global-canonical-completion | plain_target_statement | canonical completion fixed loss | global | target_memory |
| global-no-label-repeat-a | target_pair_repeat | fixed loss fixed loss | global | target_memory |
| global-no-label-repeat-b | target_pair_repeat | fixed loss fixed loss | global | target_memory |
