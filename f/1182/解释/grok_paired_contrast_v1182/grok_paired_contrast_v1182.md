# MiniGPT grokking paired contrast v1182

- Generated: `2026-06-17T10:05:18Z`
- Status: `pass`
- Decision: `grokking_weight_decay_pair_contrast_consistent`

## Summary

| Metric | Value |
| --- | --- |
| paired_contrast_ready | True |
| source_status | pass |
| source_decision | grokking_phase_profile_consistent |
| source_phase_report | f\1181\解释\grok_trajectory_phases_v1181\grok_trajectory_phases_v1181.json |
| seed_count | 5 |
| phase_row_count | 10 |
| pair_count | 5 |
| matched_memorization_count | 5 |
| on_delayed_grok_count | 5 |
| off_memorized_censored_count | 5 |
| no_decay_censored_count | 5 |
| mean_final_val_gain | 0.8003984 |
| min_final_val_gain | 0.753687 |
| mean_steps_saved_by_grok_stop | 24760.0 |
| longest_delay_seed | 1341 |
| largest_final_val_gain_seed | 1339 |
| required_min_final_val_gain | 0.7 |
| boundary | paired_phase_contrast_only_no_training_rerun |
| next_step | use_pair_rows_as_the_plainest_weight_decay_counterfactual_for_v1179_grokking |

## Grokking Paired Contrasts

| seed | pair_status | on_phase | off_phase | on_t_mem | off_t_mem | t_mem_delta | on_t_gen | off_t_gen | on_grok_gap | on_steps_run | off_steps_run | steps_saved_by_grok_stop | on_final_val_acc | off_final_val_acc | final_val_gain | on_low_val_plateau_rate | off_low_val_plateau_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1337 | weight_decay_counterfactual | delayed_grok | memorized_only_censored | 100 | 100 | 0.0 | 11400 |  | 11300 | 11600 | 40000 | 28400.0 | 0.965989 | 0.139099 | 0.82689 | 0.8407079646017699 | 1.0 |
| 1338 | weight_decay_counterfactual | delayed_grok | memorized_only_censored | 100 | 100 | 0.0 | 12700 |  | 12600 | 12900 | 40000 | 27100.0 | 0.951907 | 0.19822 | 0.753687 | 0.9603174603174603 | 1.0 |
| 1339 | weight_decay_counterfactual | delayed_grok | memorized_only_censored | 100 | 100 | 0.0 | 10500 |  | 10400 | 11600 | 40000 | 28400.0 | 0.970772 | 0.139631 | 0.8311409999999999 | 0.7596153846153846 | 1.0 |
| 1340 | weight_decay_counterfactual | delayed_grok | memorized_only_censored | 100 | 100 | 0.0 | 14600 |  | 14500 | 14700 | 40000 | 25300.0 | 0.957885 | 0.155175 | 0.80271 | 0.7793103448275862 | 1.0 |
| 1341 | weight_decay_counterfactual | delayed_grok | memorized_only_censored | 100 | 100 | 0.0 | 25200 |  | 25100 | 25400 | 40000 | 14600.0 | 0.952836 | 0.165272 | 0.787564 | 0.8207171314741036 | 1.0 |

## Recommendations

- Use the paired rows as the shortest honest explanation of v1179: the same seed memorizes in both arms, but only the weight-decay arm generalizes.
- Seed 1339 is the clearest final-accuracy contrast; seed 1341 is the clearest delayed-grokking story.
