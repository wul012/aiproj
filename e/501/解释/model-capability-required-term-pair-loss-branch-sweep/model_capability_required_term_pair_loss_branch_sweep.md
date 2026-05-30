# MiniGPT Required-Term Pair Loss-Branch Sweep

- Status: `pass`
- Decision: `required_term_pair_loss_branch_tradeoff`
- Sweep decision: `loss_branch_sweep_tradeoff_only`
- Source contrast-free decision: `contrast_free_training_partial_only`
- Targets: `1`
- Variants: `3`
- Training pass count: `3`
- Focus-hit variants: `3`
- Full-hit variants: `0`

## Variant Results

| Pair | Variant | Focus | Hits | Dropped source hits | Full hit | Tradeoff |
| --- | --- | --- | --- | --- | --- | --- |
| 01-fixed-loss | missed-first-order | loss | loss | fixed | False | True |
| 01-fixed-loss | missed-boosted | loss | loss | fixed | False | True |
| 01-fixed-loss | missed-anchored | loss | loss | fixed | False | True |

## Target Summary

| Pair | Focus missed term | Source hit terms | Focus-hit variants | Full-hit variants | Best variant |
| --- | --- | --- | ---: | ---: | --- |
| 01-fixed-loss | loss | fixed | 3 | 0 | missed-first-order |

## Boundary

- Model quality claim: `loss_branch_tradeoff_signal_only`
- Reason: The previously missed branch can be made to appear, but the sweep did not preserve a full pair hit.
- Next action: compare the tradeoff variant against source-order probes and tune for retaining both branches
