# MiniGPT Required-Term Pair Minimal Prompt Loss First-Token Repair Plan

- Status: `pass`
- Decision: `minimal_prompt_loss_first_token_repair_plan_ready`
- Proposed corpus mode: `minimal_prompt_loss_first_token_repair_objective`
- Repair focus: `loss_first_token_and_branch_separation`
- Model quality claim: `repair_plan_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| diagnostic_passed | pass | pass | branch-bias diagnostic must pass |
| fixed_absorbs_loss_confirmed | pass | minimal_prompt_branch_bias_fixed_absorbs_loss | repair plan requires confirmed fixed-absorbs-loss failure |
| loss_hit_absent | pass | 0 | loss branch should be absent before applying loss-first-token repair |
| fixed_hit_present | pass | 2 | fixed branch should remain a known signal while repairing loss |
| dominant_bias_fixed | pass | fixed | dominant bias must be fixed |

## Next Action

rerun seed 3535 with corpus_mode=minimal_prompt_loss_first_token_repair_objective
