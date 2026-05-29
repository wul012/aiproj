# MiniGPT Model Capability Token Budget Stability

- Status: `pass`
- Decision: `token_budget_stability_ready`
- Stability decision: `repeated_token_budget_relief_without_score_progress`
- Token relief seeds: `2`
- Persistent fail relief seeds: `2`
- Score/pass progress seeds: `0`
- Mean token stall delta: `-9.0`
- Mean persistent fail delta: `-9.0`

| Seed | Status | Token stall delta | Persistent fail delta | Score delta | Pass delta | Decision |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1337 | pass | -9.0 | -9.0 | 0.0 | 0.0 | longer_token_budget_reduces_eval_stall |
| 2026 | pass | -9.0 | -9.0 | 0.0 | 0.0 | longer_token_budget_reduces_eval_stall |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Longer token budgets repeatedly reduced token/shape stalls, but did not improve score or pass-transition evidence.
- Next action: keep cap 12 as the evaluation budget and probe data/rubric changes before increasing model size
