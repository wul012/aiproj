# MiniGPT readability report

- Generated: `2026-07-16T12:23:04.901911+00:00`
- Status: `None`
- Decision: `None`

## Summary

| Metric | Value |
| --- | --- |
| verdict | review |
| reason | broken_cells |
| scope | own_grokked_substrate_toy_scale_frozen_recipe_60k_budget |
| g0_references | True |
| g1_complete | True |
| g2_bar_stable | True |
| width_states | 16=broken, 32=still_slower, 64=converged |
| rho_by_width | 16=1.2143, 32=3.3571, 64=1.7143 |
| hole_rule_fired | False |
| parity_band | 0.5, 2.0 |
| ref81_median | 1400.0 |

## Cells

| arm | width | lr | seed | class | t_gen | t_mem | heldout_acc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| width | 16 | 0.004 | 1337 | broken | 1300 |  | 0.846818 |
| width | 16 | 0.004 | 1338 | grokked | 1700 |  | 0.965989 |
| width | 16 | 0.004 | 1339 | grokked | 1800 |  | 0.962003 |
| width | 32 | 0.004 | 1337 | grokked | 2500 | 800 | 0.999336 |
| width | 32 | 0.004 | 1338 | grokked | 4700 | 900 | 0.999336 |
| width | 32 | 0.004 | 1339 | grokked | 6900 | 1200 | 0.999601 |
| width | 64 | 0.004 | 1337 | grokked | 2400 | 200 | 0.983792 |
| width | 64 | 0.004 | 1338 | grokked | 1800 | 200 | 0.999203 |
| width | 64 | 0.004 | 1339 | grokked | 3000 | 300 | 1.0 |
