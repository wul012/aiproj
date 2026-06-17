# MiniGPT v1179 grokking (delayed generalization)

- Generated: `2026-06-17T05:07:24Z`
- Status: `pass`
- Decision: `grokking_reproduced_wd_driven`

## Summary

| Metric | Value |
| --- | --- |
| p | 97 |
| train_frac | 0.2 |
| n_layer | 1 |
| n_embd | 128 |
| lr | 0.001 |
| weight_decay_on | 1.0 |
| weight_decay_off | 0.0 |
| max_steps | 40000 |
| seeds | 5 |
| verdict | grokking_reproduced_wd_driven |
| g0_task_correct | True |
| g1_memorization | True |
| g2_grid_complete | True |
| delay_real | True |
| grok_reproduced | True |
| wd_on_grok_rate | 1.0 |
| wd_on_mem_rate | 1.0 |
| wd_on_t_gen_mean | 14880.0 |
| wd_on_t_gen_std | 5971.348256466039 |
| wd_on_grok_gap_mean | 14780.0 |
| wd_on_val_at_mem_mean | 0.14693769365549086 |
| wd_on_final_val_mean | 0.9598777999999999 |
| wd_off_grok_rate | 0.0 |
| wd_off_mem_rate | 1.0 |
| wd_off_t_gen_mean |  |
| wd_off_final_val_mean | 0.1594794 |
| boundary | toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim |

## Rows

| seed | weight_decay | memorized | grokked | t_mem | t_gen | grok_gap | val_at_mem | final_train_acc | final_val_acc | steps_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1337 | 1.0 | True | True | 100 | 11400 | 11300 | 0.11119968444108963 | 1.0 | 0.965989 | 11600 |
| 1337 | 0.0 | True | False | 100 |  |  | 0.10960542410612106 | 1.0 | 0.139099 | 40000 |
| 1338 | 1.0 | True | True | 100 | 12700 | 12600 | 0.19516408443450928 | 1.0 | 0.951907 | 12900 |
| 1338 | 0.0 | True | False | 100 |  |  | 0.19476550817489624 | 1.0 | 0.19822 | 40000 |
| 1339 | 1.0 | True | True | 100 | 10500 | 10400 | 0.141490638256073 | 1.0 | 0.970772 | 11600 |
| 1339 | 0.0 | True | False | 100 |  |  | 0.14016208052635193 | 1.0 | 0.139631 | 40000 |
| 1340 | 1.0 | True | True | 100 | 14600 | 14500 | 0.15730038285255432 | 1.0 | 0.957885 | 14700 |
| 1340 | 0.0 | True | False | 100 |  |  | 0.16128604114055634 | 1.0 | 0.155175 | 40000 |
| 1341 | 1.0 | True | True | 100 | 25200 | 25100 | 0.12953367829322815 | 1.0 | 0.952836 | 25400 |
| 1341 | 0.0 | True | False | 100 |  |  | 0.12993223965168 | 1.0 | 0.165272 | 40000 |

## Recommendations

- Grokking reproduced: train accuracy saturates early, validation generalizes only much later.
- Weight decay is the driver -- the wd=0 arm memorizes but (essentially) never groks within budget.
- This is a delayed phase transition, not slow co-convergence (val was still near chance at memorization).
