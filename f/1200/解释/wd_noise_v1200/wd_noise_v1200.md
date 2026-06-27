# MiniGPT weight decay rescues generalization under label noise v1200

- Generated: `2026-06-21T04:20:23Z`
- Status: `pass`
- Decision: `wd_equals_early_stopping`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | wd_equals_early_stopping |
| verdict | wd_equals_early_stopping |
| L | 21 |
| n_train | 256 |
| width | 32 |
| noise_eta | 0.2 |
| seeds | 5 |
| lr | 0.003 |
| best_wd | 3.0 |
| best_eff_decay | 0.009 |
| wd0_earlystop_err | 0.2549 |
| wd0_converged_err | 0.3684 |
| best_wd_converged_err | 0.1758 |
| rescue_gap | 0.0791 |
| rescue | False |
| did | 0.2392 |
| did_ok | True |
| best_wd_train_acc | 0.7758 |
| best_wd_acc_clean_subset | 0.8989 |
| best_wd_fit_to_noise | 0.3235 |
| dissociation | True |
| interior_optimum | True |
| wd0_logit_norm | 16.3763 |
| best_wd_logit_norm | 0.6755 |
| robust | True |
| valid_measurement | True |
| flag_n_seeds | 5 |
| flag_noise_eta | 0.2 |
| flag_best_wd | 3.0 |
| flag_substrate_ok | True |
| flag_reference_memorized | True |
| flag_converged | True |
| flag_wd0_converged_err | 0.3684 |
| flag_wd0_earlystop_err | 0.2549 |
| flag_best_wd_converged_err | 0.1758 |
| flag_rescue_gap | 0.0791 |
| flag_rescue | False |
| flag_did | 0.2392 |
| flag_did_ok | True |
| flag_best_wd_train_acc | 0.7758 |
| flag_best_wd_acc_clean_subset | 0.8989 |
| flag_best_wd_fit_to_noise | 0.3235 |
| flag_dissociation | True |
| flag_interior | True |
| flag_wd0_logit_norm | 16.3763 |
| flag_best_wd_logit_norm | 0.6755 |
| flag_robust | True |

## Rows

| wd | eff_decay | test_err_converged | test_err_earlystop | train_acc_noisy | acc_clean_subset | fit_to_noise |
| --- | --- | --- | --- | --- | --- | --- |
| 0.0 | 0.0 | 0.3684 | 0.2549 | 1.0 | 1.0 | 1.0 |
| 0.1 | 0.0003 | 0.3556 | 0.2855 | 0.9805 | 0.9882 | 0.9516 |
| 0.3 | 0.0009 | 0.3446 | 0.2821 | 0.9164 | 0.9494 | 0.787 |
| 1.0 | 0.003 | 0.305 | 0.2627 | 0.8422 | 0.9022 | 0.6187 |
| 3.0 | 0.009 | 0.1758 | 0.1462 | 0.7758 | 0.8989 | 0.3235 |
| 10.0 | 0.03 | 0.3479 | 0.1699 | 0.5992 | 0.6638 | 0.3744 |

## Recommendations

- VERDICT (wd_equals_early_stopping, status=pass): does WEIGHT DECAY rescue generalization under label noise (eta=0.2) on v1199's noisy halfspace, at a fixed overparameterized width 32? status='pass' certifies a VALID measurement -- substrate sound, the wd=0 reference DOES memorize the noise (train_acc 1.000, so there is something to rescue), the budget converged, >= 4 seeds, and the verdict survives dropping the extreme wd points (True).
- RESCUE (vs the STRONG early-stopping baseline, not the strawman): at the best weight decay wd=3.0 (effective decay lr*wd=0.0090) the CONVERGED clean test error is 0.1758 vs the wd=0 TRAJECTORY-MINIMUM (early-stopping optimum) 0.2549 -- a gap of 0.079; the wd=0 CONVERGED value is 0.3684. rescue=False: wd improves the wd=0 CONVERGED value massively but does NOT significantly beat the wd=0 EARLY-STOPPING optimum at this scale/seed-count -- so wd reaches early-stopping PARITY at convergence (an oracle-free alternative to early stopping), not a new generalization regime.
- MECHANISM -- NOISE REJECTION via the flip-mask dissociation (argmax-based, hence immune to logit rescaling): at wd=3.0 the model fits the CLEAN-labeled train rows (acc_clean_subset 0.8989) while REFUSING the flipped rows (fit_to_noise 0.3235); aggregate noisy train_acc 0.7758 (toward 1-eta=0.80). dissociation=True -- this separates true selective rejection from uniform underfitting (which would drop acc_clean_subset too). logit_norm wd0 16.3763 -> best_wd 0.6755.
- ATTRIBUTION -- difference-in-differences vs the eta=0 control (wide models overfit even on CLEAN data, v1199): the EXCESS noisy-arm improvement DiD=0.2392 (>= 0.05 required: True) is the noise-specific part of the rescue, not generic capacity regularization. Shape: interior_optimum=True (echoing the grokking wd dose-response v1183).
- SCOPE: 1-layer n_head=1 MiniGPT, halfspace L=21, N=256, width 32, 5 seeds, wd grid [0.0, 0.1, 0.3, 1.0, 3.0, 10.0] at lr=0.003. The explicit-regularization complement to v1199's null (overparameterization HURTS under label noise): weight decay rescues it by enforcing the min-norm clean solution. Honest measurement AT TOY SCALE. Designed via a 5-lens adversarial Workflow design panel + a CPU probe. Phase A trains once + caches every (eta,wd,seed) trajectory + flip-mask metrics; Phase B is CPU-only.
