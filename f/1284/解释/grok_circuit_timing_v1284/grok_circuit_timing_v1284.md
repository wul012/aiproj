# MiniGPT readability report

- Generated: `2026-07-17T04:49:50.074465+00:00`
- Status: `None`
- Decision: `None`

## Summary

| Metric | Value |
| --- | --- |
| verdict | review |
| reason | mixed_fractions |
| scope | own_grokked_substrate_toy_scale_canonical_recipe_6_cells |
| g0_ok | True |
| g1_complete | True |
| g2_bar_stable | True |
| fractions | 20/1337=0.2748, 20/1338=0.4718, 24/1337=0.2506, 24/1338=0.2399, 28/1337=0.3084, 28/1338=0.2186 |
| coupled_final_median | 0.8833 |
| runs | 49 |
| total_steps | 60600 |

## Cells

| width | seed | phase | fraction | c0_share | final_share | t_mem | t_gen | heldout_acc | snapshot_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | 1337 | coupled | 0.2748 | 0.11716 | 0.91488 | 1300 | 1300 | 0.985652 | 5 |
| 20 | 1338 | coupled | 0.4718 | 0.107952 | 0.883328 | 1500 | 1500 | 0.988043 | 6 |
| 24 | 1337 | coupled | 0.2506 | 0.125861 | 0.851287 | 1100 | 1100 | 0.988442 | 5 |
| 24 | 1338 | delayed | 0.2399 | 0.109785 | 0.811575 | 2300 | 3600 | 0.98791 | 9 |
| 28 | 1337 | delayed | 0.3084 | 0.128936 | 0.764643 | 1900 | 5100 | 0.963332 | 10 |
| 28 | 1338 | delayed | 0.2186 | 0.108132 | 0.763848 | 1600 | 2700 | 0.960941 | 8 |
