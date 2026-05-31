# MiniGPT Required-Term Pair Fixed-Retention Loss-Rebalance Corpus Contract

- Status: `pass`
- Decision: `fixed_retention_loss_rebalance_corpus_modes_ready`
- Version: `v605.0.0`
- New mode count: `2`

## Modes

| Mode | Role | Pair id removed | Fixed prefix rows | Loss rebalance rows |
| --- | --- | --- | --- | --- |
| equals_surface_no_pair_id_fixed_retention_loss_rebalance_repair | retain fixed, rebalance loss | True | True | True |
| equals_surface_no_pair_id_fixed_retention_dual_cycle_repair | alternating dual cycle | True | True | True |

## Boundary

This contract only proves the loss-rebalance corpus modes are registered and test-covered. Real model behavior is checked in the next training run.
