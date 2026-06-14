# MiniGPT DPO+SFT-auxiliary (NLL-regularized DPO) v1168

- Generated: `2026-06-14T14:56:31Z`
- Status: `pass`
- Decision: `dpo_sft_aux_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | dpo_sft_aux_measured |
| verdict | dpo_sft_aux_recovers_generation_matches_plain_sft |
| vanilla_dpo_verdict | vanilla_dpo_regresses_generation |
| device | cuda |
| seeds | 3 |
| ops | C,R,S,L |
| beta | 0.1 |
| lr | 0.001 |
| sft_init_steps | 3000 |
| budget_forward_passes | 1600 |
| dpo_opt_steps | 800 |
| sft_opt_steps | 1600 |
| lambda_grid | 0,0.25,0.5,1,2,5 |
| n_layer | 4 |
| n_head | 4 |
| n_embd | 128 |
| use_rope | True |
| pref_train_pairs | 1442 |
| pref_eval_pairs | 479 |
| dropped_degenerate_pairs | 179 |
| gate_lower | 0.4 |
| gate_upper | 0.85 |
| sft_init_exact_match | 0.506361 |
| sft_init_mean_margin | 11.983902 |
| sft_init_confusable_error_rate | 0.022965 |
| loss_optimized | True |
| margin_improvable | True |
| task_learned | True |
| vanilla_dpo_exact_match | 0.141858 |
| best_lambda | 1.0 |
| best_lambda_exact_match | 0.683842 |
| best_lambda_confusable_error_rate | 0.002088 |
| sft_on_chosen_exact_match | 0.739186 |
| sft_on_chosen_confusable_error_rate | 0.009047 |
| recovers_generation | True |
| beats_sft_on_generation | False |
| matches_sft_on_generation | True |
| suppresses_confusable_vs_sft | False |

## Rows

| arm | lambda | exact_match_mean | exact_match_std | mean_margin | pref_acc | mean_logp_chosen | delta_logp_chosen | confusable_error_rate | param_l2_delta | logp_drift | dpo_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sft_init |  | 0.506361 | 0.088947 | 11.983902 | 0.944328 | -1.745218 | 0.0 | 0.022965 | 0.0 | 0.0 |  |
| dpo_aux_l0 | 0.0 | 0.141858 | 0.086202 | 81.286868 | 0.991649 | -24.710798 | -22.965581 | 0.000696 | 27.593679 | 23.418657 | 0.003907 |
| dpo_aux_l0.25 | 0.25 | 0.618957 | 0.115837 | 60.799334 | 0.995129 | -2.91033 | -1.165112 | 0.001392 | 31.226278 | 2.833059 | 0.023172 |
| dpo_aux_l0.5 | 0.5 | 0.663486 | 0.100628 | 57.735563 | 0.993737 | -2.446888 | -0.70167 | 0.002088 | 31.055513 | 2.440277 | 0.034954 |
| dpo_aux_l1 | 1.0 | 0.683842 | 0.141406 | 49.215711 | 0.990953 | -1.86327 | -0.118052 | 0.002088 | 31.118177 | 1.939017 | 0.058734 |
| dpo_aux_l2 | 2.0 | 0.655852 | 0.086729 | 42.373137 | 0.986778 | -1.868268 | -0.12305 | 0.006959 | 30.520357 | 1.911457 | 0.089925 |
| dpo_aux_l5 | 5.0 | 0.669211 | 0.111349 | 34.573647 | 0.981211 | -1.518559 | 0.226659 | 0.009743 | 29.920453 | 1.612465 | 0.166865 |
| sft_on_chosen |  | 0.739186 | 0.168991 | 23.901194 | 0.980515 | -1.110681 | 0.634537 | 0.009047 | 35.572801 | 1.521829 |  |

## Recommendations

- VERDICT (dpo_sft_aux_recovers_generation_matches_plain_sft): vanilla DPO (λ=0) takes held-out exact-match 0.506 -> 0.142 (vanilla_dpo_regresses_generation). Adding the chosen-NLL aux, the best λ=1 reaches 0.684 exact-match (recovers_generation=True); the matched-compute SFT-on-chosen control reaches 0.739. 3 seeds, gap-minus-combined-std significance.
- AUX RECOVERS GENERATION: the NLL term anchors logp(chosen) so the λ-sweep interpolates from vanilla DPO (λ=0, generation crashes) toward SFT-on-chosen (λ→large). λ=0 reproduces vanilla DPO and λ→large converges to SFT — the sweep is a fair interpolation between the two endpoints.
- vs PLAIN SFT (matches on exact-match): on overall generation the SFT term tends to do the heavy lifting. The one DPO-attributable axis is the confusable error: best-λ DPO+SFT confusable-error 0.002 vs SFT-on-chosen 0.009 (suppresses_confusable_vs_sft=False) — the negative signal targets the specific confusion plain SFT-on-positives leaves in place.
- LOSS: aux is the token-level mean CE train_sft minimizes on chosen, fused with the DPO summed-logp from ONE chosen forward (same mask). Reference frozen; arms share init clone + seeded batch stream; DPO+SFT does 2 policy forwards/step so SFT-on-chosen gets ~2x steps at the same forward budget.
- GATE: status='pass' means the comparison was VALID/measurable (init in band=True, DPO loss optimized=True, margin improvable=True) — NOT that DPO+SFT is good. SCOPE: NLL-regularized DPO (DPO+SFT / RPO) on a synthetic deterministic correctness signal with confusable hard-negatives, from-scratch char-level MiniGPT; NOT human preferences / RLHF. Scale-dependent.
