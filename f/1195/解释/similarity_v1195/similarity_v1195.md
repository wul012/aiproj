# MiniGPT task-similarity -> catastrophic forgetting v1195

- Generated: `2026-06-19T14:52:08Z`
- Status: `pass`
- Decision: `forgetting_governed_by_output_overlap`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | forgetting_governed_by_output_overlap |
| verdict | forgetting_governed_by_output_overlap |
| p | 23 |
| seeds | 5 |
| train_frac | 0.8 |
| b_budget | 1500 |
| chance | 0.04348 |
| leak_free | True |
| accA_plateau | 0.9906 |
| per_seed_plateau_ok | True |
| continue_on_A_forgetting | -0.0038 |
| joint_accA | 0.8547 |
| joint_accB | 0.8189 |
| spearman_overlap_forgetting | -1.0 |
| spearman_perm_p | 0.0167 |
| slope_span | 0.7962 |
| overlap_survives_accB_and_drift | True |
| superlinear_vs_overwrite_null | False |
| mean_superlinear_excess | 0.0764 |
| c2_family_does_not_protect | True |
| family_protects | False |
| c3_type_points_on_curve | True |
| structure_at_fixed_overlap | False |
| n_mix_curve | 5 |
| n_indep_type_learned | 3 |
| valid_measurement | True |
| flag_g_a_consolidated | True |
| flag_g_floor_clean | True |
| flag_g_no_operand_leak | True |
| flag_g_jointly_learnable | True |
| flag_g_enough_curve_points | True |
| flag_degenerate_zero_variance | False |
| flag_c1_monotone_slope | True |
| flag_spearman_overlap_forget | -1.0 |
| flag_spearman_perm_p | 0.0167 |
| flag_slope_span | 0.7962 |
| flag_overlap_survives_accB_and_drift | True |
| flag_beta_overlap_given_accB | -0.983 |
| flag_beta_accB | 0.0 |
| flag_beta_overlap_given_drift | -0.998 |
| flag_beta_drift | -0.019 |
| flag_superlinear_vs_overwrite_null | False |
| flag_mean_superlinear_excess | 0.0764 |
| flag_c2_family_does_not_protect | True |
| flag_family_protects | False |
| flag_underpowered_type_contrast | False |
| flag_c3_type_points_on_curve | True |
| flag_structure_at_fixed_overlap | False |
| flag_lowov_forget_spread | 0.0528 |
| flag_n_mix_learned | 6 |
| flag_n_mix_curve | 5 |
| flag_n_indep_type_learned | 3 |

## Rows

| arm | overlap | forgetting | forgetting_std | accB_conflict_test | accB_conflict_train | emb_drift | learned |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mix:1.000 | 1.0 | -0.0019 | 0.014 |  |  | 2.817 | True |
| mix:0.875 | 0.8849 | 0.1415 | 0.0411 | 0.1169 | 1.0 | 2.1846 | True |
| mix:0.750 | 0.7604 | 0.3208 | 0.0298 | 0.1259 | 1.0 | 2.5221 | True |
| mix:0.500 | 0.5321 | 0.6566 | 0.0739 | 0.2977 | 1.0 | 2.5617 | True |
| mix:0.250 | 0.2792 | 0.8019 | 0.0371 | 0.5446 | 1.0 | 2.51 | True |
| mix:0.000 | 0.0434 | 0.9377 | 0.0084 | 0.7903 | 1.0 | 2.6058 | True |
| type:add_same | 1.0 | -0.0019 | 0.014 |  |  | 2.817 | True |
| type:add_offset | 0.0 | 0.9906 | 0.0094 | 1.0 | 1.0 | 3.2397 | True |
| type:linear | 0.0396 | 0.9491 | 0.0227 | 0.9287 | 1.0 | 3.2646 | True |
| type:mul | 0.0434 | 0.9377 | 0.0084 | 0.7903 | 1.0 | 2.6058 | True |
| type:rand | 0.0434 | 0.9566 | 0.0196 | 0.0433 | 1.0 | 2.971 | True |

## Recommendations

- VERDICT (forgetting_governed_by_output_overlap, status=pass): x-axis is the ANALYTIC output-table overlap of B with A=(a+b) mod 23 -- model-INDEPENDENT, |{(a,b):f_B==f_A}|/p^2. Forgetting = A's held-out accuracy drop from its consolidated plateau 0.991 after a fixed 1500-step B phase. status='pass' certifies a VALID measurement (A consolidated per-seed, clean continue-on-A floor -0.004, no operand leak, add+mul jointly learnable A0.85/B0.82, >=5 learnable interior curve points), NOT a clean collapse.
- C1 SLOPE (interior, overlap<1): forgetting is monotone-graded in overlap -- Spearman(overlap,forgetting)=-1.0 (perm p=0.0167), spanning 0.796 from high-overlap to low-overlap (>= 0.3); slope_certified=True. The overlap=1 endpoint is EXCLUDED (forgetting-free by construction = v1193's continue-on-A floor + op-token-confounded); the claim is the INTERIOR only.
- NOT A B-LEARNEDNESS / DRIFT ARTIFACT: controlling for accB and shared-embedding drift, the overlap coefficient stays negative and dominant (std beta overlap|accB=-0.983 vs accB=0.0; overlap|drift=-0.998 vs drift=-0.019); overlap_survives=True. accB is read on CONFLICT cells only (where the retained A-circuit cannot answer for B).
- FAMILY IS A RED HERRING (re-confirms v1193's distribution-shift null via a 2nd manipulation): at overlap~0, add_offset (SAME '+' operation, just +7) forgets 0.991 vs mul 0.938 -- equivalent (|Δ|<= 0.15), both >> add_same -0.002; family_does_not_protect=True, structure_at_fixed_overlap=False. UNIFICATION residual test (type points on the mixture curve)=True.
- SHAPE vs the overwrite null: the trivial 'overwrite only the conflicting cells' null predicts forgetting ~= (1-overlap)*plateau. Observed mean excess over the null is 0.0764 (< margin) -> forgetting is APPROXIMATELY the local-overwrite null (mild mid-overlap excess only). So the overlap law is largely the overwrite-fraction made quantitative, NOT a special global collapse; v1193's 'catastrophic' forgetting is the overlap=0 endpoint of this graded, ~proportional overwrite. SCOPE: toy modular arithmetic, 1-layer transformer, p=23; overlap = 1 - conflict-fraction on shared inputs; the random-partition mixture is fit on train cells but does NOT generalize the per-cell split to held-out cells; NOT a claim about instruction-tuned LLM forgetting.
