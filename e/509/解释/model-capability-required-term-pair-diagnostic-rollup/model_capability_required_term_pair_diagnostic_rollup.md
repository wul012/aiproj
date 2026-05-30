# MiniGPT Required-Term Pair Diagnostic Rollup

- Status: `pass`
- Decision: `required_term_pair_next_span_objective`
- Rollup decision: `rollup_continue_with_span_objective`
- Passing stages: `6/6`

## Stages

| Stage | Status | Decision | Key metric | Source |
| --- | --- | --- | --- | --- |
| internal forced-choice signal | pass | required_term_pair_forced_choice_internal_match | full_match_variants=1 | e\503\解释\model-capability-required-term-pair-forced-choice-diagnostic\model_capability_required_term_pair_forced_choice_diagnostic.json |
| internal/free-generation gap | pass | required_term_pair_generation_gap_observed | internal_only_prompts=2 | e\504\解释\model-capability-required-term-pair-generation-gap\model_capability_required_term_pair_generation_gap.json |
| decoding profile partial expression | pass | required_term_pair_decoding_gap_partial_only | continuation_hits=2; full_profiles=0 | e\505\解释\model-capability-required-term-pair-decoding-gap-probe\model_capability_required_term_pair_decoding_gap_probe.json |
| first-token path trace | pass | required_term_pair_decoding_path_late_expression | first_sample_matches=0; late_hits=2 | e\506\解释\model-capability-required-term-pair-decoding-path-trace\model_capability_required_term_pair_decoding_path_trace.json |
| constrained first-token repair | pass | required_term_pair_first_token_repair_improved_partial | improved_prompts=2; full_profiles=0 | e\507\解释\model-capability-required-term-pair-first-token-repair\model_capability_required_term_pair_first_token_repair.json |
| prefix completion span check | pass | required_term_pair_prefix_completion_long_prefix | one_token_hits=3; span_gaps=3 | e\508\解释\model-capability-required-term-pair-prefix-completion-sweep\model_capability_required_term_pair_prefix_completion_sweep.json |

## Boundary

- Model quality claim: `diagnostic_rollup_only`
- Reason: Diagnostics show internal signal and partial generation, but prefix completion still has span gaps.
- Next action: build the smallest continuation-span training objective for fixed/loss instead of more decoding tweaks

## Next Experiment Plan

- Plan: `continuation_span_objective_fixed_loss`
- Recommended: `True`
- Reason: internal signal exists, decoding does not recover full profiles, and prefix completion still has span gaps

### Steps

- build a tiny continuation-span corpus where prompts stop immediately before fixed/loss
- train a candidate from the current best symmetric-anchor checkpoint with a small repeatable budget
- evaluate free generation, first-token rank, and prefix-completion minimum-hit length with the same prompts
- accept only if full-profile hits improve without losing the existing loss one-token completion signal

### Minimum Success Criteria

- decoding_profile_full_hit_count increases above 0
- fixed minimum_hit_prefix_token_count drops below 4
- loss one-token prefix completion is retained
- all generated artifacts link back to the v509 source rollup

### Excluded Options

- adding more decoding profiles before changing the span objective
- claiming production model quality from forced-prefix evidence
- training on unrelated larger data without preserving the fixed/loss prompt set
