# MiniGPT grokking trajectory phases v1181

- Generated: `2026-06-17T09:48:24Z`
- Status: `pass`
- Decision: `grokking_phase_profile_consistent`

## Summary

| Metric | Value |
| --- | --- |
| phase_report_ready | True |
| source_status | pass |
| source_decision | grokking_reproduced_wd_driven |
| source_verdict | grokking_reproduced_wd_driven |
| source_grok_report | f\1179\解释\grok_v1179\grok_v1179.json |
| seed_count | 5 |
| row_count | 10 |
| curve_count | 10 |
| weight_decay_on | 1.0 |
| weight_decay_off | 0.0 |
| wd_on_delayed_grok_count | 5 |
| wd_off_memorized_censored_count | 5 |
| paired_phase_separation_count | 5 |
| wd_on_low_plateau_rate_mean | 0.8321336571672611 |
| wd_on_min_gap | 10400.0 |
| wd_on_max_gap | 25100.0 |
| longest_delay_seed | 1341 |
| min_gap_steps | 1000 |
| low_val_threshold | 0.5 |
| min_wd_on_low_plateau_rate | 0.7 |
| boundary | curve_phase_compression_only_no_training_rerun |
| next_step | use_phase_rows_to_explain_which_part_of_the_curve_makes_v1179_grokking |

## Grokking Phase Rows

| seed | arm | weight_decay | phase | t_mem | t_gen | grok_gap | plateau_eval_count | low_val_plateau_rate | val_at_mem | final_val_acc | max_val_jump | max_val_jump_step | curve_endpoint_matches_row |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1337 | weight_decay_on | 1.0 | delayed_grok | 100 | 11400 | 11300 | 113 | 0.8407079646017699 | 0.11119968444108963 | 0.965989 | 0.15902799999999995 | 11300 | True |
| 1337 | weight_decay_off | 0.0 | memorized_only_censored | 100 |  |  | 400 | 1.0 | 0.10960542410612106 | 0.139099 | 0.108011 | 100 | True |
| 1338 | weight_decay_on | 1.0 | delayed_grok | 100 | 12700 | 12600 | 126 | 0.9603174603174603 | 0.19516408443450928 | 0.951907 | 0.195164 | 100 | True |
| 1338 | weight_decay_off | 0.0 | memorized_only_censored | 100 |  |  | 400 | 1.0 | 0.19476550817489624 | 0.19822 | 0.194766 | 100 | True |
| 1339 | weight_decay_on | 1.0 | delayed_grok | 100 | 10500 | 10400 | 104 | 0.7596153846153846 | 0.141490638256073 | 0.970772 | 0.435499 | 11500 | True |
| 1339 | weight_decay_off | 0.0 | memorized_only_censored | 100 |  |  | 400 | 1.0 | 0.14016208052635193 | 0.139631 | 0.13816900000000001 | 100 | True |
| 1340 | weight_decay_on | 1.0 | delayed_grok | 100 | 14600 | 14500 | 145 | 0.7793103448275862 | 0.15730038285255432 | 0.957885 | 0.30795799999999995 | 11100 | True |
| 1340 | weight_decay_off | 0.0 | memorized_only_censored | 100 |  |  | 400 | 1.0 | 0.16128604114055634 | 0.155175 | 0.161286 | 100 | True |
| 1341 | weight_decay_on | 1.0 | delayed_grok | 100 | 25200 | 25100 | 251 | 0.8207171314741036 | 0.12953367829322815 | 0.952836 | 0.41344500000000006 | 22700 | True |
| 1341 | weight_decay_off | 0.0 | memorized_only_censored | 100 |  |  | 400 | 1.0 | 0.12993223965168 | 0.165272 | 0.11996799999999999 | 100 | True |

## Recommendations

- The v1179 curves compress into the expected phases: early train memorization, a long low-validation plateau, then late generalization only with weight decay.
- The longest delayed seed is 1341, useful as the clearest example when explaining grokking to readers.
