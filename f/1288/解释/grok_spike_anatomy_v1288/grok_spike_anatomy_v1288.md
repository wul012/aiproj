# MiniGPT readability report

- Generated: `2026-07-18T14:34:40.227734+00:00`
- Status: `None`
- Decision: `None`

## Summary

| Metric | Value |
| --- | --- |
| verdict | spikes_are_wd_driven |
| reason |  |
| scope | own_grokked_substrate_toy_scale_d128_branch_arms |
| g0_ok | True |
| g1_complete | True |
| g2_bar_stable | True |
| s1 | 8 |
| s0 | 0 |
| s1_bar | 5 |
| s0_persist | 3 |
| purity_delta_wd1 | -0.0033 |
| purity_delta_wd0 | 0.0006 |
| norm_ratio_wd1 | 0.9533 |
| norm_ratio_wd0 | 1.7527 |
| uncensor | {'lr': 0.004, 'seed': 1338, 'recovered': False, 'final_val': 0.88136, 'heldout_acc': 0.88136}, {'lr': 0.004, 'seed': 1339, 'recovered': True, 'final_val': 1.0, 'heldout_acc': 1.0} |
| runs | 29 |
| total_steps | 117000 |

## Cells

| lr | seed | k_branch | horizon | branch_val | spikes_wd1 | spikes_wd0 | spikes_continuous | branch_purity | purity_wd1 | min_val_wd1 | ends_in_spike_wd1 | purity_wd0 | min_val_wd0 | ends_in_spike_wd0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 1339 | 14700 | 31500 | 1.0 | 0 | 0 | 2 | 0.372206 | 0.574048 | 0.931713 | False | 0.372797 | 0.958682 | False |
| 0.002 | 1337 | 2700 | 5700 | 1.0 | 1 | 0 | 1 | 0.779647 | 0.821574 | 0.42487 | False | 0.811434 | 0.978212 | False |
| 0.002 | 1338 | 3900 | 8400 | 1.0 | 3 | 0 | 3 | 0.726543 | 0.716006 | 0.311279 | False | 0.748795 | 0.969045 | False |
| 0.004 | 1337 | 2000 | 4200 | 1.0 | 2 | 0 | 2 | 0.931885 | 0.928613 | 0.739604 | False | 0.937558 | 0.979009 | False |
| 0.004 | 1338 | 2500 | 5400 | 1.0 | 4 | 0 | 3 | 0.911456 | 0.935397 | 0.656835 | False | 0.917273 | 0.984456 | False |
| 0.004 | 1339 | 1400 | 3000 | 0.996546 | 1 | 0 | 2 | 0.820709 | 0.924913 | 0.8981 | False | 0.802272 | 0.990833 | False |
| 0.008 | 1337 | 1400 | 3000 | 0.999867 | 1 | 0 | 0 | 0.93399 | 0.914896 | 0.363093 | False | 0.90549 | 0.98419 | False |
| 0.008 | 1338 | 2500 | 4200 | 0.998406 | 1 | 0 | 1 | 0.900113 | 0.89399 | 0.681812 | False | 0.888696 | 0.909659 | False |
| 0.008 | 1339 | 2100 | 4500 | 0.991497 | 1 | 0 | 1 | 0.898583 | 0.888527 | 0.356583 | False | 0.872115 | 0.963199 | False |
