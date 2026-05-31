# MiniGPT Required-Term Pair Loss-Branch Objective Comparison

- Status: `pass`
- Decision: `loss_branch_objectives_confirm_loss_only_tradeoff`
- Pair-full reports: `0`
- Loss-only tradeoff reports: `3`
- Model quality claim: `tradeoff_only`

## Routes

| Route | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- |
| v590-targeted | loss | fixed | False |
| v591-dual-anchor | loss | fixed | False |
| v592-micro-span | loss | fixed | False |

## Boundary

- Reason: All compared loss-branch objectives recover loss but drop fixed.
- Next action: build a route decision and test whether one route is worth seed stability replay
