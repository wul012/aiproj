# MiniGPT v1275 Fourier lottery-ticket test

- Generated: `2026-07-12T04:10:45Z`
- Status: `pass`
- Decision: `pruning_breaks_circuit`

## Summary

| Metric | Value |
| --- | --- |
| verdict | pruning_breaks_circuit |
| scope | toy_scale_own_substrate |
| checkpoint_sha256 | 46F2A11A945F0BD140AF09FE298B28DD31062B4E3018EA159876C263F7DCB7DB |
| arm_p_probe_ok | False |
| arm_p_aligned | False |
| ticket_grok_count | 0 |
| control_grok_count | 0 |
| tickets_aligned | False |
| actual_training_runs | 0 |
| max_training_runs | 15 |
| descoped_levels | 0.5, 0.75, 0.875 |
| checkpoint_unchanged | True |
| p_complete | True |
| random_controls_complete | True |
| arm_l_complete | False |
| arm_l_skipped | True |
| budget_ok | True |
| ticket_groks | False |
| control_tie | False |

## Rows

| phase | mode_or_arm | seed | sparsity | heldout_acc | known_share | random_share | share_margin | top_freqs | t_gen | step_cap | grokked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P | per_tensor |  | 0.5 | 0.406536 | 0.314068 | 0.205057 | 0.109011 | 43,48,3,26,12 |  |  |  |
| P | per_tensor |  | 0.7 | 0.074266 | 0.298791 | 0.166861 | 0.13193 | 43,3,48,26,44 |  |  |  |
| P | per_tensor |  | 0.8 | 0.02883 | 0.27392 | 0.146738 | 0.127182 | 3,43,48,26,12 |  |  |  |
| P | per_tensor |  | 0.9 | 0.015677 | 0.244907 | 0.123376 | 0.121531 | 48,43,44,12,3 |  |  |  |
| P | per_tensor |  | 0.95 | 0.011558 | 0.21102 | 0.114988 | 0.096032 | 48,44,43,3,14 |  |  |  |
| P | global |  | 0.5 | 0.486781 | 0.30518 | 0.204559 | 0.100621 | 43,3,48,26,44 |  |  |  |
| P | global |  | 0.7 | 0.119835 | 0.305282 | 0.16648 | 0.138802 | 43,3,48,26,44 |  |  |  |
| P | global |  | 0.8 | 0.038927 | 0.305102 | 0.149546 | 0.155556 | 43,3,48,26,44 |  |  |  |
| P | global |  | 0.9 | 0.012223 | 0.305274 | 0.12698 | 0.178294 | 43,3,48,26,44 |  |  |  |
| P | global |  | 0.95 | 0.009698 | 0.314153 | 0.116563 | 0.19759 | 43,3,48,26,44 |  |  |  |

## Recommendations

- Interpret this result only on the mod-97 toy model and its frozen v1185 substrate.
- The 0.75 and 0.875 IMP levels were pre-run descoped to honor the five-runs-per-seed cap.
- Use the cached measurements for threshold re-analysis; do not retrain in Phase B.
