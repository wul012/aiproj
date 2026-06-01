# MiniGPT Required-Term Pair Surface Policy Plan

- Status: `pass`
- Decision: `required_term_pair_surface_policy_plan_ready`
- Failure terms: `['loss']`
- Replay policies: `['single_label_default', 'single_label_suppress_newline', 'pair_context_prefix', 'dual_boundary_sentence']`
- Model quality claim: `surface_policy_plan_only`

## Policies

| Policy | Profile | Leakage | Replay | Purpose |
| --- | --- | --- | --- | --- |
| single_label_default | default | none | True | Measure the current minimal label prompt without changing decoding. |
| single_label_suppress_newline | suppress_newline_tokens | none | True | Check whether newline suppression alone repairs the missing surface term. |
| pair_context_prefix | suppress_newline_tokens | contextual_anchor | True | Test whether preserving the other learned term before the target label stabilizes the missed term. |
| dual_boundary_sentence | suppress_newline_tokens | contextual_anchor | True | Replay the corpus boundary wording at inference time without writing the target value. |
| target_echo_upper_bound | suppress_newline_tokens | target_echo | False | Keep a documented upper-bound policy out of replay because it already contains the answer. |

## Boundary

- Reason: The plan separates non-leaking baselines from contextual-anchor replay and excludes target-echo upper bounds.
- Next action: run surface policy replay over the dual-boundary seed reports
