# MiniGPT calibration under uncertainty + temperature scaling v1192

- Generated: `2026-06-19T07:27:01Z`
- Status: `pass`
- Decision: `overconfidence_specifically_corrected_by_temperature`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | overconfidence_specifically_corrected_by_temperature |
| verdict | overconfidence_specifically_corrected_by_temperature |
| headline_n | 10 |
| seeds | 3 |
| mean_true_entropy_nats | 1.126902 |
| entropy_spread | 1.553894 |
| uniform_kl_floor | 0.482536 |
| oracle_analytic_ece | 0.0 |
| oracle_sampled_ece_floor | 0.00333 |
| hard_ce_kl | 0.25683 |
| hard_ce_mean_conf | 0.5594 |
| hard_ce_mean_acc | 0.4417 |
| hard_ce_overconfidence_gap | 0.1177 |
| hard_ce_ece | 0.12413 |
| hard_ce_ece_std | 0.03071 |
| fitted_T | 1.8171 |
| fitted_T_std | 0.1047 |
| hard_ce_ece_after_T | 0.06514 |
| paired_delta_ece | 0.059 |
| paired_delta_ece_std | 0.02898 |
| kl_after_T | 0.16092 |
| rel_ece_reduction | 0.4753 |
| rel_kl_reduction | 0.3735 |
| calibration_kl_co_move | True |
| wrong_T_value | 4.5323 |
| ece_fitted_T | 0.065135 |
| ece_wrong_T | 0.140943 |
| calibrated_ece_pre | 0.040032 |
| calibrated_ece_post_headlineT | 0.081987 |
| boundary_mean_H | 0.309379 |
| boundary_gap | 0.0134 |
| boundary_overconfident | True |
| boundary_correctable | False |
| binning_robust | True |
| not_magic_T_to_one | True |
| teacher_kl_to_true | 0.048735 |
| valid_measurement | True |
| flag_g0_task_learned | True |
| flag_g1_entropy_structure | True |
| flag_g2_temperature_identified | True |
| flag_g3_ece_estimator_valid | True |
| flag_direction_overconfident | True |
| flag_T_significantly_gt_1 | True |
| flag_ece_above_oracle_floor | True |
| flag_correction_paired_significant | True |
| flag_u_shaped | True |
| flag_wrong_T_worse | True |
| flag_t_not_helping_calibrated | True |
| flag_binning_robust | True |
| flag_not_magic_T_to_one | True |
| flag_calibration_kl_co_move | True |
| flag_boundary_not_correctable_null | True |
| flag_soft_distill_calibrated | True |

## Rows

| arm | T | T_std | ece | ece_T | delta_ece_mean | delta_ece_std | nll | nll_T | kl | kl_T | brier | conf | acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hard_ce | 1.8171 | 0.1047 | 0.12413 | 0.06514 | 0.059 | 0.02898 | 1.38373 | 1.28782 | 0.25683 | 0.16092 | 0.6591 | 0.5594 | 0.4417 |
| soft_distill | 0.9851 | 0.0057 | 0.0469 | 0.04808 | -0.00117 | 0.00134 | 1.17554 | 1.17548 | 0.04863 | 0.04858 | 0.6079 | 0.4983 | 0.4894 |
| label_smooth | 1.3261 | 0.0077 | 0.09841 | 0.07621 | 0.0222 | 0.00921 | 1.30865 | 1.28688 | 0.18175 | 0.15997 | 0.64811 | 0.5284 | 0.4489 |
| random_init | 2.8134 | 2.7598 | 0.0172 | 0.00767 | 0.00953 | 0.008 | 1.60851 | 1.60706 | 0.48161 | 0.48016 | 0.79973 | 0.2257 | 0.2085 |
| boundary_low_entropy | 1.2964 | 0.1406 | 0.04521 | 0.04589 | -0.00068 | 0.00772 | 0.42532 | 0.40554 | 0.11595 | 0.09616 | 0.20113 | 0.8884 | 0.8751 |

## Recommendations

- VERDICT (overconfidence_specifically_corrected_by_temperature): on a SYNTHETIC Dirichlet next-char task (K contexts, M=5, KNOWN P_true; mean entropy 1.127 nats, spread 1.55), a 2L/32 transformer trained with hard CE at n=10 samples/ctx is OVERCONFIDENT: mean confidence 0.559 >> mean accuracy 0.442 (gap +0.118), analytic ECE 0.124±0.031 >> the EXACT oracle floor 0.000. status='pass' certifies a VALID measurement (model beats uniform KL 0.483, real entropy spread, identified T, non-degenerate bins), NOT a flattering magnitude.
- FIX: one GLOBAL temperature T=1.82±0.10 (>1, fit by NLL over all contexts) reduces ECE 0.124->0.065 (paired Δ 0.059±0.029, lb>0=True) toward the floor. PAIRED per-seed test (shared model+contexts), not the unpaired in-quadrature test.
- SPECIFIC (not 'any flattening helps'): ECE-vs-T is U-shaped with its minimum at the fitted T (u_shaped=True); a mismatched T=4.5323 from a more-overconfident regime gives higher ECE (0.141 vs fitted 0.065, wrong_T_worse=True); the same T does NOT help an already-calibrated model (0.040->0.082, t_not_helping_calibrated=True); and the oracle's own analytic ECE is 0.000≈0.
- NOT MAGIC — finite-sample MLE artifact: across the samples/ctx sweep the fitted T trends toward 1 as n grows (not_magic_T_to_one=True; n=3:T=4.45, n=10:T=1.82, n=30:T=1.24, n=100:T=1.14, n=300:T=1.08). Overconfidence is the few-sample collapse toward the sampled mode, not an intrinsic architectural property.
- NOVELTY vs v1173 (honest): expected-NLL = entropy + KL, so on this substrate ECE and KL CO-MOVE under temperature (rel ECE reduction 0.48 ≈ rel KL reduction 0.37, co_move=True) — we do NOT claim an ECE/KL dissociation. Calibration adds beyond KL: (a) DIRECTION (KL is direction-blind; ECE diagnoses OVER- vs under-confidence) and (b) the actionable single-scalar fix, measured against an EXACT oracle floor. soft_distill is already calibrated (T=0.99, calibrated=True) — a consistency check with v1173, not new novelty.
- BOUNDARY (the null): a LOW-entropy task instance (mean H 0.309) is only marginally overconfident (gap +0.013 vs +0.118 at high H) and crucially NOT correctable by temperature (ECE 0.045->0.046, correctable=False) — the correctable-overconfidence phenomenon needs real aleatoric uncertainty; at low H there is little GLOBAL over-confidence and one scalar cannot touch the per-context residual. SAMPLED ECE has a positive Jensen-bias floor (oracle sampled-ECE 0.003>0) — exactly why the headline uses ANALYTIC metrics (oracle floor 0). SCOPE: synthetic aleatoric categorical, few-sample regime; NOT a claim that transformers are overconfident in general.
