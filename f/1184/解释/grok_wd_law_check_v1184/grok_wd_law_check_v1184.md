# MiniGPT grokking weight-decay law check v1184

- Generated: `2026-06-18T03:30:35Z`
- Status: `pass`
- Decision: `wd_law_interior_optimum_reconstructed`

## Summary

| Metric | Value |
| --- | --- |
| wd_law_check_ready | True |
| source_status | pass |
| source_decision | wd_dose_response_interior_optimum |
| source_verdict | wd_dose_response_interior_optimum |
| source_wd_law_report | f\1183\解释\grok_wd_law_v1183\grok_wd_law_v1183.json |
| seed_count | 5 |
| wd_count | 5 |
| seed_row_count | 25 |
| grokking_wds | 0.3, 1.0 |
| computed_threshold_wd | 0.3 |
| computed_fastest_wd | 1.0 |
| computed_fastest_t_gen | 14920.0 |
| computed_second_fastest_t_gen | 26560.0 |
| fastest_gap_steps | 11640.0 |
| low_end_censored | True |
| high_end_censored | True |
| strongest_mem_rate | 1.0 |
| strongest_grok_rate | 0.0 |
| strongest_seed_mem_count | 5 |
| strongest_seed_grok_count | 0 |
| grok_rate_threshold | 0.6 |
| min_fastest_gap_steps | 1000 |
| boundary | artifact_reconstruction_only_no_training_rerun |
| next_step | use_v1183_as_weight_decay_dose_response_anchor_if_check_passes |

## Weight-Decay Law Checks

| id | status | expected | actual | detail |
| --- | --- | --- | --- | --- |
| source_status_pass | pass | pass | pass | source report must be a valid measurement |
| source_verdict_interior_optimum | pass | wd_dose_response_interior_optimum | decision=wd_dose_response_interior_optimum, verdict=wd_dose_response_interior_optimum | v1183 headline claim is an interior optimum, not a monotone acceleration claim |
| grid_complete_rows | pass | dose_rows=5, seed_rows=25 | dose_rows=5, seed_rows=25 | dose rows and seed rows must cover every configured weight decay |
| all_doses_memorize | pass | mem_rate>=0.999 for every dose | 1.0, 1.0, 1.0, 1.0, 1.0 | dose-response should separate memorization from generalization, not training failure |
| grok_threshold_matches_summary | pass | 0.3 | 0.3 | first dose with grok_rate>=0.6 must match the summary threshold |
| fastest_wd_matches_summary | pass | 1.0 | 1.0 | fastest grokking dose must be re-derived from dose rows |
| fastest_is_interior | pass | fastest wd is not the minimum or maximum dose | 1.0 | interior optimum requires the fastest dose to be inside the sweep range |
| fastest_gap_material | pass | >= 1000 | 11640.0 | fastest dose should be materially faster than the next grokking dose |
| low_end_censored | pass | True | computed=True, summary=True | too-little weight decay should be censored below the grok threshold |
| high_end_censored_not_broken | pass | high_end_censored=True, too_much_wd_breaks_memorization=False | computed_high_end_censored=True, summary_high_end=True, too_much_breaks_mem=False | strongest dose should memorize but fail to grok, proving the high-end side of the interior optimum |
| strongest_seed_rows_memorize_not_grok | pass | memorized=5, grokked=0 | strongest_seed_mem_count=5, strongest_seed_grok_count=0 | every strongest-dose seed should memorize but none should grok |
| not_monotone_acceleration_claim | pass | interior optimum overrides monotone acceleration | decision=wd_dose_response_interior_optimum, interior_optimum=True, monotone_t_gen_decrease=True | the check must guard the exact over-claim v1183 fixed |
| boundary_present | pass | toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim | toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim | positive dose-response result must keep its toy-scale boundary |

## Recommendations

- The v1183 dose-response claim reconstructs from the dose rows: grokking appears only above a threshold, is fastest at an interior dose, and disappears again at the strongest dose.
- Use weight_decay=1.0 as the fastest toy-scale grokking dose, while keeping the high-end censoring boundary explicit.
