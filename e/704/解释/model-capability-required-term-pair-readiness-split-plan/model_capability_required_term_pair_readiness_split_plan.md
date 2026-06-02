# MiniGPT Required-Term Pair-Readiness Split Plan

- Status: `pass`
- Decision: `pair_readiness_split_plan_ready`
- Proposed next artifact: `pair_readiness_split_contract`
- Model quality claim: `plan_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| closeout_passed | pass | pass | minimal prompt closeout must pass |
| closeout_decision | pass | minimal_prompt_batch_closed_without_pair_full | split plan only follows a closed no-pair-full minimal-prompt batch |
| three_real_reports | pass | 3 | need at least three real attempts |
| no_pair_full | pass | 0 | pair-full candidate should be promoted instead of planning a split |
| mixed_failures | pass | fixed=1, loss=2 | split plan needs evidence that both branches can win separately |

## Split

- Training split: `direct_branch_completion_rows, anti_contamination_rows, balanced_prefix_progression_rows`
- Evaluation split: `fixed=, loss=, heldout_fixed_loss_pair_probe`
- Promotion guard: `claim pair capability only when heldout fixed and loss continuations both hit`
