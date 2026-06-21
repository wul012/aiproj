# MiniGPT double descent (absent at toy scale) v1199

- Generated: `2026-06-21T02:02:22Z`
- Status: `pass`
- Decision: `no_double_descent_monotone`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | no_double_descent_monotone |
| verdict | no_double_descent_monotone |
| L | 21 |
| n_train | 256 |
| noise_eta | 0.2 |
| seeds | 5 |
| ctrl_ok | True |
| interp_reached | True |
| w_interp | 16 |
| ms_second_descent | False |
| ms_peak_w | 32 |
| ms_test_err_at_peak | 0.3894 |
| ms_test_err_widest | 0.3894 |
| epoch_width | 32 |
| epoch_rise | 0.0746 |
| epoch_rise_ctrl | 0.0505 |
| epoch_recovery | 0.0093 |
| epoch_best_pre | 0.3144 |
| epoch_final | 0.3889 |
| epoch_dd | False |
| signal_before_noise | False |
| tau_grid_agree_frac | 1.0 |
| valid_measurement | True |
| flag_n_seeds | 5 |
| flag_noise_eta | 0.2 |
| flag_ctrl_ok | True |
| flag_interp_reached | True |
| flag_w_interp | 16 |
| flag_ms_peak_w | 32 |
| flag_ms_second_descent | False |
| flag_ms_test_err_at_peak | 0.3894 |
| flag_ms_test_err_widest | 0.3894 |
| flag_epoch_width | 32 |
| flag_epoch_rise | 0.0746 |
| flag_epoch_rise_ctrl | 0.0505 |
| flag_epoch_recovery | 0.0093 |
| flag_epoch_best_pre | 0.3144 |
| flag_epoch_final | 0.3889 |
| flag_epoch_interp_frac | 1.0 |
| flag_epoch_dd | False |
| flag_signal_before_noise | False |
| flag_tau_grid_agree_frac | 1.0 |

## Rows

| width | eff_params | test_err_noise | test_err_clean | train_acc_noise |
| --- | --- | --- | --- | --- |
| 3 |  | 0.2466 | 0.1029 | 0.8375 |
| 4 |  | 0.2684 | 0.0407 | 0.8195 |
| 6 |  | 0.325 | 0.0601 | 0.9773 |
| 8 |  | 0.3113 | 0.1081 | 0.9758 |
| 12 |  | 0.3261 | 0.1234 | 0.9789 |
| 16 |  | 0.3382 | 0.1216 | 0.9906 |
| 24 |  | 0.3587 | 0.174 | 0.9969 |
| 32 |  | 0.3894 | 0.2461 | 0.9938 |

## Recommendations

- VERDICT (no_double_descent_monotone, status=pass): does a tiny 1-layer MiniGPT show DOUBLE DESCENT on a noisy linear-teacher (halfspace) over L=21 bits with eta=0.2 label noise? status='pass' certifies a VALID measurement -- the eta=0 control interpolates AND generalizes (test_err <= 0.12), the noisy models DO reach interpolation (w_interp=16, so the noise is genuinely memorized), >= 4 seeds complete, and the conclusion is invariant across the interpolation-tau grid (100%).
- MODEL-SIZE arm (fixed N=256, sweep width, train-to-interpolation): NO second descent. The clean-test-error 'peak' over the overparameterized region sits at w=32 (0.3894); the widest model (32) does NOT drop below it (test_err 0.3894) -> overparameterization does not help. ms_second_descent=False.
- EPOCH-WISE arm (fixed width=32, test error vs training step): after the train set interpolates, clean test error rises from its pre-interpolation best (0.3144) to a plateau (0.3889), a rise of 0.0746 -- but the eta=0 control ALSO rises 0.0505 (wide models overfit even on CLEAN data), so the rise is only partially noise-attributable (signal_before_noise=False). Crucially there is NO recovery (recovery 0.0093 < 0.05) -> epoch_wise_double_descent=False: single-descent overfitting, so EARLY STOPPING (not scale or longer training) is what helps.
- CONCLUSION (no_double_descent_monotone): NO double descent in either arm at this toy scale. In the model-size arm the BEST generalization is at the UNDERPARAMETERIZED end and test error rises ~monotonically with width (overparameterization HURTS, the OPPOSITE of a second descent); in the epoch-wise arm there is no recovery after interpolation. The eta=0 control confirms the substrate is sound (best clean test error well below 0.12) and that part of the degradation is generic capacity-overfitting, not only label noise.
- SCOPE: 1-layer n_head=1 MiniGPT, halfspace over L=21 bits, fixed N=256, 5 seeds. This is an honest measurement AT TOY SCALE -- NOT a claim that double descent is absent in large models (it is well-documented there). Designed via a 5-lens adversarial design panel + 4 CPU probes (parity does not interpolate noisy labels -> halfspace; model-size/sample-wise/epoch-wise each probed). Phase A trains once + caches every trajectory; Phase B is CPU-only zero-retrain.
