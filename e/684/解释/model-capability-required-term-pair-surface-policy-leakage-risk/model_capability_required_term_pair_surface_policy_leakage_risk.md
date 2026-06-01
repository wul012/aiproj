# MiniGPT Required-Term Pair Surface Policy Leakage Risk

- Status: `pass`
- Decision: `required_term_pair_surface_policy_contextual_risk_documented`
- Selected policy: `pair_context_prefix`
- Risk level: `medium`
- Promotion allowed: `False`

## Risks

| Risk | Level | Detail |
| --- | --- | --- |
| contextual_anchor | medium | Prompt supplies the other term as an anchor. |
| minimal_prompt_not_stable | medium | Non-leaking single-label baselines are not stable. |
