# MiniGPT model capability route promotion bounded real replay prompt-aligned seed revision

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_ready`
- Ready: `True`
- Total examples: `28`
- Exact prompt answers: `5`

## Seed Examples

| Example | Case | Type | Completion | Guardrail |
| --- | --- | --- | --- | --- |
| prompt-aligned-carry-revision-carry-repair-objective-answer-direct-direct_case_answer | objective-answer-direct | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-carry-repair-objective-answer-direct-self_check_answer | objective-answer-direct | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-carry-repair-objective-answer-role-direct_case_answer | objective-answer-role | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-carry-repair-objective-answer-role-self_check_answer | objective-answer-role | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-carry-repair-objective-answer-check-direct_case_answer | objective-answer-check | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-carry-repair-objective-answer-check-self_check_answer | objective-answer-check | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-check-missing_term_retention | objective-answer-check | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-check-contrastive_self_check | objective-answer-check | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-contrast-baseline_preservation | objective-answer-contrast | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-contrast-missing_term_retention | objective-answer-contrast | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-contrast-contrastive_self_check | objective-answer-contrast | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-direct-missing_term_retention | objective-answer-direct | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-direct-contrastive_self_check | objective-answer-direct | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-jsonish-baseline_preservation | objective-answer-jsonish | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-jsonish-missing_term_retention | objective-answer-jsonish | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-jsonish-contrastive_self_check | objective-answer-jsonish | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-role-missing_term_retention | objective-answer-role | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-carry-revision-objective-answer-role-contrastive_self_check | objective-answer-role | carry_forward_seed_revision | fixed loss | retain_revised_seed_signal |
| prompt-aligned-objective-answer-direct-exact_benchmark_prompt_answer | objective-answer-direct | exact_benchmark_prompt_answer | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-direct-exact_benchmark_prompt_self_check | objective-answer-direct | exact_benchmark_prompt_self_check | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-role-exact_benchmark_prompt_answer | objective-answer-role | exact_benchmark_prompt_answer | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-role-exact_benchmark_prompt_self_check | objective-answer-role | exact_benchmark_prompt_self_check | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-contrast-exact_benchmark_prompt_answer | objective-answer-contrast | exact_benchmark_prompt_answer | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-contrast-exact_benchmark_prompt_self_check | objective-answer-contrast | exact_benchmark_prompt_self_check | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-jsonish-exact_benchmark_prompt_answer | objective-answer-jsonish | exact_benchmark_prompt_answer | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-jsonish-exact_benchmark_prompt_self_check | objective-answer-jsonish | exact_benchmark_prompt_self_check | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-check-exact_benchmark_prompt_answer | objective-answer-check | exact_benchmark_prompt_answer | fixed loss | exact_benchmark_prompt_alignment |
| prompt-aligned-objective-answer-check-exact_benchmark_prompt_self_check | objective-answer-check | exact_benchmark_prompt_self_check | fixed loss | exact_benchmark_prompt_alignment |
