# MiniGPT Required-Term Pair Fixed-Retention Objective Readiness

- Status: `pass`
- Decision: `design_fixed_retention_objective_before_more_loss_branch_training`
- Fixed-retention required: `True`
- First-token gap confirmed: `True`
- Model quality claim: `readiness_only`

## Requirements

| Requirement | Required | Reason | Acceptance |
| --- | --- | --- | --- |
| fixed_first_token_retention | True | fixed first token ranks behind loss/space on missed seeds | fixed_expected_rank must improve before adding more loss weighting |
| loss_branch_no_extra_weight | True | loss branch already wins while fixed drops | new corpus must not increase loss-only row density without fixed retention rows |
| pair_full_seed_gate | True | v590-v596 found only residual single-branch evidence | run at least one real seed before calling the objective useful |

## Boundary

- Reason: Loss branch is strong enough to dominate, while fixed first-token retention is weak across missed seeds.
- Next action: build a fixed-retention corpus objective with balanced first-token rows and a real seed gate
