# MiniGPT Required-Term Pair Branch-Retention Sweep

- Status: `pass`
- Decision: `required_term_pair_branch_retention_partial`
- Sweep decision: `branch_retention_sweep_tradeoff_remains`
- Source loss-branch decision: `loss_branch_sweep_tradeoff_only`
- Targets: `1`
- Variants: `3`
- Training pass count: `3`
- Balanced variants: `0`
- Full-hit variants: `0`

## Variant Results

| Pair | Variant | Hits | Missed | Balanced | Full hit | Tradeoff |
| --- | --- | --- | --- | --- | --- | --- |
| 01-fixed-loss | alternating-balanced | fixed | loss | False | False | True |
| 01-fixed-loss | symmetric-boost | fixed | loss | False | False | True |
| 01-fixed-loss | symmetric-anchor |  | fixed, loss | False | False | False |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Balanced clean variants still produced a branch tradeoff instead of retaining both branches.
- Next action: try a smaller supervised decoding/evaluation diagnostic before more corpus weighting
