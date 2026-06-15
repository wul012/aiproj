# MiniGPT distillation under uncertainty v1173

- Generated: `2026-06-15T10:27:56Z`
- Status: `pass`
- Decision: `distillation_under_uncertainty_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | distillation_under_uncertainty_measured |
| verdict | dark_knowledge_is_data_efficiency_under_uncertainty |
| device | cuda |
| seeds | 5 |
| k_contexts | 32 |
| m_outputs | 5 |
| mean_true_entropy_nats | 1.126902 |
| entropy_spread | 1.553894 |
| teacher_size | 4L/64 |
| teacher_kl_to_true | 0.041222 |
| teacher_kl_to_true_std | 0.007052 |
| teacher_entropy | 1.161452 |
| teacher_leakage | 0.00143 |
| teacher_faithful_g1 | True |
| entropy_structure_g2 | True |
| label_smoothing_eps | 0.433929 |
| student_samples_per_ctx | 1 |
| task_learned | True |
| heldout_prompts | 32 |
| scratch_hard_kl | 4.476106 |
| teacher_argmax_hard_kl | 3.51566 |
| teacher_soft_kl | 0.049635 |
| label_smooth_kl | 1.298118 |
| shuffled_teacher_kl | 2.4163 |
| oracle_true_P_kl | 0.00184 |
| data_efficiency_term | 0.960446 |
| dark_knowledge_term | 3.466025 |
| dk_slope_vs_entropy | 3.307002 |
| dk_slope_se | 0.257952 |
| dk_slope_lb | 3.04905 |
| de_slope_vs_entropy | 0.299154 |
| scratch_many_kl | 1=4.243565, 3=1.239796, 10=0.311132, 30=0.071078, 100=0.059108, 400=0.047194 |
| flag_soft_beats_argmax | True |
| flag_soft_beats_hard | True |
| flag_soft_beats_label_smooth | True |
| flag_shuffled_hurts | True |
| flag_dark_knowledge_grows_with_H | True |
| flag_hard_samples_recover_P | True |

## Rows

| arm | kl_fwd_mean | kl_fwd_std | kl_fwd_median | kl_full_mean | excess_kl_vs_teacher | leakage | entropy_bias |
| --- | --- | --- | --- | --- | --- | --- | --- |
| scratch_hard | 4.476106 | 0.322516 | 5.140715 | 4.476627 | 4.434884 | 0.00052 | -1.121928 |
| teacher_argmax_hard | 3.51566 | 0.032233 | 3.87388 | 3.516163 | 3.474438 | 0.000502 | -1.121421 |
| teacher_soft | 0.049635 | 0.001847 | 0.037086 | 0.051129 | 0.008413 | 0.001492 | 0.052124 |
| label_smooth | 1.298118 | 0.038132 | 1.530259 | 1.777795 | 1.256896 | 0.381015 | -0.782501 |
| shuffled_teacher | 2.4163 | 0.039528 | 2.855184 | 2.948399 | 2.375078 | 0.386086 | -0.681069 |
| oracle_true_P | 0.00184 | 0.001075 | 0.001472 | 0.002374 | -0.039382 | 0.000534 | 0.003712 |

## Recommendations

- VERDICT (dark_knowledge_is_data_efficiency_under_uncertainty): on a STOCHASTIC task (mean true entropy 1.127 nats) the teacher is SOFT and faithful (KL(true||teacher) 0.0412 ≈ 0.05*H ceiling; entropy 1.161 ≈ true 1.127) — the mirror of v1172's near-one-hot deterministic teacher. status='pass' certifies a VALID measurement (faithful soft teacher, real entropy spread 1.55, valid baseline, controls ran), NOT that distillation is good.
- DARK KNOWLEDGE = KL(teacher_argmax_hard) − KL(teacher_soft) = 3.516 − 0.050 = +3.466. SAME teacher, SAME 400-sample budget, mode-only pseudo-label vs the full soft shape — soft<<argmax (soft_beats_argmax=True) IS dark knowledge, and it GROWS with context entropy (slope 3.307, lb 3.049>0=True). shuffled_teacher (identity destroyed) HURTS (KL 2.416) — the mirror of v1172 where it was inert.
- NOT MAGIC — data-efficiency under uncertainty: scratch_many at the teacher's own 400 samples/ctx reaches KL 0.047 (hard_samples_recover_P=True). The benefit is buying the large-n hard target at small n; the teacher's 400-sample budget is amortized, not free. data-efficiency term +0.960.
- CONTROLS: label_smooth (ε=0.434 matched to MEAN entropy, KL 1.298) flattens generically — can't encode the SPECIFIC P (soft_beats_label_smooth=True); oracle_true_P 0.002 is the upper bound (KL floor). All KL framed vs the teacher CEILING 0.0412, never reported as '≈0=perfect'.
- v1172↔v1173 CONTRAST: same train_student/kl_term machinery; deterministic teacher (H≈0.05, one-hot) → no dark knowledge, distill==hard; stochastic teacher (H≈1.29, soft) → dark knowledge real, distill≪hard, grows with H. SCOPE: single-position next-char categorical; Dirichlet synthetic is the controlled stand-in for real-text ambiguity (KL lower-is-better → all comparisons via beats_lower).
