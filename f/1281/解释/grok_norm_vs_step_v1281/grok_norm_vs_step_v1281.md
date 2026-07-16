# MiniGPT readability report

- Generated: `2026-07-16T11:42:42.489842+00:00`
- Status: `None`
- Decision: `None`

## Summary

| Metric | Value |
| --- | --- |
| verdict | review |
| reason | mixed_pairs |
| scope | own_grokked_substrate_toy_scale_frozen_recipe_60k_budget |
| g0_references | True |
| g1_complete | True |
| g2_bar_stable | True |
| pairs | 0.004={'state': 'ok', 'rho': 0.359}, 0.008={'state': 'ok', 'rho': 0.7778} |
| parity_band | 0.5, 2.0 |
| ref80_medians | 3900.0, 1800.0 |
| ref79_baseline_median | 11400.0 |

## Cells

| arm | alpha | lr | seed | class | t_gen | t_mem | heldout_acc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| verdict | 1.0 | 0.004 | 1337 | grokked | 1400 | 100 | 0.99442 |
| verdict | 1.0 | 0.004 | 1338 | grokked | 1800 | 100 | 0.99907 |
| verdict | 1.0 | 0.004 | 1339 | grokked | 1000 | 100 | 0.999203 |
| verdict | 1.0 | 0.008 | 1337 | grokked | 1000 | 300 | 0.999336 |
| verdict | 1.0 | 0.008 | 1338 | grokked | 1400 | 200 | 0.989106 |
| verdict | 1.0 | 0.008 | 1339 | grokked | 1500 | 200 | 0.991497 |
| dose | 1.0 | 0.002 | 1337 | grokked | 1900 | 100 | 0.993889 |
| dose | 1.0 | 0.002 | 1338 | grokked | 2800 | 100 | 0.986582 |
| symmetry | 2.0 | 0.008 | 1337 | grokked | 900 | 200 | 0.999867 |
| symmetry | 2.0 | 0.008 | 1338 | grokked | 900 | 200 | 1.0 |
