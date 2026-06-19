# MiniGPT EWC vs replay for catastrophic forgetting v1194

- Generated: `2026-06-19T13:06:50Z`
- Status: `pass`
- Decision: `replay_dominates_ewc`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | replay_dominates_ewc |
| verdict | replay_dominates_ewc |
| task_a | add |
| task_b | mul |
| p | 23 |
| chance | 0.04348 |
| b_majority_prior | 0.0898 |
| seeds | 3 |
| b_budget | 1500 |
| b_phase_weight_decay | 0.0 |
| accA_plateau | 0.9843 |
| continue_on_A_forgetting | -0.0031 |
| M_replay_best_min | 0.8176 |
| M_replay_std | 0.0393 |
| M_ewc_best_min | 0.1918 |
| M_ewc_std | 0.0393 |
| ewc_max_accA_any_lambda | 0.6761 |
| ewc_max_accB_any_lambda | 0.805 |
| naive_accA | 0.0472 |
| naive_accB | 0.805 |
| ewc_frozen_accB_at_maxlambda | 0.283 |
| hybrid_min | 0.1164 |
| replay_at_hybrid_k_min | 0.7547 |
| joint_accA | 0.8616 |
| joint_accB | 0.8365 |
| fisher_degenerate_frac | 0.1242 |
| valid_measurement | True |
| flag_g_a_consolidated | True |
| flag_g_b_learned | True |
| flag_g_jointly_learnable | True |
| flag_g_no_operand_leak | True |
| flag_g_floor_clean | True |
| flag_g_ewc_anchor_engages | True |
| flag_g_fisher_well_specified | True |
| flag_ewc_can_protect_A | True |
| flag_ewc_can_stay_plastic | True |
| flag_ewc_frontier_bracketed | True |
| flag_ewc_all_or_nothing | True |
| flag_replay_keeps_both_tasks | True |
| flag_ewc_keeps_both_tasks | False |
| flag_replay_dominates | True |
| flag_ewc_dominates | False |
| flag_ewc_adds_on_top_of_replay | False |

## Rows

| method | knob | acc_A | acc_B | min_both |
| --- | --- | --- | --- | --- |
| ewc | lambda=0e+00 | 0.0472 | 0.805 | 0.0472 |
| ewc | lambda=3e+09 | 0.2767 | 0.5786 | 0.2767 |
| ewc | lambda=1e+10 | 0.3899 | 0.3836 | 0.3836 |
| ewc | lambda=3e+10 | 0.4434 | 0.3522 | 0.3522 |
| ewc | lambda=4e+10 | 0.5283 | 0.3113 | 0.3113 |
| ewc | lambda=4e+10 | 0.6195 | 0.3019 | 0.3019 |
| ewc | lambda=5e+10 | 0.6258 | 0.3176 | 0.3176 |
| ewc | lambda=6e+10 | 0.6321 | 0.2925 | 0.2925 |
| ewc | lambda=1e+11 | 0.6541 | 0.2893 | 0.2893 |
| ewc | lambda=3e+11 | 0.4371 | 0.283 | 0.283 |
| replay | k=0 | 0.0472 | 0.805 | 0.0472 |
| replay | k=4 | 0.5031 | 0.8176 | 0.5031 |
| replay | k=8 | 0.7547 | 0.8113 | 0.7547 |
| replay | k=16 | 0.8145 | 0.8113 | 0.8113 |
| replay | k=32 | 0.8774 | 0.8113 | 0.8113 |
| replay | k=64 | 0.8585 | 0.8113 | 0.8113 |
| replay | k=128 | 0.9277 | 0.8176 | 0.8176 |
| hybrid(ewc+replay) | lam=3e+10,k=8 |  |  | 0.1164 |
| multitask_joint | upper bound | 0.8616 | 0.8365 | 0.8365 |

## Recommendations

- VERDICT (replay_dominates_ewc): on the v1193 substrate (A=add then B=mul mod 23, shared 1-layer transformer), the best stability-plasticity operating point (M = max over the strength knob of min(acc_A, acc_B)) is REPLAY 0.818±0.039 vs EWC 0.192±0.039. status='pass' certifies a VALID, FAIR measurement (A consolidated 0.984, B learnable, jointly learnable, no operand leak, EWC anchor engages), NOT that either method is good.
- EWC GOT A FAIR SHOT (not a strawman): across lambda EWC CAN protect A (max acc_A 0.676, can_protect=True) AND CAN stay plastic (max acc_B 0.805 vs naive 0.805, can_stay_plastic=True) — but NOT at the SAME lambda (all_or_nothing=True): as lambda rises acc_A only climbs once acc_B has already collapsed (at lambda_max acc_B 0.283 ~ prior 0.090 = frozen). lambda=0 reproduces naive (acc_A 0.047~chance 0.043). Fisher non-degenerate (zero-frac 0.124); the per-example diagonal Fisher and the EWC penalty reach the tied number-embedding exactly once.
- MECHANISM (ties to v1193): the forgetting is a GLOBAL distribution shift, and the most A-important parameters are the SHARED/tied number-embedding rows that B must overwrite. A diagonal-Fisher LOCAL anchor can only resist by freezing those rows — which blocks B — so EWC has no operating point that keeps both. REPLAY keeps A in the loss directly without freezing anything, reaching (acc_A 0.928) while B still learns.
- HONEST BUDGET DISCLOSURE: the two methods are different resource regimes — replay re-shows 8..128 stored A-train rows EVERY step (a LARGER per-step batch) and stores k examples; EWC stores the Fisher vector + theta* (two model copies) and replays NO data. So 'replay wins' holds at matched B-STEP budget and is partly the v1193 truth that seeing A-data beats not seeing it. We therefore claim BEST-MIN dominance at matched step budget, NOT a resource-free Pareto superiority.
- HYBRID (does EWC add anything on top of replay?): EWC+replay (lambda=3e+10, k=8) min-both 0.116 vs replay-alone at k=8 0.755 (ewc_adds=False). SCOPE: toy modular arithmetic, p=23, 1-layer transformer, diagonal-Fisher single-anchor EWC; NOT a claim that EWC is useless in general — only that a local anchor loses to data rehearsal for this global-shift forgetting.
