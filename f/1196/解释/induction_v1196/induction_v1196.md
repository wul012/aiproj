# MiniGPT in-context induction requires depth v1196

- Generated: `2026-06-20T09:02:08Z`
- Status: `pass`
- Decision: `induction_requires_depth`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | induction_requires_depth |
| verdict | induction_requires_depth |
| K | 20 |
| T | 64 |
| seeds | 5 |
| chance | 0.05 |
| ceiling | 0.95 |
| S_success_bar | 0.57 |
| widths | [8, 16, 24, 32, 48, 64, 96, 128] |
| unigram_acc | 0.1421 |
| max_marginal | 0.1411 |
| random_init_acc | 0.0629 |
| wstar_1L |  |
| wstar_2L | 17.27 |
| wstar_1L_finite_frac | 0.0 |
| wstar_2L_finite_frac | 1.0 |
| verdict_max_width | 64 |
| gap_at_converged_widest | 0.7887 |
| one_layer_caught_up | False |
| one_layer_extended_max_acc | 0.4283 |
| two_layer_undertrains_large_width | True |
| shortcut_1L_max_acc | 1.0 |
| shortcut_control_ok | True |
| attn_only_2L_max_acc | 0.9941 |
| attn_only_1L_max_acc | 0.1796 |
| attn_only_2L_inducts | True |
| valid_measurement | True |
| flag_task_learnable | True |
| flag_in_context_ok | True |
| flag_random_init_ok | True |
| flag_random_init_acc | 0.0629 |
| flag_shortcut_control_ok | True |
| flag_shortcut_1L_max_acc | 1.0 |
| flag_unigram_acc | 0.1421 |
| flag_max_marginal | 0.1411 |
| flag_verdict_max_width | 64 |
| flag_wstar_1L |  |
| flag_wstar_2L | 17.27 |
| flag_wstar_1L_finite_frac | 0.0 |
| flag_wstar_2L_finite_frac | 1.0 |
| flag_one_layer_extended_max_acc | 0.4283 |
| flag_two_layer_undertrains_large_width | True |
| flag_ordering_holds_paired | True |
| flag_ordering_seed_frac | 1.0 |
| flag_gap_at_widest | 0.7887 |
| flag_one_layer_caught_up_at_widest | False |
| flag_attn_only_2L_max_acc | 0.9941 |
| flag_attn_only_1L_max_acc | 0.1796 |
| flag_attn_only_2L_inducts | True |
| flag_degenerate_zero_variance | False |
| flag_grid_step | 8 |

## Rows

| arm | depth | width | acc | acc_std | swap_follow | succ_attn_mass | layer0_prev_token |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clean_depth1_width8 | 1 | 8 | 0.1062 | 0.0037 | 0.0969 | 0.1411 | 0.3413 |
| clean_depth1_width16 | 1 | 16 | 0.1491 | 0.0017 | 0.1031 | 0.1588 | 0.3826 |
| clean_depth1_width24 | 1 | 24 | 0.1601 | 0.0007 | 0.1125 | 0.1562 | 0.3743 |
| clean_depth1_width32 | 1 | 32 | 0.1719 | 0.0061 | 0.0813 | 0.1722 | 0.4819 |
| clean_depth1_width48 | 1 | 48 | 0.2 | 0.0016 | 0.1281 | 0.1842 | 0.6027 |
| clean_depth1_width64 | 1 | 64 | 0.2107 | 0.0028 | 0.1094 | 0.1791 | 0.6666 |
| clean_depth1_width96 | 1 | 96 | 0.2963 | 0.0205 | 0.1375 | 0.1587 | 0.712 |
| clean_depth1_width128 | 1 | 128 | 0.4283 | 0.0053 | 0.2531 | 0.1157 | 0.8189 |
| clean_depth2_width8 | 2 | 8 | 0.1086 | 0.008 | 0.0781 | 0.1259 | 0.2431 |
| clean_depth2_width16 | 2 | 16 | 0.4895 | 0.2488 | 0.2625 | 1.0447 | 0.644 |
| clean_depth2_width24 | 2 | 24 | 0.9975 | 0.0016 | 0.9125 | 2.7077 | 1.2201 |
| clean_depth2_width32 | 2 | 32 | 0.9991 | 0.0007 | 0.9125 | 3.2166 | 1.537 |
| clean_depth2_width48 | 2 | 48 | 0.9993 | 0.0003 | 0.9156 | 2.786 | 1.3577 |
| clean_depth2_width64 | 2 | 64 | 0.9994 | 0.0001 | 0.9125 | 2.3331 | 1.4876 |
| clean_depth2_width96 | 2 | 96 | 0.5449 | 0.0117 | 0.3187 | 0.1278 | 0.2717 |
| clean_depth2_width128 | 2 | 128 | 0.606 | 0.0169 | 0.425 | 0.1243 | 0.2689 |
| shortcut_1L_fixedoffset_width16 | 1 | 16 | 1.0 | 0.0 |  |  |  |
| shortcut_1L_fixedoffset_width32 | 1 | 32 | 1.0 | 0.0 |  |  |  |
| shortcut_1L_fixedoffset_width64 | 1 | 64 | 1.0 | 0.0 |  |  |  |
| attn_only_depth1_width24 | 1 | 24 | 0.1644 | 0.0009 |  |  |  |
| attn_only_depth1_width48 | 1 | 48 | 0.1668 | 0.0011 |  |  |  |
| attn_only_depth1_width96 | 1 | 96 | 0.1796 | 0.0012 |  |  |  |
| attn_only_depth2_width24 | 2 | 24 | 0.9366 | 0.0343 |  |  |  |
| attn_only_depth2_width48 | 2 | 48 | 0.9872 | 0.002 |  |  |  |
| attn_only_depth2_width96 | 2 | 96 | 0.9941 | 0.0048 |  |  |  |

## Recommendations

- VERDICT (induction_requires_depth, status=pass): clean content-based INDUCTION on a high-diversity random sequence (target = the token that MOST-RECENTLY followed the current one; variable distance; first occurrences masked). Headline metric = inductable accuracy vs chance 0.050 and the in-context UNIGRAM floor 0.142. status='pass' certifies a VALID, genuinely in-context measurement (every succeeding arm beats the unigram floor by >= 0.15 and a swap follows; 2-layer succeeds so the task is learnable; the 1-layer shortcut-control succeeds so a 1-layer clean-task failure is a content-induction limit, not incapacity).
- DEPTH (pre-registered W*-ordering at success bar S=0.570, over the converged width range <= 64): W*(1-layer)=None (finite in 0.0 of seeds) vs W*(2-layer)=17.27 (finite in 1.0). At width 64: 1-layer acc 0.211 vs 2-layer 0.999 (gap +0.789, 1L_caught_up=False). With the shortcuts blocked, induction needs depth: 1 layer (even with its MLP) does not learn it while 2 layers do. EXTENDED bound: 1-layer's best across ALL swept widths (to 128) is only 0.4283 (< S) -- still failing at 128 (7x the 2-layer threshold). HONEST: 2-layer UNDER-TRAINS at width>64 within the fixed 1500-step budget (two_layer_undertrains_large_width=True) -- an optimization effect (fresh data rules out overfitting), so the verdict uses the converged range and 1L's extended widths only as a one-sided failure bound.
- SHORTCUT CONTROL (why the task design matters): the SAME 1-layer model TRAINED on the fixed-offset (positional repeat) task reaches acc 1.0 (>= S) -> 1-layer IS capable of in-context copying when a POSITIONAL shortcut exists. Earlier probes showed a free-running forced-successor task collapses into cycles so a FREQUENCY heuristic also fakes it (unigram floor 0.142). The clean task blocks both, exposing the genuine depth requirement.
- ATTENTION-ONLY (the textbook regime; MLP zeroed): 2-layer attention-only max acc 0.9941 (inducts=True), 1-layer attention-only 0.1796. The canonical 'induction needs 2 layers' is an ATTENTION-ONLY theorem; our 1-layer has an MLP yet still fails, so we report CONSISTENCY with the theorem, not a refutation.
- CAUSAL + MECHANISM: swap-probe follow-rate 0.91 at depth2/width64 -> the model uses in-context CONTENT, not frequency/recency. Induction-attention (mass on the most-recent successor position, summed over heads) best-layer 2.333, layer-0 prev-token 1.488 -- the composed prev-token -> induction circuit. SCOPE: toy synthetic induction, 1-2 layer MiniGPT WITH MLP + learned abs positions, tied embeddings, fixed budget, single (K=20,T=64); a within-swept-width statement, NOT a claim about LLM ICL.
