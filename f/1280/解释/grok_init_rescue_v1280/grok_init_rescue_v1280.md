# MiniGPT readability report

- Generated: `2026-07-16T11:06:38.059699+00:00`
- Status: `None`
- Decision: `None`

## Summary

| Metric | Value |
| --- | --- |
| verdict | norm_clock_revived_under_lr_scaling |
| reason |  |
| scope | own_grokked_substrate_toy_scale_frozen_recipe_60k_budget |
| g0_reference | True |
| g1_complete | True |
| g2_bar_stable | True |
| rescued_lrs | 0.002, 0.004 |
| class_by_lr | 0.00025=['stuck_memorized', 'stuck_memorized'], 0.0005=['stuck_memorized', 'stuck_memorized'], 0.002=['grokked', 'grokked'], 0.004=['grokked', 'grokked'] |
| dose_shape | cliff |
| baseline_median_tgen | 11400.0 |

## Cells

| arm | alpha | lr | seed | class | t_gen | t_mem | heldout_acc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rescue | 0.5 | 0.00025 | 1337 | stuck_memorized |  | 600 | 0.152916 |
| rescue | 0.5 | 0.00025 | 1338 | stuck_memorized |  | 600 | 0.200478 |
| rescue | 0.5 | 0.0005 | 1337 | stuck_memorized |  | 400 | 0.156503 |
| rescue | 0.5 | 0.0005 | 1338 | stuck_memorized |  | 400 | 0.200478 |
| rescue | 0.5 | 0.002 | 1337 | grokked | 3800 | 300 | 0.981267 |
| rescue | 0.5 | 0.002 | 1338 | grokked | 4000 | 300 | 0.976618 |
| rescue | 0.5 | 0.004 | 1337 | grokked | 1300 | 500 | 0.999203 |
| rescue | 0.5 | 0.004 | 1338 | grokked | 2300 | 500 | 0.999203 |
| dose | 0.6 | 0.001 | 1337 | stuck_memorized |  | 200 | 0.106151 |
| dose | 0.6 | 0.001 | 1338 | stuck_memorized |  | 200 | 0.209247 |
| dose | 0.7 | 0.001 | 1337 | stuck_memorized |  | 200 | 0.105088 |
| dose | 0.7 | 0.001 | 1338 | stuck_memorized |  | 200 | 0.217085 |
| dose | 0.85 | 0.001 | 1337 | grokked | 44200 | 100 | 0.954564 |
| dose | 0.85 | 0.001 | 1338 | grokked | 35600 | 100 | 0.960542 |
