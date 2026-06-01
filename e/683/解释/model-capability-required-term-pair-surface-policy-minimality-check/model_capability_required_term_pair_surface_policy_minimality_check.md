# MiniGPT Required-Term Pair Surface Policy Minimality Check

- Status: `pass`
- Decision: `required_term_pair_surface_policy_contextual_anchor_required`
- Selected policy: `pair_context_prefix`
- Contextual anchor required: `True`
- Model quality claim: `contextual_decode_policy_only`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| selected_policy_present | pass | selector must name a selected policy |
| selected_policy_stable | pass | selected policy must be stable across seeds |
| non_leaking_baseline_not_stable | pass | minimal non-leaking baselines are not stable, so contextual anchoring is still required |
| selected_policy_contextual_anchor | pass | selected policy should be marked as contextual anchor, not model baseline |
| promotion_blocked | pass | selector must block promotion before leakage/minimality is reviewed |

## Boundary

- Reason: The selected policy is stable, but non-leaking minimal baselines are not stable.
- Next action: treat the selected policy as a contextual decoding aid and run leakage-risk documentation
