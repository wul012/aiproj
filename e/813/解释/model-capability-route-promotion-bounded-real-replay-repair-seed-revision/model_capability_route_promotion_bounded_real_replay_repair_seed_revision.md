# MiniGPT model capability route promotion bounded real replay repair seed revision

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_repair_seed_revision_ready`
- Ready: `True`
- Original examples: `6`
- Added examples: `12`
- Total examples: `18`
- Baseline preservation examples: `2`

## Seed Examples

| Example | Case | Type | Completion | Guardrail |
| --- | --- | --- | --- | --- |
| revision-carry-repair-objective-answer-direct-direct_case_answer | objective-answer-direct | carry_forward_original_repair_seed | fixed loss | retain_original_repair_signal |
| revision-carry-repair-objective-answer-direct-self_check_answer | objective-answer-direct | carry_forward_original_repair_seed | fixed loss | retain_original_repair_signal |
| revision-carry-repair-objective-answer-role-direct_case_answer | objective-answer-role | carry_forward_original_repair_seed | fixed loss | retain_original_repair_signal |
| revision-carry-repair-objective-answer-role-self_check_answer | objective-answer-role | carry_forward_original_repair_seed | fixed loss | retain_original_repair_signal |
| revision-carry-repair-objective-answer-check-direct_case_answer | objective-answer-check | carry_forward_original_repair_seed | fixed loss | retain_original_repair_signal |
| revision-carry-repair-objective-answer-check-self_check_answer | objective-answer-check | carry_forward_original_repair_seed | fixed loss | retain_original_repair_signal |
| revision-objective-answer-check-missing_term_retention | objective-answer-check | missing_term_retention | fixed loss | prove_failed_case_recovery_before_promotion |
| revision-objective-answer-check-contrastive_self_check | objective-answer-check | contrastive_self_check | fixed loss | require_replay_comparison_after_each_repair_training |
| revision-objective-answer-contrast-baseline_preservation | objective-answer-contrast | baseline_preservation | fixed loss | preserve_baseline_pass_before_accepting_repair_checkpoint |
| revision-objective-answer-contrast-missing_term_retention | objective-answer-contrast | missing_term_retention | fixed loss | prove_failed_case_recovery_before_promotion |
| revision-objective-answer-contrast-contrastive_self_check | objective-answer-contrast | contrastive_self_check | fixed loss | require_replay_comparison_after_each_repair_training |
| revision-objective-answer-direct-missing_term_retention | objective-answer-direct | missing_term_retention | fixed loss | prove_failed_case_recovery_before_promotion |
| revision-objective-answer-direct-contrastive_self_check | objective-answer-direct | contrastive_self_check | fixed loss | require_replay_comparison_after_each_repair_training |
| revision-objective-answer-jsonish-baseline_preservation | objective-answer-jsonish | baseline_preservation | fixed loss | preserve_baseline_pass_before_accepting_repair_checkpoint |
| revision-objective-answer-jsonish-missing_term_retention | objective-answer-jsonish | missing_term_retention | fixed loss | prove_failed_case_recovery_before_promotion |
| revision-objective-answer-jsonish-contrastive_self_check | objective-answer-jsonish | contrastive_self_check | fixed loss | require_replay_comparison_after_each_repair_training |
| revision-objective-answer-role-missing_term_retention | objective-answer-role | missing_term_retention | fixed loss | prove_failed_case_recovery_before_promotion |
| revision-objective-answer-role-contrastive_self_check | objective-answer-role | contrastive_self_check | fixed loss | require_replay_comparison_after_each_repair_training |
