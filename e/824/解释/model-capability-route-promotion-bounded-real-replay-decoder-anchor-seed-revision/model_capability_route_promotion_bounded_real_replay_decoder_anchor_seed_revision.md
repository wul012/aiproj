# MiniGPT model capability route promotion bounded real replay decoder anchor seed revision

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_ready`
- Ready: `True`
- Examples: `48`
- Added examples: `20`
- Bridge examples: `15`
- Direct examples: `5`

## Seed Examples

| ID | Case | Type | Completion | Guardrail |
| --- | --- | --- | --- | --- |
| decoder-anchor-carry-prompt-aligned-carry-revision-carry-repair-objective-answer-direct-direct_case_answer | objective-answer-direct | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-carry-repair-objective-answer-direct-self_check_answer | objective-answer-direct | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-carry-repair-objective-answer-role-direct_case_answer | objective-answer-role | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-carry-repair-objective-answer-role-self_check_answer | objective-answer-role | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-carry-repair-objective-answer-check-direct_case_answer | objective-answer-check | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-carry-repair-objective-answer-check-self_check_answer | objective-answer-check | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-check-missing_term_retention | objective-answer-check | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-check-contrastive_self_check | objective-answer-check | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-contrast-baseline_preservation | objective-answer-contrast | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-contrast-missing_term_retention | objective-answer-contrast | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-contrast-contrastive_self_check | objective-answer-contrast | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-direct-missing_term_retention | objective-answer-direct | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-direct-contrastive_self_check | objective-answer-direct | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-jsonish-baseline_preservation | objective-answer-jsonish | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-jsonish-missing_term_retention | objective-answer-jsonish | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-jsonish-contrastive_self_check | objective-answer-jsonish | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-role-missing_term_retention | objective-answer-role | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-carry-revision-objective-answer-role-contrastive_self_check | objective-answer-role | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-direct-exact_benchmark_prompt_answer | objective-answer-direct | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-direct-exact_benchmark_prompt_self_check | objective-answer-direct | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-role-exact_benchmark_prompt_answer | objective-answer-role | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-role-exact_benchmark_prompt_self_check | objective-answer-role | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-contrast-exact_benchmark_prompt_answer | objective-answer-contrast | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-contrast-exact_benchmark_prompt_self_check | objective-answer-contrast | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-jsonish-exact_benchmark_prompt_answer | objective-answer-jsonish | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-jsonish-exact_benchmark_prompt_self_check | objective-answer-jsonish | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-check-exact_benchmark_prompt_answer | objective-answer-check | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-carry-prompt-aligned-objective-answer-check-exact_benchmark_prompt_self_check | objective-answer-check | carry_forward_prompt_aligned_seed | fixed loss | retain_prompt_aligned_seed_signal |
| decoder-anchor-objective-answer-direct-unanchored_direct_answer | objective-answer-direct | unanchored_direct_answer | fixed loss | unanchored_exact_answer |
| decoder-anchor-objective-answer-direct-prefix_f_bridge | objective-answer-direct | prefix_f_bridge | ixed loss | first_character_bridge |
| decoder-anchor-objective-answer-direct-prefix_fixed_space_bridge | objective-answer-direct | prefix_fixed_space_bridge | loss | first_term_to_second_term_bridge |
| decoder-anchor-objective-answer-direct-prefix_fixed_l_bridge | objective-answer-direct | prefix_fixed_l_bridge | oss | second_term_prefix_bridge |
| decoder-anchor-objective-answer-role-unanchored_direct_answer | objective-answer-role | unanchored_direct_answer | fixed loss | unanchored_exact_answer |
| decoder-anchor-objective-answer-role-prefix_f_bridge | objective-answer-role | prefix_f_bridge | ixed loss | first_character_bridge |
| decoder-anchor-objective-answer-role-prefix_fixed_space_bridge | objective-answer-role | prefix_fixed_space_bridge | loss | first_term_to_second_term_bridge |
| decoder-anchor-objective-answer-role-prefix_fixed_l_bridge | objective-answer-role | prefix_fixed_l_bridge | oss | second_term_prefix_bridge |
| decoder-anchor-objective-answer-contrast-unanchored_direct_answer | objective-answer-contrast | unanchored_direct_answer | fixed loss | unanchored_exact_answer |
| decoder-anchor-objective-answer-contrast-prefix_f_bridge | objective-answer-contrast | prefix_f_bridge | ixed loss | first_character_bridge |
| decoder-anchor-objective-answer-contrast-prefix_fixed_space_bridge | objective-answer-contrast | prefix_fixed_space_bridge | loss | first_term_to_second_term_bridge |
| decoder-anchor-objective-answer-contrast-prefix_fixed_l_bridge | objective-answer-contrast | prefix_fixed_l_bridge | oss | second_term_prefix_bridge |
| decoder-anchor-objective-answer-jsonish-unanchored_direct_answer | objective-answer-jsonish | unanchored_direct_answer | fixed loss | unanchored_exact_answer |
| decoder-anchor-objective-answer-jsonish-prefix_f_bridge | objective-answer-jsonish | prefix_f_bridge | ixed loss | first_character_bridge |
| decoder-anchor-objective-answer-jsonish-prefix_fixed_space_bridge | objective-answer-jsonish | prefix_fixed_space_bridge | loss | first_term_to_second_term_bridge |
| decoder-anchor-objective-answer-jsonish-prefix_fixed_l_bridge | objective-answer-jsonish | prefix_fixed_l_bridge | oss | second_term_prefix_bridge |
| decoder-anchor-objective-answer-check-unanchored_direct_answer | objective-answer-check | unanchored_direct_answer | fixed loss | unanchored_exact_answer |
| decoder-anchor-objective-answer-check-prefix_f_bridge | objective-answer-check | prefix_f_bridge | ixed loss | first_character_bridge |
| decoder-anchor-objective-answer-check-prefix_fixed_space_bridge | objective-answer-check | prefix_fixed_space_bridge | loss | first_term_to_second_term_bridge |
| decoder-anchor-objective-answer-check-prefix_fixed_l_bridge | objective-answer-check | prefix_fixed_l_bridge | oss | second_term_prefix_bridge |
