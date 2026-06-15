# MiniGPT knowledge distillation v1172

- Generated: `2026-06-15T09:39:55Z`
- Status: `pass`
- Decision: `distillation_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | distillation_measured |
| verdict | no_distill_benefit |
| device | cuda |
| seeds | 5 |
| ops | C,R,S,L |
| teacher_size | 4L/64 |
| teacher_params | 201920 |
| teacher_exact_match | 0.858333 |
| teacher_mean_maxprob | 0.989019 |
| teacher_mean_entropy_nats | 0.03663 |
| dark_knowledge_absent | True |
| label_smoothing_eps | 0.011896 |
| capable_size | 2L/32 |
| scratch_train_em_floored_size | 0.05 |
| task_learned | True |
| heldout_prompts | 360 |
| scratch_hard_em | 0.772778 |
| label_smooth_em | 0.782778 |
| shuffled_teacher_em | 0.761111 |
| distill_tau1_hw0_em | 0.756667 |
| distill_tau2_hw0_em | 0.803333 |
| scratch_long_em | 0.948889 |
| scratch_long_steps | 2485 |
| distill_gap_fraction_vs_scratch | -0.1883 |
| flag_beats_scratch | False |
| flag_beats_label_smooth | False |
| flag_beats_shuffled_teacher | False |
| flag_dark_knowledge_absent | False |
| flag_scratch_long_catches_up | True |

## Rows

| size | n_layer | n_embd | params | arm | steps | em_mean | em_std | delta_vs_scratch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1L/16 | 1 | 16 | 3776 | scratch_hard | 700 | 0.122222 | 0.040158 | 0.0 |
| 1L/16 | 1 | 16 | 3776 | label_smooth | 700 | 0.100556 | 0.054659 | -0.021667 |
| 1L/16 | 1 | 16 | 3776 | distill_tau1_hw0 | 700 | 0.116111 | 0.049355 | -0.006111 |
| 2L/24 | 2 | 24 | 15192 | scratch_hard | 700 | 0.806111 | 0.073372 | 0.0 |
| 2L/24 | 2 | 24 | 15192 | label_smooth | 700 | 0.831667 | 0.030149 | 0.025556 |
| 2L/24 | 2 | 24 | 15192 | distill_tau1_hw0 | 700 | 0.730556 | 0.086736 | -0.075556 |
| 2L/32 | 2 | 32 | 26400 | scratch_hard | 700 | 0.772778 | 0.111118 | 0.0 |
| 2L/32 | 2 | 32 | 26400 | label_smooth | 700 | 0.782778 | 0.077912 | 0.01 |
| 2L/32 | 2 | 32 | 26400 | shuffled_teacher | 700 | 0.761111 | 0.032691 | -0.011667 |
| 2L/32 | 2 | 32 | 26400 | distill_tau1_hw0 | 700 | 0.756667 | 0.101162 | -0.016111 |
| 2L/32 | 2 | 32 | 26400 | distill_tau1_hw05 | 700 | 0.836111 | 0.043033 | 0.063333 |
| 2L/32 | 2 | 32 | 26400 | distill_tau2_hw0 | 700 | 0.803333 | 0.056465 | 0.030556 |
| 2L/32 | 2 | 32 | 26400 | distill_tau2_hw05 | 700 | 0.787778 | 0.142571 | 0.015 |
| 2L/32 | 2 | 32 | 26400 | scratch_long | 2485 | 0.948889 | 0.033483 | 0.176111 |
| 3L/48 | 3 | 48 | 86304 | scratch_hard | 700 | 0.876667 | 0.063422 | 0.0 |
| 3L/48 | 3 | 48 | 86304 | label_smooth | 700 | 0.872778 | 0.095104 | -0.003889 |
| 3L/48 | 3 | 48 | 86304 | distill_tau1_hw0 | 700 | 0.792222 | 0.073922 | -0.084444 |
| 4L/64 | 4 | 64 | 201920 | scratch_hard | 700 | 0.867222 | 0.039645 | 0.0 |
| 4L/64 | 4 | 64 | 201920 | label_smooth | 700 | 0.822222 | 0.052374 | -0.045 |
| 4L/64 | 4 | 64 | 201920 | distill_tau1_hw0 | 700 | 0.811111 | 0.084277 | -0.056111 |

## Recommendations

- VERDICT (no_distill_benefit): on a DETERMINISTIC task the teacher (4L/64, held-out EM 0.858) is near-one-hot (mean max-prob 0.989, entropy 0.037 nats), so dark knowledge cannot exist by construction — this measures the LOGIT-MATCHING face of distillation. status='pass' certifies the comparison was validly measured (teacher learnable, scratch off the floor, real headroom, controls ran), NOT that distillation is good.
- PRIMARY CONTRAST at 2L/32 (5 independent-init seeds): distill_tau1_hw0 0.757 vs scratch_hard 0.773 (beats=False), vs label_smooth 0.783 (beats=False), vs shuffled_teacher 0.761 (beats=False). The teacher-specific verdict requires beating BOTH controls; otherwise the gain is generic soft-target regularization.
- DARK KNOWLEDGE: absent by construction (teacher max-prob 0.989); tau=1 (no softening) is the faithful target. tau is a COUPLED knob (temperature x effective step size via the tau^2 KL scaling), NOT an isolated cause — do not read 'higher tau worse' as clean causation.
- COMPUTE FRAMING: results at matched STUDENT STEPS (700) treat the teacher forward as free amortized supervision; scratch_long re-runs scratch at matched-FLOPs (2485 steps). A capability claim is honest only if it survives matched-FLOPs OR is explicitly scoped to the teacher-amortized regime.
- CAPACITY: the Δ(distill−scratch) curve tracks the scratch→teacher headroom (peaks at intermediate capacity). The smallest size is an OPTIMIZATION/learnability FLOOR (train-EM 0.05) — below it neither arm clears chance, so its negative deltas are NOT 'distillation hurts'. SCOPE: dark-knowledge transfer needs an ambiguous/multi-answer task, out of scope at char-toy scale.
