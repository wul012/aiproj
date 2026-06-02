# MiniGPT Pair-Readiness Capacity-Probe Plan

- Status: `pass`
- Decision: `pair_readiness_capacity_probe_plan_ready`
- Proposed next artifact: `pair_readiness_capacity_probe_training_run`

## Training Config

| Key | Value |
| --- | --- |
| seed | 3535 |
| max_iters | 1800 |
| eval_iters | 2 |
| batch_size | 16 |
| block_size | 16 |
| n_layer | 2 |
| n_head | 2 |
| n_embd | 96 |
| learning_rate | 0.01 |
| max_new_tokens | 12 |
| temperature | 0.2 |
| top_k | 1 |
| device | cpu |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| route_comparison_passed | pass | pass | source route comparison must pass |
| route_comparison_decision | pass | pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full | capacity probe follows only the closed fixed/loss row-patching branch |
| no_pair_full_route | pass | False | no route should already be pair-full |
| fixed_recovery_returned_to_baseline | pass | True | fixed-recovery must be confirmed as a baseline return |
| route_count_four | pass | 4 | comparison should include baseline, loss-retention, structured, and fixed-recovery routes |
