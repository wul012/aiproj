# MiniGPT DPO-lite preference tuning v1166

- Generated: `2026-06-14T09:44:55Z`
- Status: `pass`
- Decision: `dpo_preference_tuning_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | dpo_preference_tuning_measured |
| verdict | dpo_raises_margin_but_generation_regresses |
| reference_verdict | reference_term_no_measurable_effect_at_this_scale |
| sft_control_verdict | matched_compute_sft_on_chosen_beats_dpo_on_generation |
| device | cuda |
| seeds | 3 |
| ops | C,R,S,L |
| beta | 0.1 |
| lr | 0.001 |
| sft_init_steps | 3000 |
| budget_sweep | 240,720,1600 |
| compute_axis | forward_passes (dpo: 2 policy forwards/step; sft_on_chosen: 1/step) |
| n_layer | 4 |
| n_head | 4 |
| n_embd | 128 |
| use_rope | True |
| pref_train_pairs | 1450 |
| pref_eval_pairs | 471 |
| dropped_degenerate_pairs | 179 |
| gate_lower | 0.4 |
| gate_upper | 0.85 |
| sft_init_exact_match | 0.587786 |
| sft_init_pref_acc | 0.969568 |
| sft_init_mean_margin | 14.266256 |
| sft_init_logp_chosen | -1.350072 |
| sft_init_confusable_error_rate | 0.016277 |
| loss_optimized | True |
| margin_improvable | True |
| task_learned | True |
| min_budget | 240 |
| max_budget | 1600 |
| dpo_with_ref_pref_acc_at_max | 0.995754 |
| dpo_with_ref_mean_margin_at_max | 86.148308 |
| dpo_with_ref_exact_match_at_max | 0.10369 |
| dpo_with_ref_delta_logp_chosen_at_max | -26.740186 |
| dpo_no_ref_exact_match_at_max | 0.141221 |
| sft_on_chosen_exact_match_at_max | 0.75827 |
| dpo_with_ref_last_loss_at_max | 0.002989 |

## Rows

| arm | budget_forward_passes | opt_steps | pref_acc_mean | pref_acc_std | exact_match_mean | exact_match_std | mean_logp_chosen | mean_logp_rejected | delta_logp_chosen | delta_logp_rejected | mean_margin | confusable_error_rate | param_l2_delta | logp_drift | dpo_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sft_init | 0 | 0 | 0.969568 | 0.028826 | 0.587786 | 0.175199 | -1.350072 | -15.616328 | 0.0 | 0.0 | 14.266256 | 0.016277 | 0.0 | 0.0 |  |
| dpo_with_ref | 240 | 120 | 0.994338 | 0.009806 | 0.211832 | 0.099512 | -10.42429 | -60.541945 | -9.074217 | -44.925617 | 50.117659 | 0.000708 | 15.421966 | 9.393542 | 0.085845 |
| dpo_with_ref | 720 | 360 | 0.991507 | 0.005617 | 0.145038 | 0.063093 | -18.008967 | -86.058828 | -16.658895 | -70.442499 | 68.049857 | 0.0 | 22.947171 | 16.929626 | 0.017159 |
| dpo_with_ref | 1600 | 800 | 0.995754 | 0.004246 | 0.10369 | 0.057263 | -28.090259 | -114.238571 | -26.740186 | -98.622243 | 86.148308 | 0.0 | 28.976102 | 26.88935 | 0.002989 |
| dpo_no_ref | 240 | 120 | 0.990092 | 0.01365 | 0.217557 | 0.100114 | -11.047248 | -56.934315 | -9.697176 | -41.317986 | 45.887065 | 0.000708 | 15.010732 | 10.014653 | 0.065548 |
| dpo_no_ref | 720 | 360 | 0.987261 | 0.013922 | 0.13486 | 0.119139 | -20.132195 | -83.688728 | -18.782122 | -68.0724 | 63.556531 | 0.001415 | 23.861388 | 18.997393 | 0.019713 |
| dpo_no_ref | 1600 | 800 | 0.991507 | 0.006369 | 0.141221 | 0.077941 | -26.338535 | -110.914241 | -24.988462 | -95.297912 | 84.575706 | 0.000708 | 28.059155 | 25.196186 | 0.002958 |
| sft_on_chosen | 240 | 240 | 0.980184 | 0.021687 | 0.714377 | 0.16357 | -0.922814 | -19.86108 | 0.427259 | -4.244751 | 18.938267 | 0.010616 | 12.825562 | 0.816987 |  |
| sft_on_chosen | 720 | 720 | 0.982307 | 0.018057 | 0.740458 | 0.153848 | -0.909268 | -23.978071 | 0.440805 | -8.361742 | 23.068803 | 0.008493 | 22.484395 | 0.984019 |  |
| sft_on_chosen | 1600 | 1600 | 0.990092 | 0.010034 | 0.75827 | 0.140008 | -0.877171 | -25.977237 | 0.472901 | -10.360909 | 25.100066 | 0.005662 | 33.559231 | 1.105887 |  |

## Recommendations

- VERDICT (dpo_raises_margin_but_generation_regresses): from a weak SFT init (held-out exact-match 0.588, in the [0.4,0.85] headroom band), DPO-with-ref at 1600 forward passes grows the held-out margin 14.3 -> 86.1 (preference-accuracy 0.970 -> 0.996, already near-ceiling) but held-out exact-match FALLS 0.588 -> 0.104, with delta_logp_chosen -26.740. 3 seeds, gap-minus-combined-std significance.
- THE LESSON: the MARGIN (and pref-accuracy) is the OPTIMIZATION TARGET (it moves by construction); held-out exact-match is the CAPABILITY metric. DPO maximizes a RELATIVE margin, so logp_chosen can fall while logp_rejected falls faster — the margin can rise while generation does not improve. NOTE: pref-accuracy saturates near 1.0 at the init (ranking is easier than generating), so the margin is the faithful 'did the objective move' signal; do not read a preference rise as a capability win.
- KILLER CONTROL (matched_compute_sft_on_chosen_beats_dpo_on_generation): matched on FORWARD PASSES (DPO does 2 policy forwards/step, so SFT-on-chosen gets ~2x the optimizer steps), continued SFT-on-chosen reaches exact-match 0.758 vs DPO-with-ref 0.104 at the max budget. This tests whether any DPO movement is uniquely DPO or just more supervision on positives.
- REFERENCE TERM (reference_term_no_measurable_effect_at_this_scale): DPO-no-ref reaches exact-match 0.141 vs with-ref 0.104 at max budget. The KL/reference anchor's stabilizing benefit is a large-scale phenomenon; whatever is reported here is bounded to this tiny scale.
- GATE: status='pass' means the comparison was VALID and measurable (init in band=True, DPO loss optimized=True, margin improvable=True) — NOT that DPO is good. SCOPE: DPO-the-loss on a synthetic deterministic correctness signal with confusable hard-negatives, from-scratch char-level MiniGPT; NOT human preferences / RLHF. Findings are scale-dependent.
