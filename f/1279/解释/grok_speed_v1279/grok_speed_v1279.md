# MiniGPT v1279 narrow-grok-speed norm-clock test

- Generated: `2026-07-13T12:28:30Z`
- Status: `pass`
- Decision: `review`

## Summary

| Metric | Value |
| --- | --- |
| verdict | review |
| reason | substrate_unsound |
| scope | own_grokked_substrate_toy_scale_frozen_recipe |
| g0_substrate | False |
| g1_complete | True |
| g2_bar_stable | True |
| phenomenon | review |
| ratio_wide_over_narrowest | 4.071 |
| alpha_monotone_pairs | 3/6 |
| mediation_share | -inf |
| matched_alpha_tgen | inf |
| wide_base_tgen | 11400.0 |
| narrow_base_tgen | 2700.0 |

## Cells

| arm | width | seed | alpha | n0 | n_final | heldout_acc | t_gen | censored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grid | 16 | 1337 | 1.0 | 8.0921 | 26.6847 | 0.952305 | 2800 | False |
| grid | 16 | 1338 | 1.0 | 8.0946 | 27.088 | 0.955228 | 2600 | False |
| grid | 16 | 1339 | 1.0 | 8.0924 | 36.3788 | 0.959081 | 6600 | False |
| grid | 32 | 1337 | 1.0 | 10.8823 | 37.319 | 0.97024 | 2600 | False |
| grid | 32 | 1338 | 1.0 | 10.8884 | 37.6796 | 0.953368 | 3400 | False |
| grid | 32 | 1339 | 1.0 | 10.8875 | 38.4367 | 0.961206 | 2700 | False |
| grid | 64 | 1337 | 1.0 | 15.2266 | 46.4935 | 0.226651 |  | True |
| grid | 64 | 1338 | 1.0 | 15.2203 | 46.044 | 0.971436 | 35000 | False |
| grid | 64 | 1339 | 1.0 | 15.2228 | 45.5071 | 0.225189 |  | True |
| grid | 128 | 1337 | 1.0 | 22.0936 | 41.519 | 0.965989 | 11400 | False |
| grid | 128 | 1338 | 1.0 | 22.089 | 42.0488 | 0.951906 | 12700 | False |
| grid | 128 | 1339 | 1.0 | 22.0863 | 42.9488 | 0.970772 | 10500 | False |
| alpha_wide | 128 | 1337 | 0.5 | 11.0468 | 42.0191 | 0.174439 |  | True |
| alpha_wide | 128 | 1338 | 0.5 | 11.0445 | 44.3367 | 0.200744 |  | True |
| alpha_wide | 128 | 1339 | 0.5 | 11.0431 | 41.6629 | 0.294141 |  | True |
| alpha_wide | 128 | 1337 | 2.0 | 44.1871 | 41.6973 | 0.952039 | 12800 | False |
| alpha_wide | 128 | 1338 | 2.0 | 44.1781 | 39.488 | 0.986714 | 23200 | False |
| alpha_wide | 128 | 1339 | 2.0 | 44.1726 | 40.3324 | 0.957885 | 20200 | False |
| alpha_star | 128 | 1337 | 0.4926 | 10.8823 | 48.8166 | 0.144945 |  | True |
| alpha_star | 128 | 1338 | 0.4929 | 10.8884 | 43.7803 | 0.197954 |  | True |
| alpha_star | 128 | 1339 | 0.493 | 10.8875 | 48.4933 | 0.230902 |  | True |
| alpha_narrow | 32 | 1337 | 2.0 | 21.7646 | 40.2795 | 0.963066 | 3900 | False |
| alpha_narrow | 32 | 1338 | 2.0 | 21.7767 | 36.1069 | 0.98512 | 2400 | False |
| alpha_narrow | 32 | 1339 | 2.0 | 21.775 | 29.8664 | 0.973163 | 1200 | False |

## Recommendations

- Adjudicate the review branch externally before any follow-up.
