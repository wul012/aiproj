# MiniGPT v1183 grokking weight-decay dose-response

- Generated: `2026-06-17T14:10:16Z`
- Status: `pass`
- Decision: `wd_dose_response_interior_optimum`

## Summary

| Metric | Value |
| --- | --- |
| p | 97 |
| train_frac | 0.2 |
| n_layer | 1 |
| n_embd | 128 |
| max_steps | 40000 |
| seeds | 5 |
| wds | 0.0, 0.1, 0.3, 1.0, 3.0 |
| verdict | wd_dose_response_interior_optimum |
| g0_task_correct | True |
| g1_memorization | True |
| g2_grid_complete | True |
| grok_wds | 0.3, 1.0 |
| grok_threshold_wd | 0.3 |
| fastest_grok_wd | 1.0 |
| censored_below_threshold | True |
| high_end_grok_censored | True |
| interior_optimum | True |
| too_much_wd_breaks_memorization | False |
| monotone_t_gen_decrease | True |
| strongest_groks_sooner_significant | True |
| boundary | toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim |

## Rows

| weight_decay | grok_rate | mem_rate | n_grokked | t_gen_mean | t_gen_std | grok_gap_mean | final_val_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0 | 0.0 | 1.0 | 0 |  | 0.0 |  | 0.1594794 |
| 0.1 | 0.2 | 1.0 | 1 | 38000.0 | 0.0 | 37800.0 | 0.7208718000000001 |
| 0.3 | 1.0 | 1.0 | 5 | 26560.0 | 5684.012667121705 | 26360.0 | 0.9596654000000001 |
| 1.0 | 1.0 | 1.0 | 5 | 14920.0 | 5944.07267788677 | 14720.0 | 0.9603294 |
| 3.0 | 0.0 | 1.0 | 0 |  | 0.0 |  | 0.195217 |

## Recommendations

- Grokking weight-decay is non-monotone with an interior optimum: it groks fastest at weight_decay=1.0, and both too little and too much decay fail to grok within budget.
- Below weight_decay=0.3 the model memorizes but does not grok in budget; the strongest decay tested also memorizes but does not grok in budget (it does NOT break memorization).
