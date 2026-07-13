# MiniGPT v1277 capacity squeeze

- Generated: `2026-07-13T05:13:21Z`
- Status: `pass`
- Decision: `squeeze_hits_capacity_floor`

## Summary

| Metric | Value |
| --- | --- |
| verdict | squeeze_hits_capacity_floor |
| reason | squeeze_hits_capacity_floor |
| scope | own_grokked_substrate_toy_scale |
| g0_substrate | True |
| g1_complete | True |
| g2_ratio_stable | True |
| keep_ratio | 0.9 |
| grokked_squeeze_cells | 0 |
| forced_packing | 0 |
| economized | 0 |
| off_mechanism | 0 |
| smallest_grokking_width | 12 |
| baseline_k_func_median | 3.0 |
| baseline_gram_median | 0.060003 |

## Cells

| width | seed | heldout_acc | t_gen | k_func | footprint | gram_maxcos_at_k | n_eff | class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 32 | 1337 | 0.97024 | 2600 | 4 | 8 | 0.093311 | 8.9937 | economized |
| 32 | 1338 | 0.953368 | 3400 | 3 | 6 | 0.041113 | 9.1491 | economized |
| 32 | 1339 | 0.961206 | 2700 | 3 | 6 | 0.060003 | 9.1184 | economized |
| 16 | 1337 | 0.952305 | 2800 | 3 | 6 | 0.083078 | 4.0509 | economized |
| 16 | 1338 | 0.955228 | 2600 | 4 | 8 | 0.384127 | 3.7817 | economized |
| 16 | 1339 | 0.959081 | 6600 | 4 | 8 | 0.115741 | 4.9991 | economized |
| 12 | 1337 | 0.956158 | 3200 | 5 | 10 | 0.564025 | 3.3517 | economized |
| 12 | 1338 | 0.777202 |  | 2 | 4 | 0.023719 | 2.3037 | not_grokked |
| 12 | 1339 | 0.78783 |  | 2 | 4 | 0.006753 | 2.7568 | not_grokked |
| 8 | 1337 | 0.15451 |  | 4 | 8 | 0.737277 | 2.0557 | not_grokked |
| 8 | 1338 | 0.537797 |  | 2 | 4 | 0.0494 | 2.226 | not_grokked |
| 8 | 1339 | 0.160755 |  | 4 | 8 | 0.765921 | 2.1177 | not_grokked |
| 4 | 1337 | 0.008503 |  | 1 | 2 | 0.193614 | 33.7862 | not_grokked |
| 4 | 1338 | 0.009831 |  | 1 | 2 | 0.296957 | 32.5784 | not_grokked |
| 4 | 1339 | 0.010496 |  | 1 | 2 | 0.888835 | 23.7988 | not_grokked |

## Recommendations

- Locate the floor: sweep between the smallest grokking width and the largest failing width with a longer step budget.
