# MiniGPT Loss-Internal-Preference Objective Comparison

- Status: `pass`
- Decision: `loss_internal_preference_objectives_confirm_branch_tradeoff`
- Pair-full reports: `0`
- Fixed-only reports: `2`
- Loss-only reports: `1`
- Union hit terms: `['fixed', 'loss']`

## Branch Rows

| Route | Hit Terms | Missed Terms | Pair Full |
| --- | --- | --- | --- |
| loss-internal-preference | ['fixed'] | ['loss'] | False |
| loss-internal-first-token | ['loss'] | ['fixed'] | False |
| loss-internal-ranked-choice | ['fixed'] | ['loss'] | False |

## Boundary

- Model quality claim: `tradeoff_only`
- Reason: The routes recover different branches but no route keeps both at once.
- Next action: run forced-choice diagnostics to separate generation failure from internal preference
